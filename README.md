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

### Envelope

Every model file shares the same outer shape:

```json
{
  "$schema": "https://raw.githubusercontent.com/Computational-Biology-Aachen/mxl-schemas/main/v1/<kind>-model.schema.json",
  "spec_version": "1.0",
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

- **variables** — state variables with an initial `value`; in the ODE format each also carries its derivative `fn`.
- **parameters** — constants with a `value`.
- **reactions** — a rate `fn` and a per-variable `stoichiometry` map (kinetic only).
- **derived** — quantities computed from other entities at each time point; in the steady-state format these are the model's outputs.
- **readouts** — report-only quantities that do not feed back into the dynamics. Omitted from the steady-state format, which has no dynamics.

### Presentation metadata

Every entity accepts optional presentation fields so a model round-trips losslessly through mxlweb:

- `displayName` — human-readable label (used by UIs and code generation).
- `texName` — LaTeX rendering of the symbol.
- `slider` — `{ min, max, step, desc? }` interactive-slider config on `variable` / `parameter`. Bounds are **strings** so authored precision is preserved verbatim.

All three are optional: a bare math-only file still validates.

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
