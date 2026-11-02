# ADR 0006: Units Are Descriptive and Never Change Numbers

**Status:** Implemented (spec 1.1)
**Scope:** `unit` on variables, parameters, derived quantities, readouts and reactions; `v1/units.json`

---

## 1. Context

Units document a model, allow consistency checks and are needed for SBML export. They could also be used to convert values, e.g. to rescale a model's time unit.

## 2. Decision

- `unit` is optional everywhere; a file without units is valid.
- A unit is a flat product of factors `{kind, prefix, exponent}` times a `multiplier`, the same model as an SBML `unitDefinition`, with a shared registry of kinds (`v1/units.json`) and custom kinds per model.
- Units never change a number. Values are exactly what the integrator uses; no consumer converts or rescales because of a unit.

## 3. Rationale

**The numbers are the model** ([ADR 0001](0001-math-first-not-biology-first.md)). A consumer may ignore units completely and still simulate correctly.

**One representation per unit.** As a flat product, `mol/l/s` and `mol/(l·s)` are the same object, comparison is trivial and SBML export is 1:1.

**Optional, because published models often lack consistent units.** Requiring them would invite made-up ones.

## 4. Consequences

- A unit mismatch is a warning from a checking tool, never a conversion.
- Changing a model's time or concentration scale means rewriting its values and expressions; the format does not do it implicitly.
