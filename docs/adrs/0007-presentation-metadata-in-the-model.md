# ADR 0007: Presentation Metadata Lives in the Model File

**Status:** Implemented
**Scope:** `displayName`, `texName`, `slider` on entities

---

## 1. Context

Tools present models to people: readable names, LaTeX symbols, sliders with sensible ranges. This is not mathematics, and could live in a separate file.

## 2. Decision

Presentation fields are optional entity fields in the model file:

- `displayName`: a human-readable label
- `texName`: the LaTeX rendering of the symbol
- `slider`: `{min, max, step, desc?}`, with bounds as strings so authored precision is kept verbatim

They never affect the mathematics.

## 3. Rationale

**Lossless round trips.** A model moves between tools and code generators without losing what people use to read and explore it; a separate presentation file would be lost or drift out of sync.

**Compatible with math-first** ([ADR 0001](0001-math-first-not-biology-first.md)) under one rule: optional, and ignorable without changing any result.

**Strings for bounds,** so `0.1` stays `0.1` rather than its nearest binary double.

## 4. Consequences

- A math-only file is valid; tools fall back to ids.
- Slider bounds are parsed by consumers that need them as numbers.
