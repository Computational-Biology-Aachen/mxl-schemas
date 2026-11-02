# ADR 0010: Canonical Identifiers

**Status:** Implemented (rules and fixtures); schema enforcement pending
**Scope:** `v1/identifiers.json`, `tests/identifiers.fixtures.json`; entity ids in every model file

---

## 1. Context

Model authors use free-form names (`CO2 (dissolved)`, `Fd*`, `Δψ`), but every code generator needs identifiers, and different languages forbid different things. If each consumer sanitised names its own way, the same model would have different ids in Python, JavaScript and WebAssembly, and anything referring to entities (analyses, references, generated code) would need translation tables.

## 2. Decision

- `v1/identifiers.json` defines one mapping from names to identifiers: ASCII `[A-Za-z_][A-Za-z0-9_]*`, Greek and some Latin letters transliterated, biochemical symbols spelled out (`Fd*` → `Fd_star`, `ATP/tot` → `ATP_per_tot`), other invalid runs collapsed to `_`, and a `_` suffix for keywords and names generated code reserves. The mapping is idempotent; two names of one model mapping to the same identifier is an error.
- Entity ids in a model file must already be canonical. Free-form names go into `displayName` ([ADR 0007](0007-presentation-metadata-in-the-model.md)).

## 3. Rationale

**One id per entity everywhere.** A model has the same ids in every language and every file that refers to it.

**Rules as data.** The mapping is a rule file plus cross-language fixtures, so each consumer implements it against the same contract and the schemas stay free of code.

## 4. Consequences

- The model schemas do not yet enforce the identifier pattern on entity keys (only on custom unit kinds); adding `propertyNames` patterns is a follow-up.
