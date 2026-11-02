# ADR 0005: Derived Quantities and Readouts Are Separate

**Status:** Implemented
**Scope:** `derived` and `readouts` sections of the kinetic and ODE schemas

---

## 1. Context

Models compute quantities from their state: some feed the dynamics (a rate depends on them), others are only reported (a fluorescence signal, a ratio shown in a figure).

## 2. Decision

- **`derived`** quantities are computed from other entities at each time point and may be used anywhere in the dynamics.
- **`readouts`** are report-only: no rate, derived quantity, ODE right-hand side or other dynamic part may depend on one. A readout may depend on derived quantities and earlier readouts.
- Steady-state models have no `readouts`: without dynamics, every output is a derived quantity.

## 3. Rationale

**Performance.** A consumer can leave readouts out of the compiled right-hand side and its Jacobian entirely, and compute them only for output.

**Meaning.** Readouts are observables: measurement-like signals that can be added or changed without touching the model's dynamics, and that are guaranteed not to influence them.

## 4. Consequences

- That nothing in the dynamics references a readout is a reference check the schema cannot express; consumers check it.
