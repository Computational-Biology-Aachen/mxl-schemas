# mxl-schemas: Architecture Context

The entry point for understanding *why* the mxl file formats are shaped the way they are. mxl-schemas has no dependencies: it is JSON Schemas, rule files and fixtures that consumers in any language vendor and test against.

## The Central Fact

A model file stores the mathematical model, not the biology. Everything else follows from that.

→ [ADR 0001 — The model is the mathematics, not the biology](0001-math-first-not-biology-first.md)

## The Model Format

→ [ADR 0002 — Three model kinds, split by formulation](0002-three-kinds-by-formulation.md)
→ [ADR 0003 — Model mathematics as JSON node trees](0003-model-math-as-json-node-trees.md)
→ [ADR 0004 — Every value may be an expression](0004-every-value-may-be-an-expression.md)
→ [ADR 0005 — Derived quantities and readouts are separate](0005-derived-vs-readouts.md)
→ [ADR 0008 — Neural-network blocks: architecture inline, weights external](0008-nn-blocks-architecture-inline-weights-external.md)
→ [ADR 0009 — Scope: what the model format leaves out](0009-scope-what-is-left-out.md)
→ [ADR 0014 — Array nodes and model data](0014-array-nodes-and-model-data.md) (model restriction amended by ADR 0015)
→ [ADR 0015 — Array-valued intermediates](0015-array-valued-intermediates.md)

## What Never Changes a Result

Optional, descriptive, ignorable without changing any number.

→ [ADR 0006 — Units are descriptive and never change numbers](0006-units-descriptive-never-numeric.md)
→ [ADR 0007 — Presentation metadata lives in the model file](0007-presentation-metadata-in-the-model.md)

## Shared Contracts

→ [ADR 0010 — Canonical identifiers](0010-canonical-identifiers.md)
→ [ADR 0011 — Versioning, vendored copies and strict rejection](0011-versioning-and-vendoring.md)

## Analyses (experimental)

→ [ADR 0012 — Analysis files](0012-analysis-files.md)
→ [ADR 0013 — Analysis expressions are strings](0013-analysis-expression-strings.md) (superseded by ADR 0014)

## Related Formats

How SBML, CellML, SED-ML, PEtab and others compare: [related-formats.md](../related-formats.md).
