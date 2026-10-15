"""Tests of the standard run's scoring (toqb.score_loop_preg)."""
import itertools

from toqb.score_loop_preg import differences, score, sign_flip_p


def _brute(d):
    obs = sum(d)
    pats = list(itertools.product([1, -1], repeat=len(d)))
    return sum(1 for s in pats if sum(a * b for a, b in zip(s, d)) >= obs - 1e-12) / len(pats)


def test_sign_flip_matches_brute_force():
    for d in ([0.2, 0.1, -0.05, 0.3], [0.0, 0.0, 0.1], [-0.1, -0.2, 0.05, 0.0, 0.3, 0.02], [0.5]):
        assert abs(sign_flip_p(d) - _brute(d)) < 1e-12


def test_sign_flip_all_positive():
    assert abs(sign_flip_p([0.1] * 10) - 1 / 1024) < 1e-15


def _row(seed, p, q, valid_p=True, valid_q=True):
    r = dict(seed=seed, psf_valid=valid_p, qk_valid=valid_q, psf_complete=valid_p, qk_complete=valid_q,
             psf_batch_usd=226.5, qk_batch_usd=232.3)
    for key in ("accuracy", "margin", "noiseless_accuracy"):
        r[f"psf_{key}"] = p if valid_p else None
        r[f"qk_{key}"] = q if valid_q else None
    return r


def test_failed_arms():
    rows = [_row(1, 0.7, 0.5), _row(2, None, 0.5, valid_p=False), _row(3, 0.7, None, valid_q=False)]
    ds, used, out = differences(rows, "accuracy")
    assert used == [1, 2] and out == [3]
    assert abs(ds[0] - 0.2) < 1e-12 and abs(ds[1] + 1.0) < 1e-12  # a failed PSF-Zero arm counts as the worst


def test_verdicts():
    rows = [_row(s, 0.7, 0.5) for s in range(10)]
    res = score(rows)
    assert res["L1"]["verdict"] == "CONFIRMED"
    assert res["L2"]["verdict"] == "CONFIRMED" and res["L2"]["p"] < 0.01
    assert res["L5"]["verdict"] == "CONFIRMED" and res["L6"]["verdict"] == "CONFIRMED"
    rows = [_row(s, 0.5, 0.5) for s in range(10)]
    res = score(rows)
    assert res["L2"]["verdict"] == "REFUTED" and res["L5"]["verdict"] == "REFUTED"
