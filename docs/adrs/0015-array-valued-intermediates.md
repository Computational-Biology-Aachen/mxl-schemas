# ADR 0015: Array-Valued Intermediates

**Status:** Accepted (not yet implemented)
**Scope:** derived quantities in the model schemas; `spec_version` 1.3; consumer-side validation and codegen
**Amends:** [ADR 0014](0014-array-nodes-and-model-data.md) §2 (an array subtree in a model may reference only data and numbers)

---

## 1. Context

ADR 0014 lets data reach a model only through constants. Every array subtree references nothing but data and numbers, and it is folded to a number before any backend sees the model. It left state-dependent arrays out "until a model needs it".

A model now needs it. Spectral light models attenuate each wavelength by the cell's current pigment content and then integrate over wavelength. Per wavelength λ and depth z:

- k(λ) = chl · Σ_p a_p(λ) · c_p, where the pigment contents c_p are states,
- I(λ, z) = I0(λ) · e^(−k(λ) z),
- absorbed light = Simpson over λ of a_p(λ) · I(λ, z).

Under ADR 0014 this can only be written as unrolled scalar sums: one derived quantity per wavelength and depth node, e.g. 61 wavelengths × 5 depth nodes on a 5 nm grid. The spectra end up as literals in the model file. The file becomes large and unreadable, and the browser compile time grows with it.

## 2. Decision

**Derived quantities may be arrays. The right-hand side stays scalar.** A derived quantity whose expression evaluates to a 1-D array is an array-valued intermediate. Its subtree may reference anything: data, numbers, parameters, variables, time and other derived quantities, scalar or array. The following must be scalar, and an array reaching any of them is an error:

- variables, parameters and initial values,
- reaction rates and stoichiometries,
- right-hand sides and readouts.

**Shapes.**

- Arrays are 1-D.
- A length is fixed when the model is loaded. It comes from data, never from state or parameters.
- Shapes are inferred, not declared: every array traces back to data.
- The broadcasting rules of ADR 0014 apply unchanged.
- Consumers reject a model whose arrays have unequal lengths where they combine.

**Operands that must be constants.** The following operands may reference only data and numbers, which keeps lengths static and the nodes cheap to compile:

| Node | Constant operands |
| --- | --- |
| `Simpson` | `x` (the weights are computed once per data set) |
| `Index` | `i` |
| `Slice` | `start`, `stop` |
| `At` | `t`, `times` |

The array operands (`y`, `a`) may depend on state. Analyses are evaluated, not compiled, so the restriction applies to models only.

**Data are runtime values.**

- Consumers pass data to compiled code as buffers instead of baking them in as literals. Replacing data values with the same lengths needs no recompilation.
- Different lengths are a structural change.
- Folding an array subtree that references only data and numbers is still allowed, as an optimisation.
- Data are still not parameters (ADR 0014).

**Derivatives stay symbolic.** Element-wise nodes differentiate element-wise. `Sum`, `Mean` and `Simpson` are linear in their array operand, and `Index`, `Slice`, `At` and `MaxOf`/`MinOf` (at the argmax/argmin) select. So the derivative of an array expression with respect to a scalar is an array expression built from the same nodes. Jacobians and gradients therefore stay exact, and consumers do not fall back to finite differences.

**Results stay scalar.** Array-valued derived quantities are internal. They are not result columns, plot choices or scan outputs. Their scalar reductions are ordinary derived quantities.

**SBML export unrolls.** SBML core has no arrays, so an exporter writes one assignment rule per element and each reduction as an explicit sum with literal weights. This goes one way only: importing SBML never recovers arrays.

**Version.**

- A model whose array subtree references a parameter, a variable, time or a derived quantity has `spec_version` 1.3.
- A model that uses data only through constants stays valid 1.2.
- The schema adds no nodes and no shape fields. The rules above are consumer-side validation, as the type rules for nn blocks are.

## 3. Rationale

**The right-hand side is where the solvers live.** Keeping it scalar leaves the solver interfaces untouched: the C solvers (mxl-solvers), the Jacobian layout, steady-state and MCA code. Only the code that computes the right-hand side learns to loop.

**1-D with static lengths keeps codegen small.** Every backend allocates one buffer per array quantity once and fills it with a loop of literal bounds. The right-hand side never allocates. 2-D (e.g. depth × wavelength) would need axis-aware reductions and a matrix layout. Depth is a handful of copies and stays unrolled. 2-D can be added later without breaking 1-D.

**Named arrays, because they are reused.** One attenuated spectrum feeds several integrals (one per pigment, plus quenching). With anonymous subtrees only, each would be recomputed, unless every backend eliminated common subexpressions across trees.

**The node set is closed under differentiation.** No new node is needed for Jacobians or adjoints. That is what makes exact derivatives cheap in both the sympy-based and the tree-based consumers.

**Inferred shapes.** Every length already comes from data. A declared shape would repeat it and could contradict it.

## 4. Consequences

- **Consumers that compile models need array lowering.** In practice:
  - every named array derived quantity becomes a buffer filled by one loop;
  - an anonymous element-wise subtree inside a reduction is fused into the reduction's loop, with no temporary buffer;
  - `Simpson` becomes a dot product with precomputed weights;
  - there is no common-subexpression elimination across loops (name a quantity to reuse it).
  
  Each emitter (WAT, LLVM IR, JS) only needs a counted loop and indexed loads and stores. Numpy code stays vectorised and is the reference behaviour.
- **Derivative code changes.** Symbolic differentiation (MxlPy's sympy `Array*` functions) and reverse mode (mxlweb-core's gradients) learn array-valued adjoints. A reduction spreads its scalar adjoint back over the array, and element-wise nodes multiply element-wise.
- **Exports get bigger.** SBML exports of such models are large, as the hand-unrolled models already are.
- **Old consumers reject new files.** Consumers that only know 1.2 reject 1.3 files (ADR 0011) instead of misreading them.
- **Tests are needed at three levels:**
  - cross-language fixtures for a small array model (states and parameters → right-hand side and Jacobian);
  - each backend against numpy;
  - symbolic derivatives against finite differences.
  
  The change must not slow down existing scalar models noticeably.
