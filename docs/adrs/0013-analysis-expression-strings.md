# ADR 0013: Analysis Expressions Are Strings

**Status:** Experimental
**Scope:** `$defs/expression` in `v1/analysis.schema.json`; `tests/expressions.fixtures.json`

---

## 1. Context

Analyses compute columns from results: differences between scenarios, ratios to parameters, aggregates such as the last value of a time course. Model files store expressions as node trees ([ADR 0003](0003-model-math-as-json-node-trees.md)).

## 2. Decision

Analysis expressions are strings in a small language: numbers, `+ - * / ^`, unary minus, parentheses; references (`col`, `scenario.col`, `table.col`, `param.id`, `init.id`, `data.name`, `ddt.var`); element-wise functions; aggregates; and `at`, `nth`, `slice`, `ifgt`. The grammar is described in the README and pinned down by cross-language fixtures.

## 3. Rationale

**They are a different kind of expression.** They refer to result columns, not model entities, and MathML has no notion of a column reference or an aggregate over a time course.

**People write them.** They are short and written by hand in analysis definitions, where node trees would be unreadable.

## 4. Consequences

- The tool family has two expression representations; consumers of analyses need a small parser.
- The language is experimental and may change.
