"""Tests of the second standard run's scoring (toqb.score_loop_preg2)."""
import numpy as np

from toqb.score_loop_preg import sign_flip_p as exact
from toqb.score_loop_preg2 import score, sign_flip_p


def test_small_is_exact():
    d = [0.1, -0.05, 0.2, 0.0, 0.03]
    assert sign_flip_p(d) == exact(d)


def test_monte_carlo_close_to_normal():
    rng = np.random.default_rng(0)
    d = rng.normal(0.01, 0.1, 200)
    from math import erf, sqrt
    z = d.mean() / (np.sqrt((d ** 2).mean()) / sqrt(len(d)))  # sign-flip null: sd from the raw second moment
    p_norm = 0.5 * (1 - erf(z / sqrt(2)))
    assert abs(sign_flip_p(d) - p_norm) < 0.01


def _row(s, p, q, pe, qe):
    r = dict(seed=s, psf_ok=True, qk_ok=True, psf_batch_usd=1.0, qk_batch_usd=2.0)
    for k in ("accuracy", "margin", "noiseless_accuracy"):
        r[f"psf_{k}"], r[f"qk_{k}"] = p, q
        r[f"psf_{k}_early"], r[f"qk_{k}_early"] = pe, qe
    return r


def test_growth():
    rows = [_row(s, 0.75, 0.65, 0.60, 0.58) for s in range(30)]
    res = score(rows)
    assert res["M2"]["verdict"] == "CONFIRMED" and res["M5"]["verdict"] == "CONFIRMED"
    rows = [_row(s, 0.70, 0.65, 0.60, 0.50) for s in range(30)]
    assert score(rows)["M5"]["verdict"] == "REFUTED"
