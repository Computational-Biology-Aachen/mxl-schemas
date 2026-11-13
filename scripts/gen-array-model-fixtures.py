# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "scipy", "sympy"]
# ///
"""Generate tests/array-models.fixtures.json (ADR 0015).

The reference values are computed from an element-by-element sympy expansion of
the model (independent of any consumer's array code), with Simpson weights from
scipy and the Jacobians differentiated exactly. Run: uv run scripts/gen-array-model-fixtures.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import scipy.integrate
import sympy as sp

OUT = Path(__file__).resolve().parents[1] / "tests" / "array-models.fixtures.json"


def N(name: str) -> dict:
    return {"type": "Name", "value": name}


def num(v: float) -> dict:
    return {"type": "Num", "value": v}


def op(t: str, *children: dict) -> dict:
    return {"type": t, "children": list(children)}


def exp(x: dict) -> dict:
    return {"type": "Exp", "child": x}


DATA = {
    "wavelength": [400.0, 425.0, 450.0, 500.0, 550.0, 600.0, 700.0],
    "a1": [0.9, 1.2, 0.7, 0.3, 0.2, 0.5, 0.8],
    "a2": [0.1, 0.2, 0.4, 0.9, 1.1, 0.6, 0.2],
    "I0": [50.0, 80.0, 120.0, 150.0, 140.0, 110.0, 60.0],
}
PARAMETERS = {"chl": 0.8, "z": 0.5, "kp": 0.3, "kd": 0.1, "ks": 0.05}
VARIABLES = {"c1": 0.6, "c2": 0.4, "S": 2.0}

DERIVED = {
    # arrays: state-dependent attenuation and local light per wavelength
    "k_att": op("Mul", N("chl"), op("Add", op("Mul", N("a1"), N("c1")), op("Mul", N("a2"), N("c2")))),
    "I_loc": op("Mul", N("I0"), exp(op("Minus", op("Mul", N("k_att"), N("z"))))),
    # scalars: reductions of the arrays
    "abs1": op("Simpson", op("Mul", N("a1"), N("I_loc")), N("wavelength")),
    "abs2": op("Simpson", op("Mul", N("a2"), N("I_loc")), N("wavelength")),
    "peak": op("MaxOf", N("I_loc")),
    "spread": op(
        "Add",
        op("Std", N("I_loc")),
        op("Mean", N("k_att")),
        op("Index", N("I_loc"), num(-1)),
        op("Sum", op("Slice", N("k_att"), num(1), num(4))),
        op("MinOf", N("k_att")),
        op("At", N("I_loc"), num(520), N("wavelength")),
    ),
}
REACTIONS = {
    "v1": (op("Mul", N("kp"), N("abs1"), op("Minus", num(1), N("c1"))), {"c1": 1}),
    "v2": (op("Mul", N("kp"), N("abs2"), op("Minus", num(1), N("c2"))), {"c2": 1}),
    "v_deg": (op("Mul", N("kd"), N("c1"), N("c2")), {"c1": -1, "c2": -1}),
    "v_S": (op("Divide", op("Mul", N("ks"), N("S"), N("peak")), op("Add", num(1), N("spread"))), {"S": -1}),
}


def document(derived: dict, reactions: dict, *, variables=None, parameters=None, readouts=None, spec="1.3") -> dict:
    return {
        "spec_version": spec,
        "kind": "kinetic",
        "model_id": "array_intermediates",
        "data_ref": "model.data.json",
        "model": {
            "variables": {k: {"value": num(v)} for k, v in (variables or VARIABLES).items()},
            "parameters": {k: {"value": num(v)} for k, v in (parameters or PARAMETERS).items()},
            "reactions": {
                k: {"fn": fn, "stoichiometry": {v: num(s) for v, s in st.items()}}
                for k, (fn, st) in reactions.items()
            },
            "derived": {k: {"fn": fn} for k, fn in derived.items()},
            "readouts": readouts or {},
        },
    }


# ---- reference: element-by-element sympy expansion -------------------------

ys = {k: sp.Symbol(k) for k in VARIABLES}
ps = {k: sp.Symbol(k) for k in PARAMETERS}
n = len(DATA["wavelength"])
wl = np.array(DATA["wavelength"])
w = np.array([scipy.integrate.simpson(np.eye(n)[i], x=wl) for i in range(n)])
d = {k: [sp.Float(x, 30) for x in v] for k, v in DATA.items()}

k_att = [ps["chl"] * (d["a1"][i] * ys["c1"] + d["a2"][i] * ys["c2"]) for i in range(n)]
I_loc = [d["I0"][i] * sp.exp(-k_att[i] * ps["z"]) for i in range(n)]
mean_I = sum(I_loc) / n
at = int(np.argmin(np.abs(wl - 520)))
scalars = {
    "abs1": sum(sp.Float(w[i], 30) * d["a1"][i] * I_loc[i] for i in range(n)),
    "abs2": sum(sp.Float(w[i], 30) * d["a2"][i] * I_loc[i] for i in range(n)),
    "peak": sp.Max(*I_loc),
    "spread": sp.sqrt(sum((x - mean_I) ** 2 for x in I_loc) / (n - 1))
    + sum(k_att) / n
    + I_loc[-1]
    + sum(k_att[1:4])
    + sp.Min(*k_att)
    + I_loc[at],
}
rates = {
    "v1": ps["kp"] * scalars["abs1"] * (1 - ys["c1"]),
    "v2": ps["kp"] * scalars["abs2"] * (1 - ys["c2"]),
    "v_deg": ps["kd"] * ys["c1"] * ys["c2"],
    "v_S": ps["ks"] * ys["S"] * scalars["peak"] / (1 + scalars["spread"]),
}
rhs = {
    "c1": rates["v1"] - rates["v_deg"],
    "c2": rates["v2"] - rates["v_deg"],
    "S": -rates["v_S"],
}


def value(expr: sp.Expr, subs: dict) -> float:
    return float(sp.N(expr.subs(subs), 30))


def point(variables: dict) -> dict:
    subs = {ys[k]: v for k, v in variables.items()} | {ps[k]: v for k, v in PARAMETERS.items()}
    return {
        "variables": variables,
        "derived": {k: value(e, subs) for k, e in scalars.items()},
        "rhs": {k: value(e, subs) for k, e in rhs.items()},
        "dfdy": {k: {v: value(sp.diff(e, ys[v]), subs) for v in ys} for k, e in rhs.items()},
        "dfdp": {k: {p: value(sp.diff(e, ps[p]), subs) for p in ps} for k, e in rhs.items()},
    }


# ---- models every consumer must reject --------------------------------------


def broken(description: str, **kw) -> dict:
    derived = DERIVED | kw.pop("derived", {})
    reactions = REACTIONS | kw.pop("reactions", {})
    data = kw.pop("data", DATA)
    return {"description": description, "model": document(derived, reactions, **kw), "data": data}


ERRORS = [
    broken("a reaction rate is an array", reactions={"v_bad": (op("Mul", N("kp"), N("I_loc")), {"S": 1})}),
    broken("a stoichiometry is an array", reactions={"v_bad": (N("kp"), {})}),
    broken("a readout is an array", readouts={"spectrum": {"fn": N("I_loc")}}),
    broken("Simpson's x depends on a variable", derived={"abs1": op("Simpson", N("I_loc"), op("Mul", N("wavelength"), N("c1")))}),
    broken("Index's index is a parameter", derived={"peak": op("Index", N("I_loc"), N("kp"))}),
    broken("Slice's bounds depend on a variable", derived={"peak": op("Sum", op("Slice", N("I_loc"), num(0), N("S")))}),
    broken("At's t depends on a variable", derived={"peak": op("At", N("I_loc"), N("S"), N("wavelength"))}),
    broken(
        "arrays of unequal length combine",
        derived={"k_att": op("Add", N("a1"), N("short"))},
        data=DATA | {"short": [1.0, 2.0, 3.0]},
    ),
]
# the helper above takes numeric stoichiometries, so the array one is patched in
ERRORS[1]["model"]["model"]["reactions"]["v_bad"]["stoichiometry"] = {"S": N("I_loc")}


def main() -> None:
    fixtures = {
        "$comment": (
            "Array-valued intermediates (ADR 0015). `model` is a kinetic .mxl.json document and "
            "`data` its sidecar. For each point (variables, with the model's parameter values) a "
            "consumer must reproduce the scalar derived quantities, the right-hand side `rhs`, "
            "and its exact Jacobians `dfdy` (rhs by variable) and `dfdp` (rhs by parameter), "
            "rhs[name][wrt], within a relative tolerance of 1e-10. Every model in `errors` must "
            "be rejected when loaded or compiled. Generated by scripts/gen-array-model-fixtures.py."
        ),
        "model": document(DERIVED, REACTIONS),
        "data": {k: {"values": v} for k, v in DATA.items()},
        "points": [point(VARIABLES), point({"c1": 0.15, "c2": 0.85, "S": 0.7})],
        "errors": [
            {"description": e["description"], "model": e["model"], "data": {k: {"values": v} for k, v in e["data"].items()}}
            for e in ERRORS
        ],
    }
    OUT.write_text(json.dumps(fixtures, indent=2) + "\n")


if __name__ == "__main__":
    main()
