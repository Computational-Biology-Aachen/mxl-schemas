# ADR 0002: Three Model Kinds, Split by Formulation

**Status:** Implemented
**Scope:** `v1/kinetic-model.schema.json`, `v1/ode-model.schema.json`, `v1/steady-state-model.schema.json`

---

## 1. Context

Models in this tool family come in three mathematical shapes: reaction networks, systems of ODEs that are not naturally reaction networks, and algebraic models with no time at all. One schema with optional sections could hold all three, but then which sections combine, and what a consumer has to run, would depend on which sections happen to be present.

## 2. Decision

One schema per formulation, selected by a required top-level `kind`:

| `kind` | Formulation | dx/dt |
| --- | --- | --- |
| `kinetic` | reactions × stoichiometry | computed as N·v |
| `ode` | one expression per variable | the variable's `fn` |
| `steady-state` | algebraic outputs of the parameters | none, there is no time |

Each schema is closed: it lists exactly the sections its formulation has.

## 3. Rationale

**The kind says which mathematical object to run** ([ADR 0001](0001-math-first-not-biology-first.md)). A consumer picks the schema and the evaluation strategy from `kind`, without inspecting the structure.

**No invented structure.** An ODE model is not forced into fake reactions to fit N·v, and a steady-state model has no variables or time to pretend about. Conversions between kinds are a tool's job; only kinetic → ode is lossless.

**Closed schemas stay simple.** There are no rules of the form "reactions are optional unless…".

## 4. Consequences

- Shared definitions (math nodes, units, parameters, presentation fields) are duplicated across the three schema files, so each stays self-contained.
- Analyses depend on the kind: a steady-state model has no time courses, an ODE model has no reactions ([ADR 0012](0012-analysis-files.md)).

## 5. Open question

Whether the shared definitions move into a common schema file referenced by all three, trading self-contained files for a single definition of each shared part, is undecided.
