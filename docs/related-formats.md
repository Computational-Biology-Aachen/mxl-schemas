# Related Formats

How the mxl formats relate to established formats, what each does differently, and how they map. The guiding difference throughout: mxl stores the mathematics a simulator runs, not a domain abstraction it has to rewrite first ([ADR 0001](adrs/0001-math-first-not-biology-first.md)).

## Summary

| Format | Covers | Structured around | Closest mxl counterpart |
| --- | --- | --- | --- |
| SBML | models | biology: compartments, species, reactions | kinetic / ODE model |
| CellML | models | mathematics: components, variables, equations | ODE model |
| SED-ML | simulation experiments | models + changes, simulations, tasks, outputs | analysis file |
| COMBINE/OMEX | archives | a zip of model, experiments, data and metadata | — |
| PEtab | parameter estimation problems | conditions, measurements, observables, parameters | readouts (partly) |
| BNGL | rule-based models | molecule patterns and reaction rules | — (the expanded network) |
| ONNX / safetensors | neural-network graphs / weights | tensors, operators | `nn_blocks` + weights file |

## SBML (Systems Biology Markup Language)

XML, currently Level 3 Version 2. A model has compartments, species (with amounts or concentrations, `hasOnlySubstanceUnits`, boundary conditions), parameters, reactions, rules (assignment, rate, algebraic), initial assignments, events, constraints and function definitions; mathematics is Content MathML. Packages extend the core, e.g. `comp` (hierarchical composition), `fbc` (flux balance constraints), `distrib` (distributions), `layout`/`render`.

**What mxl does differently.** SBML's equations follow from its biological structure, so every simulator rewrites them (amounts vs concentrations, compartment volumes in rates). mxl stores the rewritten equations directly; compartments are annotations at most.

**Mapping.**

| SBML | mxl |
| --- | --- |
| species + reactions | kinetic `variables` + `reactions` (stoichiometry as expressions, volumes inside them) |
| rate rule | ODE variable `fn` |
| assignment rule | `derived` (or `readouts`, which SBML does not distinguish) |
| initial assignment | `value` as an expression ([ADR 0004](adrs/0004-every-value-may-be-an-expression.md)) |
| compartment | a parameter used in expressions; membership as an annotation |
| function definition | inlined into expressions on import |
| unitDefinition | `unit` (same flat factor model) |
| events, delays, algebraic rules, constraints | not represented ([ADR 0009](adrs/0009-scope-what-is-left-out.md)) |

Round trips keep the numbers; export writes a single trivial compartment.

## CellML

XML, currently 2.0. A model is a set of components with variables, connected through interfaces; mathematics is Content MathML equations, which may be implicit (algebraic). Units are mandatory and part of the semantics: connected variables with different units are converted. Models can import components from other models.

**What mxl does differently.** CellML is the closest in philosophy, since it too is mathematics-first. It differs in allowing implicit equations (DAEs, out of scope in mxl), in giving units numerical meaning (in mxl units never change a number, [ADR 0006](adrs/0006-units-descriptive-never-numeric.md)), and in component encapsulation and imports, where mxl has a flat namespace of canonical ids ([ADR 0010](adrs/0010-canonical-identifiers.md)).

**Mapping.** Explicit ODE models map to the mxl ODE kind after flattening components and resolving unit conversions into the expressions.

## SED-ML (Simulation Experiment Description Markup Language)

XML, currently Level 1 Version 4. It references models by source and applies changes to them through XPath; defines simulations (uniform time course, steady state, one step) with algorithms identified by KiSAO terms; combines them in tasks and repeated tasks (scans over ranges); computes data generators (MathML over model variables); and declares outputs (2D/3D plots, reports, figures).

**What mxl does differently.** The analysis file ([ADR 0012](adrs/0012-analysis-files.md)) is bound to one model and refers to entities and result columns by canonical id instead of XPath, uses short expression strings instead of MathML ([ADR 0013](adrs/0013-analysis-expression-strings.md)), and has no algorithm ontology: integrator choice is left to each tool, with stored reference values checking that tools agree.

**Mapping.**

| SED-ML | mxl analysis |
| --- | --- |
| model + changes | scenario (`parameters`, `initial`, `edits`) |
| uniformTimeCourse / steadyState | `simulate` (`timeCourse`, `steadyState`) |
| task / repeatedTask with ranges | scenario / `scans` (`over`, `scale`, `grid`) |
| dataGenerator | `deriveEach`, `ops`, `collect`, `derive` |
| plot2D / plot3D / report | `plots` |
| — | `protocol`, `stages`, `mca`, `stability`, `golden` |

## COMBINE/OMEX archive

A zip file with a `manifest.xml` that bundles models, SED-ML files, data and metadata for exchange and publication.

**What mxl does differently.** There is no archive format. An analysis file names its model by `model_id`; neural-network weights are referenced by relative path. Bundling is left to the tools.

## PEtab

Tab-separated tables plus a YAML problem file, around an SBML model: experimental conditions, measurements, observables (formula plus noise model), parameters (bounds, scales, priors) and visualisation.

**What mxl does differently.** Parameter estimation is out of scope for now. Readouts ([ADR 0005](adrs/0005-derived-vs-readouts.md)) correspond to PEtab observable formulas but carry no noise model, and analysis reference values check agreement between tools; they are not measurements.

## BNGL (BioNetGen Language)

Rule-based modelling: molecule types with sites and states, and reaction rules over patterns, from which a (possibly very large) reaction network is generated.

**What mxl does differently.** mxl stores the generated network, the equations that are actually integrated. Rules and patterns are a modelling abstraction above the format, consistent with leaving abstractions to tools.

## ONNX and safetensors

ONNX is a protobuf graph of operators and tensors, with an option to keep large tensors in external data files. safetensors is a binary container of named tensors with a JSON header. Model hubs commonly split a JSON configuration from binary weights.

**What mxl does differently.** `nn_blocks` keep only small correction networks: the architecture is JSON inside the model file and the weights are a separate JSON file ([ADR 0008](adrs/0008-nn-blocks-architecture-inline-weights-external.md)). A binary weights format such as safetensors is left open.
