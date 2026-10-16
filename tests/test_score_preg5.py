"""Tests of toqb/score_loop_preg5.py on synthetic records."""
import json
import os

from toqb import score_loop_preg5 as S


def _rec(accs, usd_per_it=3.8):
    evals = [dict(iteration=it, accuracy=a, batch_usd=it * usd_per_it, noiseless_accuracy=a)
             for it, a in zip(range(0, 1001, 50), accs)]
    return dict(valid=True, evals=evals, version="v", engine="fast")


def _write(root, seed, psf, qk):
    d = os.path.join(root, f"seed{seed}")
    os.makedirs(d)
    json.dump(psf, open(os.path.join(d, "arm-psfai_template.json"), "w"))
    json.dump(qk, open(os.path.join(d, "arm-qiskit_2_target_template.json"), "w"))


def test_reach_and_censor():
    accs = [0.3] * 5 + [0.66] * 16  # reaches 0.65 at iteration 250, never 0.70
    it, usd, got = S.reach(_rec(accs), 0.65)
    assert (it, got) == (250, True) and abs(usd - 250 * 3.8) < 1e-9
    it, usd, got = S.reach(_rec(accs), 0.70)
    assert (it, got) == (S.CENSOR, False) and abs(usd - 1050 * 3.8) < 1e-9


def test_iteration_zero_does_not_count():
    accs = [0.9] + [0.3] * 20
    assert S.reach(_rec(accs), 0.65)[2] is False


def test_score_direction(tmp_path):
    root = str(tmp_path)
    for k, s in enumerate(range(1, 31)):
        fast = [0.3] * 3 + [0.71] * 18   # 0.65 and 0.70 at 150
        slow = [0.3] * 6 + [0.71] * 15   # at 300
        _write(root, s, _rec(fast, 3.7), _rec(slow, 3.8))
    rows = S.collect(root, range(1, 31))
    res = S.score(rows)
    assert res["R1"]["verdict"] == "CONFIRMED"
    assert res["R2"]["verdict"] == "CONFIRMED" and res["R2"]["mean_difference"] == 150
    assert res["R3"]["verdict"] == "CONFIRMED"
    assert res["R4"]["verdict"] == "CONFIRMED"
    assert "R2" in S.report(rows, res, list(range(1, 31)))


def test_missing_evaluation_is_invalid(tmp_path):
    root = str(tmp_path)
    r = _rec([0.5] * 21)
    r["evals"] = r["evals"][:-1]
    _write(root, 1, r, _rec([0.5] * 21))
    rows = S.collect(root, [1])
    assert S.score(rows)["R1"]["verdict"] == "REFUTED"
