# ADR 0008: Neural-Network Blocks: Architecture Inline, Weights External

**Status:** Implemented
**Scope:** `nn_blocks` in the kinetic and ODE schemas; `v1/nn-weights.schema.json`

---

## 1. Context

Universal differential equations add neural-network terms to a model's dynamics. Their architecture is small and meaningful to read; their weights are many numbers that change with every training run.

## 2. Decision

- An `nn_blocks` entry holds the architecture: `inputs`, `layers` (each tagged with a `type`, a `width` and an optional activation given as an expression), `seed`, `targets`, `trained`, `scale` and `mechanism`.
- `mechanism` is an ordinary expression over two placeholders, `ode` (the existing dx/dt term) and `nde` (the block's scaled output); additive, relative and multiplicative composition are presets, not a closed list. Several blocks on one variable compose in order, each taking the previous result as `ode`.
- Weights are not parameters and are not stored inline. A trained block references a weights file (`weights_ref`, relative to the model file; layout `v1/nn-weights.schema.json`, matrices `[out_features, in_features]`). An untrained block is initialised from `seed`.

## 3. Rationale

**Blocks are part of the dynamics** ([ADR 0001](0001-math-first-not-biology-first.md)): a consumer must interpret them to simulate the model, so their composition is spelled out as mathematics rather than as a named category.

**Readable, diffable model files.** Retraining changes the weights file only, the same split as ONNX's external data, HuggingFace's config/weights files and glTF's external buffers.

**Weights are not parameters,** so scans, sliders and fits over parameters never see thousands of network weights.

## 4. Consequences

- Weights are plain JSON today, which suits small correction networks. A binary weights format (e.g. safetensors) for larger networks is left open.
- Block order matters when several blocks target one variable.
