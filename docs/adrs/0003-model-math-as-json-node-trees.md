# ADR 0003: Model Mathematics as JSON Node Trees

**Status:** Implemented
**Scope:** `$defs/node` in every model schema; every `fn`, `value` and stoichiometric coefficient

---

## 1. Context

Every expression in a model (rates, derived quantities, readouts, ODE right-hand sides, initial values, stoichiometric coefficients) has to be stored somehow. The options are text in some syntax, which every consumer must parse, or a structured tree.

## 2. Decision

Model expressions are JSON trees of typed nodes, using the operator vocabulary of Content MathML:

```json
{ "type": "Mul", "children": [{ "type": "Name", "value": "k1" }, { "type": "Name", "value": "S" }] }
```

Each node has a `type` discriminator; leaves are `Num`, `Name` and `Bool`; operators carry `child`, `left`/`right`, `child`/`base` or `children`.

## 3. Rationale

**The mathematics is the core, so it must be trivially executable** ([ADR 0001](0001-math-first-not-biology-first.md)). A tree needs no parser and no precedence rules, and every consumer can walk it straight into its target: JavaScript, WebAssembly, Python, LaTeX or SBML MathML.

**The schema can check it.** Node types and their operands are validated by the schema itself, which a string cannot offer.

**MathML's vocabulary maps 1:1 to SBML.** Import and export translate node for node, with no expression rewriting.

## 4. Consequences

- Files are verbose and not meant to be written by hand; tools generate them.
- Analysis files use expression strings instead, for reasons specific to them ([ADR 0013](0013-analysis-expression-strings.md)), so the tool family has two expression representations.
