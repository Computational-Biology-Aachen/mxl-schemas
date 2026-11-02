# ADR 0009: Scope: What the Model Format Leaves Out

**Status:** Implemented (annotations planned, events open)
**Scope:** all model schemas

---

## 1. Context

Mature formats such as SBML cover far more than continuous ODE models: events, delays, algebraic rules, rich annotation. Each addition is a feature every consumer has to implement to simulate a model correctly.

## 2. Decision

| Feature | Status | Reason |
| --- | --- | --- |
| Annotations (MIRIAM/SBO terms, compartment membership) | Planned | Where biology lives ([ADR 0001](0001-math-first-not-biology-first.md)); descriptive, never affecting the mathematics |
| Events (discontinuities, triggers) | Open | Needed for pulses and switches; piecewise-constant inputs are covered by protocols in analyses today, but events change what the integrator steps, so they would be a core addition |
| Delays (delay differential equations) | Out of scope | A different mathematical object, beyond what consumers' integrators run |
| Algebraic rules (DAEs) | Out of scope | Same reason; explicit algebraic relations are `derived` quantities |

## 3. Rationale

**Everything in the core must be simulated by every consumer.** Keeping the core to explicit ODEs and algebraic outputs keeps every consumer able to run every valid file. Additions that do not affect the mathematics (annotations) are cheap; additions that do (events) need every integrating consumer to support them first.

## 4. Consequences

- Models needing delays or DAEs cannot be represented; importers reject them rather than approximate.
- Until annotations exist, biological structure from imported models is dropped.
