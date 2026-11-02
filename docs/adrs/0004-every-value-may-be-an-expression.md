# ADR 0004: Every Value May Be an Expression

**Status:** Implemented
**Scope:** `value` of variables and parameters; `stoichiometry` of reactions

---

## 1. Context

SBML spreads "where a number comes from" over several constructs: constant attributes, `initialAssignment`, assignment rules and rate rules, plus constant-only stoichiometry by default. Each is a separate concept a consumer has to support.

## 2. Decision

Every number in a model is a node tree ([ADR 0003](0003-model-math-as-json-node-trees.md)): a `Num` constant or an expression.

- **A variable's initial value** may be an expression, e.g. `Ci = 0.65 · Ca`, evaluated once at t = 0.
- **A parameter's value** may be an expression, also evaluated once at t = 0, e.g. from a variable's initial value. This is distinct from a `derived` quantity, which is recomputed whenever its inputs change.
- **A stoichiometric coefficient** may be an expression, constant or changing over time.

Initial expressions are evaluated in dependency order; a cycle is invalid.

## 3. Rationale

**One rule instead of several constructs.** A consumer evaluates a value the way it evaluates any expression ([ADR 0001](0001-math-first-not-biology-first.md)).

**"Computed once" is a concept of its own.** A quantity fixed from the initial state, which must not follow that state afterwards, cannot be expressed as a `derived` quantity. Without expression-valued parameters the format could not say it.

**Stoichiometry carries what compartments would.** With volumes as parameters rather than compartments, a coefficient such as `V_stroma / V_lumen` has to be an expression.

## 4. Consequences

- A parameter with an expression value is not a free input: setting it (a slider, a scan, a fit) replaces its expression with a number.
- Dependency order and the absence of cycles cannot be checked by a schema; consumers check them.
- In the models of this tool family so far, every parameter is a constant and only variable initial values use expressions. Some consumers accept only constant parameters; that is a gap in those consumers, not a rule of the format.
