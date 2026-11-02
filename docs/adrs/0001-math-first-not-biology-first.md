# ADR 0001: The Model Is the Mathematics, Not the Biology

**Status:** Implemented
**Scope:** every model schema (`v1/kinetic-model.schema.json`, `v1/ode-model.schema.json`, `v1/steady-state-model.schema.json`)

---

## 1. Context

SBML, the established exchange format for biochemical models, is structured biology-first: compartments with sizes, species with initial amounts or concentrations, `hasOnlySubstanceUnits`, boundary conditions, and reactions between species in compartments. The equations a simulator integrates are not in the file; they follow from these concepts. To simulate an SBML model, every implementation has to rewrite the equations itself, e.g. converting between amounts and concentrations and inserting compartment volumes into rates and stoichiometries. That rewrite is easy to get subtly wrong, and every simulator repeats it.

The biology-first structure buys something real: routines that work on the abstractions, such as moving a species to another compartment or resizing a compartment, are easy, provided the software implements them.

## 2. Decision

An `.mxl.json` file stores the mathematical model itself: exactly the equations the integrator steps, with every factor explicit.

- A kinetic model is dx/dt = N·v: rates as expressions, stoichiometric coefficients as expressions.
- An ODE model is a per-variable dx/dt expression.
- A steady-state model is a set of algebraic outputs of its parameters.

There are no compartments, species or amount/concentration semantics. A volume is a parameter, and appears wherever the equations need it, e.g. in a stoichiometry `V_stroma / V_lumen`. Biological structure that should be kept, such as compartment membership, belongs in annotations, which never affect the mathematics ([ADR 0009](0009-scope-what-is-left-out.md)).

## 3. Rationale

**The main job of a model file is to be simulated.** With the mathematics as the core, parsing and executing a model is direct: read the expressions, compile them, integrate. There is no rewrite step that every implementation must get right independently.

**There is more than one valid biological abstraction.** The same equations can be read with different compartmentalisations, lumped species or conventions. A biology-first format fixes one abstraction in the file's structure; a math-first format leaves it to each tool to decide how it presents and edits the biology, and several tools may choose differently.

**Importers do the rewrite once.** Converting from SBML means doing the biology-to-mathematics rewrite once, at import. Afterwards every consumer reads the same explicit equations.

## 4. Consequences

- An SBML round trip keeps the numbers but loses biological structure: exporting writes the explicit equations into a single trivial compartment.
- Biology-level edits (move a species, change a compartment volume consistently everywhere) are not operations on the file; they are left to tools that keep their own abstraction, or to the person editing the expressions.
- Every other decision in these ADRs is measured against this one: anything that is not mathematics (units, presentation, annotations) is optional and never changes a result.
