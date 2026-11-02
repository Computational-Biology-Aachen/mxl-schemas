# ADR 0012: Analysis Files

**Status:** Experimental
**Scope:** `v1/analysis.schema.json`, `tests/analysis.fixtures.json`

---

## 1. Context

What is done with a model (simulations, scans, control analysis, data handling, figures, checks against reference values) is usually code in one tool's language. To run the same analysis in several tools and check that they agree, it has to be data. SED-ML is the established standard for simulation experiments and PEtab for parameter estimation problems.

## 2. Decision

An analysis file (`kind: "analysis"`) is bound to one model by `model_id` and `kind`, and holds a list of analyses: scenarios, simulations (time course, protocol, steady state), scans, metabolic control analysis, local stability, per-scenario data handling, optional plots and optional checks against stored reference values.

Which analyses are possible follows from what the model kind has (time, variables, reactions; [ADR 0002](0002-three-kinds-by-formulation.md)), and the schema enforces it from `model.kind`. Whether ids exist in the model is left to consumers.

## 3. Rationale

**Smaller than SED-ML.** SED-ML refers into models through XPath over XML and relies on KiSAO terms and a full simulation ontology. Analyses here refer to result columns by id and stay short enough to write by hand.

**Not PEtab.** PEtab describes measurements, noise models and priors for estimation; fitting is out of scope for now.

**Built for running on several tools.** The point is a small, closed set of steps each tool can implement, with reference values checking that they agree, rather than an open standard.

## 4. Consequences

- While experimental, the format may change incompatibly within `spec_version` 1.0, an explicit exception to the versioning rule of [ADR 0011](0011-versioning-and-vendoring.md); it becomes subject to that rule once its status leaves Experimental.
- Fitting, sampling and sensitivity analysis are not covered.
- A rule for when new analysis kinds are added (e.g. only once two tools implement them and reference values pin them down) is under consideration, not decided.
