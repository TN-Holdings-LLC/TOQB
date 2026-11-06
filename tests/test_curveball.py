"""Task Y: the curveball grid and its selection rules (synthetic values only; no answer of the grid is used)."""
import numpy as np

from daily import curveball as CB
from daily import pool as P


def test_grid_is_fixed_and_known_to_entry():
    assert len(P.CURVE) == 78
    assert {g for g in P.CURVE_GROUP.values()} == {"Y-F1", "Y-F2", "Y-F4s", "Y-F4m"}
    for e in P.CURVE:
        assert P.entry(e[0]) == e


def test_f4_kick_follows_the_row_formula():
    qs, es = P.patch("P32")
    qc = P.f4(1, 0.3, 0.5, 1.0, qs, es)
    top = min(q // 20 for q in qs)
    rx = {qc.find_bit(i.qubits[0]).index: float(i.operation.params[0]) for i in qc.data if i.operation.name == "rx"}
    assert all(abs(rx[q] - (0.3 + 0.5 * (q // 20 - top))) < 1e-12 for q in qs)


def _fake(values_by_group):
    ans = {}
    for e in P.CURVE:
        ans[e[0]] = {str(k): v for k, v in enumerate(values_by_group(e))}
    return ans


def test_rules_and_ties():
    def vals(e):
        pid, fam, pa, par, t = e[:5]
        g = P.CURVE_GROUP[pid]
        if g == "Y-F1":
            return [0.5] * 32 if par["theta_x"] in (0.9, 1.1) else [0.9] * 32  # a tie: the smaller angle wins
        if g == "Y-F2":
            return [0.2] * 72                                                  # nothing eligible
        if g == "Y-F4s":
            return list(np.linspace(-1, 1, 32) * par["delta"])                # the largest delta spreads most
        return list(np.linspace(-0.2, 1, 32) * par["theta0"])                 # negative share 1/6: never eligible
    r = CB.select(_fake(vals))
    ch = {(c["group"], c["t"]): c for c in r["chosen"]}
    assert ch[("Y-F1", 5)]["params"]["theta_x"] == 0.9 and ch[("Y-F1", 6)]["params"]["theta_x"] == 0.9
    assert ch[("Y-F2", 4)]["id"] is None and ch[("Y-F2", 5)]["id"] is None
    assert ch[("Y-F4s", 4)]["params"] == dict(theta0=0.3, delta=0.7, theta_zz=1.0)
    assert ch[("Y-F4m", 3)]["id"] is None
    g = ch[("Y-F1", 5)]["guesses"]
    assert abs(g["all_0"] - 0.25) < 1e-12 and abs(g["all_1"] - 0.25) < 1e-12 and g["all_M_exact"] < 1e-12
