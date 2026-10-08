# mxl-schemas

Canonical JSON Schema definitions for the mxl\* tool family ([mxlpy](https://github.com/Computational-Biology-Aachen/mxlpy), [mxlweb](https://github.com/Computational-Biology-Aachen/mxlweb)).

All schemas target [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12).

## Schemas

The `.mxl.json` format comes in three formulations, one schema each, all under `v1/`. Every file carries a required top-level `kind` discriminator so a consumer can pick the right schema without inspecting the model structure.

| File                                                                 | `kind`         | Formulation                          | dx/dt                          |
| -------------------------------------------------------------------- | -------------- | ------------------------------------ | ------------------------------ |
| [`v1/kinetic-model.schema.json`](./v1/kinetic-model.schema.json)     | `kinetic`      | Reactions × stoichiometry            | computed as `N·v`              |
| [`v1/ode-model.schema.json`](./v1/ode-model.schema.json)             | `ode`          | Direct per-variable derivative       | encoded as `fn` on each `variable` |
| [`v1/steady-state-model.schema.json`](./v1/steady-state-model.schema.json) | `steady-state` | Algebraic outputs of the parameters  | none (no time integration)     |

A fourth schema, [`v1/nn-weights.schema.json`](./v1/nn-weights.schema.json), describes the external weight/bias sidecar file that an `nn_block`'s `weights_ref` points to — not a `.mxl.json` document itself, no envelope/`kind` discriminator.

### Envelope

Every model file shares the same outer shape:

```json
{
  "$schema": "https://raw.githubusercontent.com/Computational-Biology-Aachen/mxl-schemas/main/v1/<kind>-model.schema.json",
  "spec_version": "1.1",
  "kind": "kinetic | ode | steady-state",
  "model_id": "my_model",
  "description": "optional human-readable description",
  "model": { ... }
}
```

### Sections per formulation

| Section      | kinetic | ode | steady-state |
| ------------ | :-----: | :-: | :----------: |
| `variables`  |   ✓     | ✓ (with `fn`) |      —       |
| `parameters` |   ✓     | ✓   |      ✓       |
| `reactions`  |   ✓     | —   |      —       |
| `derived`    |   ✓     | ✓   |      ✓       |
| `readouts`   |   ✓     | ✓   |      —       |
| `nn_blocks`  |   ✓     | ✓   |      —       |

- **variables** — state variables with an initial `value`; in the ODE format each also carries its derivative `fn`.
- **parameters** — constants with a `value`.
- **reactions** — a rate `fn` and a per-variable `stoichiometry` map (kinetic only).
- **derived** — quantities computed from other entities at each time point; in the steady-state format these are the model's outputs.
- **readouts** — report-only quantities that do not feed back into the dynamics. Omitted from the steady-state format, which has no dynamics.
- **nn_blocks** — UDE/NODE correction terms (mxlweb ADR 0005) composed onto one or more variables' dynamics via `mechanism`, a math expression over two placeholders: `ode` (the pre-existing dx/dt term) and `nde` (this block's scaled network output). E.g. additive is `Add(ode, nde)` (`dx/dt = f(x,p,t) + scale · NN(x,θ)`); relative_multiply is `Mul(ode, Add(1, nde))` (`dx/dt = f(x,p,t) · (1 + scale · NN(x,θ))` — a near-zero/untrained network leaves `f` unchanged); multiply is `Mul(ode, nde)` (`dx/dt = f(x,p,t) · scale · NN(x,θ)` — a bare product with no such safeguard; a near-zero/untrained network zeroes out both `f` and the gradient w.r.t. every mechanistic parameter). These three are just common presets — `mechanism` accepts any expression built from `ode`/`nde` and the ordinary node set. When a variable has multiple blocks, they compose sequentially in insertion order: the first block's mechanism takes the purely mechanistic dx/dt as `ode`; each subsequent block's mechanism takes the *previous* block's already-composed result as its `ode`. This is the only well-defined generalization once `mechanism` is an arbitrary expression rather than a fixed set of categories — unlike the old closed enum, block order is now numerically significant whenever more than one block targets the same variable. This composition happens outside the ordinary `reactions`/`variables[id].fn` sections, so **a consumer must interpret `nn_blocks` to simulate a model that has any of these correctly** — it is not optional bonus metadata the way the field name alone might suggest.

  This section records the architecture needed to regenerate, re-edit, or evaluate a block: `inputs`, `layers` (a `{type, width, activation?}` stack — only `type: "dense"` exists today, but every layer is tagged so a future layer kind is a new variant rather than a restructure), `seed`, `targets`, `trained`, `scale` (the block's initial output-scaling factor), and `mechanism`. Each layer's optional `activation` is a `{name, expression}` pair — `expression` is a portable MathML definition over a single placeholder `x`, `name` lets a backend with its own native implementation, e.g. `"softplus"`, skip evaluating it node-by-node. A layer with no `activation` is a plain linear combination (can take any real value) — the common case for the final layer, but any layer, including the final one, may carry a non-identity activation; there is no separate block-level activation field.

  Weight/bias values are **not** parameters and are **not** stored inline: they live in an external per-block JSON sidecar file (`v1/nn-weights.schema.json`), keyed `w1`/`b1`/`w2`/`b2`/… per layer (1-indexed, matching `layers`), each weight matrix shaped `[out_features, in_features]` (PyTorch/equinox-native — a Keras-backed consumer transposes on import/export). A trained block (`trained: true`) requires `weights_ref`, a path to that sidecar relative to the `.mxl.json` file itself; an untrained block (`trained: false`) forbids `weights_ref` and is initialized from `seed` instead. This split — architecture in the human-readable/diffable model file, weight values in a separate file — mirrors the common pattern across ONNX's `external_data`, HuggingFace's `config.json`/`*.safetensors` split, and glTF's external-buffer mode; unlike those, both files here stay plain JSON since nn_blocks are meant to be small correction nets, not large deep networks. Omitted from the steady-state format, which has no dynamics for a correction term to feed into.

### Presentation metadata

Every entity accepts optional presentation fields so a model round-trips losslessly through mxlweb:

- `displayName` — human-readable label (used by UIs and code generation).
- `texName` — LaTeX rendering of the symbol.
- `slider` — `{ min, max, step, desc? }` interactive-slider config on `variable` / `parameter`. Bounds are **strings** so authored precision is preserved verbatim.

All three are optional: a bare math-only file still validates.

### Units (spec 1.1)

`variable`, `parameter`, `derived`, `readout` and `reaction` entities accept an optional `unit`. A unit is a flat product of factors — the same model as an SBML `unitDefinition` — so every unit has one structure regardless of how it was written (`mol/l/s` and `mol/(l*s)` are the same thing):

```json
"unit": {
  "factors": [
    { "kind": "mole",   "prefix": "micro", "exponent": 1 },
    { "kind": "metre",  "exponent": -2 },
    { "kind": "second", "exponent": -1 }
  ],
  "multiplier": 1
}
```

Value = `multiplier · ∏ (10^prefix · kind)^exponent`. `factors: []` is dimensionless. `multiplier` is optional (default 1) and only for scales no prefix can express.

`kind` must be an id from the shared registry [`v1/units.json`](./v1/units.json) — SI/SBML base and derived units, `minute`/`hour`, and domain units used across the tool family (`mol_chl`, …) — or a **custom unit** declared in the model's own top-level `model.units` section:

```json
"units": { "OD600": { "description": "optical density at 600 nm" } }
```

Custom kinds are opaque base dimensions: mxlpy turns them into `sympy.physics.units.Quantity("OD600")`, SBML export writes them as `dimensionless`. A custom id must not shadow a registry id. Unknown kinds are an error in every consumer — nothing is silently dropped.

`units.json` is the single source of truth for the vocabulary; it records each kind's display symbol, LaTeX, `sympy.physics.units` equivalent and SBML mapping. To add a unit, add it here first, then update the vendored copies (mxlweb-core `src/units/registry.ts`, mxlpy `mxlpy.units.REGISTRY`), whose drift tests compare against this file. [`tests/units.fixtures.json`](./tests/units.fixtures.json) holds cross-language conversion cases that both consumers test against.

### Math node tree

All expressions (rates, derived, readouts, initial values, stoichiometry, derivatives) are recursive trees of nodes under `$defs/node`. Each node has a `type` discriminator:

| `type`            | Operand field(s) | Meaning                           |
| ----------------- | ---------------- | --------------------------------- |
| `Num`             | `value` (number) | Numeric literal                   |
| `Name`            | `value` (string) | Reference to a variable/parameter |
| `Bool`            | `value` (boolean)| Boolean literal                   |
| unary (e.g. `Sin`)| `child`          | Single operand                    |
| `Pow`, `Implies`  | `left`, `right`  | Two operands                      |
| `Log`, `Sqrt`     | `child`, `base`  | Operand plus base/degree          |
| n-ary (`Add`, …)  | `children`       | Variadic operands                 |

## Validation

Install a CLI validator:

```bash
pip install check-jsonschema
# or
npm install -g ajv-cli
```

Validate a model file against the schema matching its `kind`:

```bash
check-jsonschema --schemafile v1/kinetic-model.schema.json path/to/model.mxl.json
# or
ajv validate -s v1/kinetic-model.schema.json -d path/to/model.mxl.json
```

## Editor integration

Add to `.vscode/settings.json` in your project to get IntelliSense on `.mxl.json` files. The file's own `$schema` field takes precedence, so a per-`kind` mapping is only a fallback:

```json
{
  "json.schemas": [
    {
      "fileMatch": ["*.mxl.json"],
      "url": "https://raw.githubusercontent.com/Computational-Biology-Aachen/mxl-schemas/main/v1/kinetic-model.schema.json"
    }
  ]
}
```

## Versioning

Breaking changes to a schema increment `spec_version` inside the schema and are released as a new major version of this repository. Backwards-compatible additions are released as minor versions.

The `$id` of each schema is its canonical URL in this repository. Tools should reference schemas by their `$id` rather than by file path.

## Contributing

Schema changes that affect mxlpy or mxlweb must be coordinated with both consumers. Update the bundled copy in `mxlpy/src/mxlpy/schemas/` and the TypeScript node types in mxlweb alongside any change here.
