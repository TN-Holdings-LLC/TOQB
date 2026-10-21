"""toqb.s2re4v (W13): select on quarters 1-2, check on quarters 3-4. Numpy only; no quantum package."""
import math

import numpy as np

from toqb import s2re as E
from toqb import s2re4v as V

M = 64


def _truth(rng):
    """Noiseless sinusoids a + b cos u + c sin u of M training outputs, kept inside [-1, 1]; labels in {+1, -1}."""
    amp = rng.uniform(0.05, 0.3, M)
    ph = rng.uniform(-math.pi, math.pi, M)
    a = rng.uniform(-0.3, 0.3, M)
    y = np.where(rng.random(M) < 0.5, 1.0, -1.0)
    return a, amp * np.cos(ph), amp * np.sin(ph), y


def _quarter(t, rng, sd):
    a, b, c = t
    return a + rng.normal(0, sd, M), b + rng.normal(0, sd, M), c + rng.normal(0, sd, M)


def test_delta_val_matches_trig2_min():
    rng = np.random.default_rng(1)
    a, b, c, y = _truth(rng)
    C = E.brier_coeffs(a, b, c, y)[1:]
    u, dv = E.trig2_min(*C)
    assert abs(V.delta_val(C, u) - dv) < 1e-12
    assert V.delta_val(C, 0.0) == 0.0
    # the change equals the Brier sum's change computed point by point
    f = lambda w: np.sum((a + b * math.cos(w) + c * math.sin(w) - y) ** 2)
    assert abs(V.delta_val(C, 0.7) - (f(0.7) - f(0.0))) < 1e-9


def test_noiseless_quarters_take_e4s_step():
    rng = np.random.default_rng(2)
    a, b, c, y = _truth(rng)
    hs = [(a, b, c)] * 4
    u, ver, sel, ok = V.select_verify(hs, y)
    u4, d4 = E.trig2_min(*E.brier_coeffs(a, b, c, y)[1:])
    assert ok and abs(u - u4) < 1e-9
    assert abs(ver - d4) < 1e-9 and abs(sel - d4) < 1e-9


def test_step_rejected_when_the_check_says_worse():
    rng = np.random.default_rng(3)
    a, b, c, y = _truth(rng)
    good = (a, b, c)
    # with quarter 4 = (2y - a, -b, -c), every product of the check pair changes sign: C_B = -C_A, so the check sees
    # exactly the opposite curve and u_A (C_A's minimum, a strict improvement there) raises C_B's loss
    flip = (2 * y - a, -b, -c)
    CA = E.brier_coeffs_split(good, good, y)
    CB = E.brier_coeffs_split(good, flip, y)
    assert np.allclose(CB, [-v for v in CA])
    u, ver, sel, ok = V.select_verify([good, good, good, flip], y)
    assert not ok and u == 0.0 and ver == 0.0 and sel == 0.0


def test_no_move_when_curve_is_flat():
    y = np.ones(M)
    z = np.zeros(M)
    assert V.select_verify([(z, z, z)] * 4, y) == (0.0, 0.0, 0.0, False)


def test_check_is_unbiased_and_selection_is_not():
    """Given u_A, the check v is unbiased for the true change at u_A; the selecting curve's own value is optimistic."""
    rng = np.random.default_rng(4)
    a, b, c, y = _truth(rng)
    t = (a, b, c)
    Ctrue = E.brier_coeffs(a, b, c, y)[1:]
    gap_v, gap_s = [], []
    for _ in range(3000):
        hs = [_quarter(t, rng, 0.25) for _ in range(4)]
        CA = E.brier_coeffs_split(hs[0], hs[1], y)
        CB = E.brier_coeffs_split(hs[2], hs[3], y)
        u, sel = E.trig2_min(*CA)
        if u == 0.0:
            continue
        true = V.delta_val(Ctrue, u)
        gap_v.append(V.delta_val(CB, u) - true)
        gap_s.append(sel - true)
    gv, gs = np.array(gap_v), np.array(gap_s)
    se_v = gv.std(ddof=1) / math.sqrt(len(gv))
    assert abs(gv.mean()) < 4 * se_v, (gv.mean(), se_v)
    assert gs.mean() < -4 * gs.std(ddof=1) / math.sqrt(len(gs)), gs.mean()


def test_quarter_seeds_never_repeat():
    d = 330
    seen = {V.quarter_seed(7 * 1000003, sw, d, k, q) for sw in range(3) for k in range(d) for q in range(4)}
    assert len(seen) == 3 * d * 4
    try:
        V.quarter_seed(0, 0, d, 0, 4)
    except ValueError:
        pass
    else:
        raise AssertionError("quarter 4 accepted")


def test_wrong_number_of_quarters():
    rng = np.random.default_rng(5)
    a, b, c, y = _truth(rng)
    try:
        V.select_verify([(a, b, c)] * 2, y)
    except ValueError:
        pass
    else:
        raise AssertionError("two estimates accepted")
