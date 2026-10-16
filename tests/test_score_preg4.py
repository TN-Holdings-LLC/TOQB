"""Tests of the budget run's scoring (toqb.score_loop_preg4)."""
from toqb.score_loop_preg4 import score


def _row(s, p, q, it_p=50, it_q=49, ok=True):
    r = dict(seed=s, psf_ok=ok, qk_ok=True, psf_iterations=it_p, qk_iterations=it_q)
    for k in ("accuracy", "margin", "noiseless_accuracy"):
        r[f"psf_{k}"], r[f"qk_{k}"] = (p if ok else None), q
    return r


def test_verdicts():
    res = score([_row(s, 0.6, 0.5) for s in range(30)])
    assert res["B1"]["verdict"] == "CONFIRMED" and res["B2"]["verdict"] == "CONFIRMED"
    assert res["B5"]["verdict"] == "CONFIRMED"
    res = score([_row(s, 0.5, 0.5) for s in range(30)])
    assert res["B2"]["verdict"] == "REFUTED"


def test_failed_and_fewer():
    res = score([_row(1, 0.6, 0.5, ok=False), _row(2, 0.6, 0.5, it_p=48)])
    assert res["B1"]["verdict"] == "REFUTED" and res["B5"]["verdict"] == "REFUTED"
    assert res["B2"]["mean_difference"] < 0  # the failed PSF-Zero arm counts at its worst
