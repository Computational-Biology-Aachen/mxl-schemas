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

A fourth schema, [`v1/nn-weights.schema.json`](./v1/nn-weights.schema.json), describes the external weight/bias sidecar file that an `nn_block`'s `weights_ref` points to — not a `.mxl.json` document itself, no envelope/`kind` discriminator. A fifth, [`v1/model-data.schema.json`](./v1/model-data.schema.json), likewise describes the data sidecar a model's `data_ref` points to (see [Model data](#model-data)).

### Envelope

Every model file shares the same outer shape:

```json
{
  "$schema": "https://raw.githubusercontent.com/Computational-Biology-Aachen/mxl-schemas/main/v1/<kind>-model.schema.json",
  "spec_version": "1.1",
  "kind": "kinetic | ode | steady-state",
  "model_id": "my_model",
  "description": "optional human-readable description",
  "data_ref": "optional: model.data.json (spec_version 1.2)",
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

`kind` must be an id from the shared registry [`v1/units.json`](./v1/units.json) — SI/SBML base and derived units, `minute`/`hour`/`bar`, and domain units used across the tool family (`mol_chl`, `einstein` = mol photons, …) — or a **custom unit** declared in the model's own top-level `model.units` section:

```json
"units": { "OD600": { "description": "optical density at 600 nm" } }
```

Custom kinds are opaque base dimensions: mxlpy turns them into `sympy.physics.units.Quantity("OD600")`, SBML export writes them as `dimensionless`. A custom id must not shadow a registry id. Unknown kinds are an error in every consumer — nothing is silently dropped.

`units.json` is the single source of truth for the vocabulary; it records each kind's display symbol, LaTeX, `sympy.physics.units` equivalent and SBML mapping. To add a unit, add it here first, then update the vendored copies (mxlweb-core `src/units/registry.ts`, mxlpy `mxlpy.units.REGISTRY`), whose drift tests compare against this file. [`tests/units.fixtures.json`](./tests/units.fixtures.json) holds cross-language conversion cases that both consumers test against.

### Identifiers

Entity ids are free-form strings in mxlpy (`"CO2 (dissolved)"`), but every code exporter needs them as identifiers. [`v1/identifiers.json`](./v1/identifiers.json) defines the one canonical mapping both mxlpy and mxlweb-core use, so a model has the same ids in Python and JavaScript: ASCII `[A-Za-z_][A-Za-z0-9_]*` (WAT locals are ASCII-only), Greek and a few Latin letters transliterated (`Δψ` → `Deltapsi`), biochemical symbols spelled out (`P700+FA-` → `P700_plus_FA_minus`, `Fd*` → `Fd_star`, `ATP/tot` → `ATP_per_tot`; a `-` between letters is a hyphen: `Light-harvesting` → `Light_harvesting`), other invalid runs collapsed to `_`, and a `_` suffix for Python/JavaScript keywords and names the generated code uses itself (`time`, `m`, `pars`, `Math`, …). Two names of one model mapping to the same identifier is an error. The rules are idempotent: a canonical id maps to itself. [`tests/identifiers.fixtures.json`](./tests/identifiers.fixtures.json) holds the cross-language cases both consumers test against.

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
| array (`Simpson`, …) | `children`    | Reduce or select from a 1-D array |

Every node broadcasts element-wise over 1-D arrays (a number combines with every element, two arrays element by element and must have equal lengths). Nine array nodes reduce or select ([ADR 0014](docs/adrs/0014-array-nodes-and-model-data.md)): `Sum`, `Mean`, `Std` (ddof = 1), `MaxOf`, `MinOf` (`[a]`), `Index` (`[a, i]`, 0-based, negative from the end), `Slice` (`[a, start, stop]`, end exclusive), `At` (`[a, t, times]`, the element at the sample of `times` nearest `t`) and `Simpson` (`[y, x]`, `scipy.integrate.simpson(y, x=x)`). `Max`/`Min` stay n-ary and element-wise.

### Model data

Named 1-D arrays, such as spectra, live in a sidecar file that the model's `data_ref` names (relative to the model file; [`v1/model-data.schema.json`](./v1/model-data.schema.json)): `{"<id>": {"values": [...], "unit"?, "description"?}}`. A table is one array per column; a shared axis (e.g. wavelength) is an array of its own. Math reaches data only through array subtrees that reference nothing but data and numbers and reduce to a number, so each is a constant a consumer evaluates once per data set, e.g. `Mul(chla_content, Simpson(Mul(abs_coef_chla, light), wavelength))`. Data are not parameters: scans, sliders and fits never see them.

## Analyses

[`v1/analysis.schema.json`](./v1/analysis.schema.json) (`kind: "analysis"`, `spec_version: "1.1"`) describes what is done *with* a model: simulations, data handling, plots and checks, as plain data any backend can run. GreenSloth runs them in the browser and exports them as MxlPy notebooks; the two are held to the same reference values. It is deliberately much smaller than SED-ML: no fitting, sampling or sensitivity analysis yet.

```json
{
  "$schema": "https://raw.githubusercontent.com/Computational-Biology-Aachen/mxl-schemas/main/v1/analysis.schema.json",
  "spec_version": "1.1",
  "kind": "analysis",
  "model": { "model_id": "poolman2000", "kind": "kinetic" },
  "analyses": [
    {
      "id": "fig3",
      "title": "Effect of cytosolic phosphate",
      "simulate": { "kind": "steadyState" },
      "scans": { "scan": { "over": { "Orthophosphate_external": [0.05, 0.1, 0.2] }, "columns": ["ex_g1p"] } },
      "plots": [
        {
          "type": "line",
          "x": { "type": "Name", "value": "scan.x" },
          "y": [{ "of": { "type": "Name", "value": "scan.ex_g1p" }, "label": "Starch flux" }]
        }
      ]
    }
  ]
}
```

An analysis file is bound to one model. Each entry in `analyses` is one figure or experiment:

| Section | What it gives |
| --- | --- |
| `scenarios` | Named runs of modified copies of the model (`parameters`, `initial`, structural `edits`, `simulate`, unrecorded `pre` runs, chained `stages`). Columns: `<scenario>.<column>` |
| `simulate` | Default run: `timeCourse` (`tEval`), `protocol` (steps holding parameter values, `pointsPerStep` or `tEval`) or `steadyState` |
| `scans` | One run per row of scanned values (`over`, relative `scale`, `grid` for a cartesian product); the final values of `columns` form the table `<name>.x`, `<name>.index`, `<name>.<column>` |
| `mca` | Response coefficients (outputs at steady state vs parameters) and parameter or variable elasticities (rates vs parameters or variables), by central differences as MxlPy's `mca`. Table: `<name>.x` (index into `wrt`), `<name>.<output>` |
| `stability` | Jacobian eigenvalues at the steady state, sorted by real then imaginary part. Table: `<name>.x`, `<name>.real`, `<name>.imag` |
| `deriveEach`, `ops` | Per-scenario columns: expressions, and named ops (below) |
| `collect`, `derive` | Tables and columns across scenarios |
| `plots` (optional) | `line`, `scatter`, `stackedBar`, `heatmap` over expressions |
| `golden` (optional) | Series checked against stored reference values, by max \|sim − reference\| / range(reference) (default tolerance 0.01) |

**Which analyses a model kind allows.** This depends on what the model has: time, variables and reactions. The schema enforces it from `model.kind`; checking that ids exist in the model is left to consumers.

| Needs | kinetic | ode | steady-state | Analyses |
| --- | :-: | :-: | :-: | --- |
| — | ✓ | ✓ | ✓ | `steadyState` (a steady-state model is evaluated), steady-state scans, response coefficients, parameter changes, `setAssignment`, `addParameter`, `parameterToAssignment`, `setData` (replace a model data array), expressions, tables, plots |
| time | ✓ | ✓ | — | `timeCourse`, `protocol`, `pre`, `stages`, time-course scans, named ops, `returnRhs` |
| variables | ✓ | ✓ | — | `initial`, `clampVariable`, `stability`, elasticities at a variable state |
| reactions | ✓ | — | — | `removeReaction`, parameter and variable elasticities |

### Expressions

Analysis expressions are node trees ([ADR 0014](docs/adrs/0014-array-nodes-and-model-data.md)): the model formats' nodes, with references as `Name`s the consumer resolves, so a consumer only evaluates trees. They are written as short strings, compiled by one reference parser (mxlweb-core's `parseExpression`) to the stored tree:

- numbers (`1`, `2.5e-3`), `+ - * / ^` (`^` is right-associative and binds tighter than unary minus: `-k ^ 2` is `-(k^2)`), parentheses
- references: `col` (inside a scenario), `scenario.col`, `table.col`, `param.<id>` and `init.<id>` (the model's defaults), `data.<name>`, `ddt.<variable>`
- element-wise: `log10 log2 ln exp sqrt abs sin`
- aggregates, reducing an array to a number: `mean sum min max first last std` (`std` uses ddof = 1)
- `at(col, t, times)` (the value of `col` at the sample of `times` nearest `t`), `nth(col, i)` (0-based), `slice(col, from, to)` (end exclusive), `simpson(y, x)`, `ifgt(a, b, x, y)` (`x` if `a > b`, else `y`)

| String | Tree |
| --- | --- |
| `wt.x - first(wt.x)` | `Minus(Name("wt.x"), Index(Name("wt.x"), Num(0)))` |
| `-log10(H * 1e-6)` | `Minus(Log(Mul(Name("H"), Num(1e-6)), Num(10)))` |
| `mean`/`sum`/`min`/`max`/`std` | `Mean`/`Sum`/`MinOf`/`MaxOf`/`Std` |
| `last(a)`, `nth(a, i)`, `slice`, `at`, `simpson` | `Index(a, -1)`, `Index(a, i)`, `Slice`, `At`, `Simpson` |
| `ifgt(a, b, x, y)` | `Piecewise(x, GreaterThan(a, b), y)` |

Arrays combine element-wise and must have equal lengths; a number broadcasts. [`tests/expressions.fixtures.json`](./tests/expressions.fixtures.json) holds cross-language cases: each string, its tree and the tree's value.

### Named ops

An `ops` entry other than `column` names an operation over one scenario's table, with its arguments as plain column names: `pamNpq` (NPQ from a PAM protocol's saturating pulses), `peaks`, `valleys`, `gaussianSmooth`, `gradient`, `diff`, `cumTrapz`, `ojip` (O-J-I-P points of a fluorescence rise) and `range` (a time window). They follow numpy/scipy semantics (`scipy.signal.find_peaks`, `gaussian_filter1d`, `numpy.gradient`, `cumulative_trapezoid`). [`tests/analysis.fixtures.json`](./tests/analysis.fixtures.json) holds valid and invalid analysis documents.

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

## Design decisions

Why the formats are shaped the way they are is recorded as ADRs, starting at [`docs/adrs/CONTEXT.md`](./docs/adrs/CONTEXT.md). [`docs/related-formats.md`](./docs/related-formats.md) compares them with SBML, CellML, SED-ML, COMBINE/OMEX, PEtab, BNGL and ONNX/safetensors.

## Contributing

Schema changes that affect mxlpy or mxlweb must be coordinated with both consumers. Update the bundled copy in `mxlpy/src/mxlpy/schemas/` and the TypeScript node types in mxlweb alongside any change here. The analysis schema is vendored in GreenSloth (`src/lib/validation/analysis.schema.json`), whose tests fail when it drifts from this copy.
