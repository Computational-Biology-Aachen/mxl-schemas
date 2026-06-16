# mxl-schemas

Canonical JSON Schema definitions for the mxl\* tool family ([mxlpy](https://github.com/Computational-Biology-Aachen/mxlpy), [mxlweb](https://github.com/Computational-Biology-Aachen/mxlweb)).

All schemas target [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12).

## Schemas

| File                                               | Format                          | Consumers     |
| -------------------------------------------------- | ------------------------------- | ------------- |
| [`mxl-model.schema.json`](./mxl-model.schema.json) | `.mxl.json` native model format | mxlpy, mxlweb |

### `mxl-model.schema.json`

Version-controllable JSON representation of a MxlPy model (`spec_version: "1.0"`).

A `.mxl.json` file captures the complete model structure:

- **variables** — state variables with initial values
- **parameters** — constants with values
- **reactions** — rate functions and stoichiometry
- **derived** — derived quantities computed from state
- **readouts** — output quantities



#### mxlpy usage

```python
import mxlpy

mxlpy.save(model, "my_model.mxl.json")
model = mxlpy.load("my_model.mxl.json")
```

## Validation

Install the CLI validator:

```bash
pip install check-jsonschema
# or
npm install -g ajv-cli
```

Validate a model file:

```bash
check-jsonschema --schemafile mxl-model.schema.json path/to/my_model.mxl.json
# or
ajv validate -s mxl-model.schema.json -d path/to/my_model.mxl.json
```

## Editor integration

Add to `.vscode/settings.json` in your project to get IntelliSense on `.mxl.json` files:

```json
{
  "json.schemas": [
    {
      "fileMatch": ["*.mxl.json"],
      "url": "https://raw.githubusercontent.com/Computational-Biology-Aachen/mxl-schemas/main/mxl-model.schema.json"
    }
  ]
}
```

## Versioning

Breaking changes to a schema increment `spec_version` inside the schema and are released as a new major version of this repository. Backwards-compatible additions are released as minor versions.

The `$id` of each schema is its canonical URL in this repository. Tools should reference schemas by their `$id` rather than by file path.

## Contributing

Schema changes that affect mxlpy or mxlweb must be coordinated with both consumers. Update the bundled copy in `mxlpy/src/mxlpy/schemas/` and the TypeScript node types in mxlweb alongside any change here.
