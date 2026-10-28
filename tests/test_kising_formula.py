"""toqb.kising_formula (2026-10-28): p fitted at the reference n is recovered, and the prediction at another n agrees
when the 'device' follows the formula itself."""
import numpy as np

from toqb import kising as K
from toqb import kising_formula as F


def cell(n, L, h, p, P=16, seed=0, se=0.01):
    rng = np.random.default_rng(seed + n)
    ins = [rng.choice([1, -1], n) for _ in range(P)]
    zl = [K.z_noiseless(s, n, L, h) for s in ins]
    lam = F.lam_formula(ins, zl, n, L, h, p)
    return dict(n=n, L=L, h=h, inputs=[[int(v) for v in s] for s in ins], noiseless_z=zl, lam=lam, se=se)


def test_recovers_p_and_agrees():
    h, L, p = 0.6, 6, 0.01
    cells = [cell(8, L, h, p), cell(10, L, h, p), cell(12, L, h, p)]
    res = F.predict(cells, ref_n=8)
    assert abs(res["ref"]["p"] - p) < 1e-5
    assert all(c["verdict"] == "AGREE" and abs(c["diff"]) < 1e-4 for c in res["cells"])


def test_detects_a_different_rate():
    h, L = 0.6, 6
    cells = [cell(8, L, h, 0.01), cell(10, L, h, 0.03, se=0.001)]
    res = F.predict(cells, ref_n=8)
    assert res["cells"][0]["verdict"] == "BELOW"
