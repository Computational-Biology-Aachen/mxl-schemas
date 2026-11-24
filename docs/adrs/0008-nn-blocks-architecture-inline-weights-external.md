# ADR 0008: Neural-Network Blocks: Architecture Inline, Weights External

**Status:** Implemented
**Scope:** `nn_blocks` in the kinetic and ODE schemas; `v0/nn-weights.schema.json`

---

## 1. Context

Universal differential equations add neural-network terms to a model's dynamics. Their architecture is small and meaningful to read; their weights are many numbers that change with every training run.

## 2. Decision

- An `nn_blocks` entry holds the architecture: `inputs`, `layers` (each tagged with a `type`, a `width` and an optional activation given as an expression), `seed`, `targets`, `trained`, `scale` and `mechanism`.
- `mechanism` is an ordinary expression over two placeholders, `ode` (the existing dx/dt term) and `nde` (the block's scaled output); additive, relative and multiplicative composition are presets, not a closed list. Several blocks on one variable compose in order, each taking the previous result as `ode`.
- Weights are not parameters and are not stored inline. A trained block references a weights file (`weights_ref`, relative to the model file; layout `v0/nn-weights.schema.json`, matrices `[out_features, in_features]`). An untrained block is initialised from `seed`.

## 3. Rationale

**Blocks are part of the dynamics** ([ADR 0001](0001-math-first-not-biology-first.md)): a consumer must interpret them to simulate the model, so their composition is spelled out as mathematics rather than as a named category.

**Readable, diffable model files.** Retraining changes the weights file only, the same split as ONNX's external data, HuggingFace's config/weights files and glTF's external buffers.

**Weights are not parameters,** so scans, sliders and fits over parameters never see thousands of network weights.

## 4. Consequences

- Weights are plain JSON today, which suits small correction networks. A binary weights format (e.g. safetensors) for larger networks is left open.
- Block order matters when several blocks target one variable.

## 5. History

- 2026-11-24 (spec_version 0.5): hidden-state blocks, input scales and generic terms, see §6.

## 6. Hidden-state blocks and terms (spec_version 0.5)

**Context.** A block that only maps the current state to a correction can't model memory: delays, unmodelled slow processes, history dependence. MxlPy (#229) adds latent states driven by a small network, and generic terms as the primitive both kinds of block lower to.

**Decision.**

- `hidden_states: n` makes a block own `n` states `{block}_h0 … {block}_h{n-1}`, appended to the state vector after the model's variables: `dh/dt = NN(inputs / input_scales, h)`, the final layer has `n` units. Target `k` gets `(W h)_k` (times `scale`, if given) as `nde`. `W` (`[targets, n]`) and `h0` live in the weights file next to `w1`, `b1`, …; an untrained block starts at `h0 = 0`.
- `scale` is required for blocks without hidden states (unchanged) and optional with them (absent means no scaling): the readout `W` already sets the magnitude of the correction.
- `input_scales` (one positive constant per input, default 1) normalises inputs of very different magnitudes for any block.
- `terms` holds generic terms: an expression `fn`, a `target` (variable, or reaction for kinetic models, `target_kind`) and a `mechanism` over `ode`/`nde`, composing in insertion order like blocks. A variable term acts on the assembled dx/dt, a reaction term rewrites the rate before the stoichiometry fans it out. A term's contribution `mechanism(prev, term) - prev` is a quantity named after the term. Terms, like blocks, never enter the stoichiometric matrix.
- Weight names, for fits and the simulator, follow mxlweb-core: `{block}_w{l}_{i}_{j}`, `{block}_b{l}_{i}` (0-indexed layer `l`), and `{block}_W_{k}_{i}` for the readout.

**Consequences.**

- Writers use 0.5 only for files with hidden states, input scales or terms; earlier files stay valid.
- mxlweb-core rejects hidden-state blocks and terms until it implements them.
