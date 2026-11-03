# ADR 0014: Array Nodes and Model Data

**Status:** Implemented
**Scope:** `$defs/node` in every schema; `data_ref` in the model schemas; `v1/model-data.schema.json`; `$defs/expression` in `v1/analysis.schema.json`; `tests/expressions.fixtures.json`
**Supersedes:** [ADR 0013](0013-analysis-expression-strings.md)

---

## 1. Context

Two places needed operations over arrays, which the scalar MathML vocabulary ([ADR 0003](0003-model-math-as-json-node-trees.md)) lacks:

- **Analyses** compute over result columns: differences between scenarios, the last value of a time course, a mean. ADR 0013 handled this with a string language. That meant every consumer of an analysis needed its own expression parser.
- **Models with spectral inputs** (pfennig2024: light spectra, pigment absorption per wavelength) integrate products of spectra. With no way to write that, the model could not be exported at all.

Both need the same small set of operations: element-wise arithmetic over 1-D arrays, plus a few operations that reduce an array or select from it.

## 2. Decision

**Values are numbers or 1-D arrays.** Every existing node broadcasts element-wise. A number combines with every element; two arrays combine element by element and must have equal lengths.

**Nine array nodes** reduce or select. Their operands are in `children`, and they follow numpy/scipy:

| Node | Operands | Meaning |
| --- | --- | --- |
| `Sum`, `Mean`, `MaxOf`, `MinOf` | `[a]` | `np.sum`, `np.mean`, `np.max`, `np.min` |
| `Std` | `[a]` | `np.std(a, ddof=1)` |
| `Index` | `[a, i]` | element `i`, 0-based, negative counts from the end |
| `Slice` | `[a, start, stop]` | `a[start:stop]` |
| `At` | `[a, t, times]` | the element at the sample of `times` nearest `t` |
| `Simpson` | `[y, x]` | `scipy.integrate.simpson(y, x=x)` |

`Max`/`Min` keep their n-ary, element-wise meaning. That is why the reductions have their own names.

**Model data** is a set of named 1-D arrays. It lives in a sidecar file (`data_ref`, relative to the model file; layout `v1/model-data.schema.json`), as nn weights do ([ADR 0008](0008-nn-blocks-architecture-inline-weights-external.md)). A table is stored as one array per column, and a shared axis such as wavelength is an array of its own.

- An array subtree in a model may reference **only data and numbers**. It must reduce to a number before it is used. Each such subtree is therefore a constant: consumers evaluate it once per data set, and simulation, Jacobians and gradients stay scalar.
- Data are not parameters. Scans, sliders and fits never see them. An analysis or a site changes a model's data by replacing it, the same way it changes a parameter value.
- Model files with data are `spec_version` 1.2. Files without data are unchanged.

**Analysis expressions are node trees.** The string syntax of ADR 0013 (README: Expressions, plus `simpson(y, x)`) remains the authoring form. mxlweb-core's `parseExpression` is its single reference parser. A file stores the tree, with references as dotted `Name`s (`wt.NPQ`, `param.k`, `data.m`) that the consumer resolves. Analysis files move to `spec_version` 1.1.

## 3. Rationale

**One vocabulary, one evaluator.** The same nodes serve model math and analyses. A consumer evaluates trees and never parses strings, and the model formats' tooling (JSON revival, LaTeX, Python export) covers analyses for free.

**Reductions, not array-valued model state.** Data feeds a model only through constants, so no backend has to represent arrays: WAT/C integrators, SBML export and adjoint gradients are untouched. A model whose arrays depend on its state would need array-valued codegen. It is left out until a model needs it.

**Sidecar data.** Spectra are thousands of numbers that change independently of the model's structure. Keeping them out of the model file keeps that file readable and diffable, as ADR 0008 does for weights.

**People still write strings.** Analysis definitions are written by hand, and short strings stay the authoring form. Only the stored form changes.

## 4. Consequences

- Analysis files are no longer valid with string expressions. The analysis format is experimental (ADR 0012), so this is a format change under the same `v1/` directory rather than a new major version.
- An array subtree that references a parameter or variable is rejected. Lifting that restriction means evaluating array subtrees inside the right-hand side.
- `tests/expressions.fixtures.json` pins the parser (`src` to `tree`) and the evaluator (`tree` to `value`) across languages.
