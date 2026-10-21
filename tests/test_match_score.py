"""toqb.match_score on synthetic run records shaped like the samples (s2re4 for Z and E4, s2rc for C0). Numpy and
scipy only; no quantum package."""
import json
import os
import tempfile

import numpy as np

from toqb import match_score as M

P = 300


def _labels():
    return np.where(np.arange(P) % 2 == 0, 1, -1)


def _p1_with_margin(y, margin, rng, spread=0.05):
    """P(1) on the label's side by `margin` on average (P(1) < 0.5 for y = +1), with per-point spread."""
    m = np.clip(margin + rng.normal(0, spread, len(y)), -0.45, 0.45)
    return np.where(y > 0, 0.5 - m, 0.5 + m)


def _rec(role, teacher, L, p1, y, cost=None):
    task = {"n": 10, "layers": L, "enc": 1.5707963267948966, "teacher_seed": teacher, "teacher_angle": 1.0,
            "teacher_gap": 0.2, "n_train": 64, "n_test": len(y)}
    reh = {"ce": 0.6, "acc": 0.6, "ce_inside": True, "acc_inside": True, "twin_vs_standin_p1_rmse": 0.01,
           "standin_p1": [float(v) for v in p1]}
    pred = {"ce_mean": 0.6, "twin_p1": [float(v) for v in p1]}
    base = dict(arm="psfai:template", task=task, valid=True, test_labels=[int(v) for v in y], rehearsal=reh,
                prediction=pred, train_wall_s=1.0)
    if role == "C0":
        base.update(kind="s2rc", loops=2000, train={"seed": 201, "init": 0.0, "pairs": 8, "sim_batch": 4,
                                                    "sim_traj": 32, "lr": 0.4, "loops": 2000})
    else:
        sweeps = 0 if role == "Z" else 3
        base.update(kind="s2re4", sweeps=sweeps, loops=0, train={"seed": teacher, "sweeps": sweeps},
                    train_traj_circuits=0 if role == "Z" else (cost if cost is not None else 4_000_000))
    return base


def _write_runs(d, margins, teachers=(4, 5, 6), layers=(8, 16), seed=1, e4_cost=None):
    rng = np.random.default_rng(seed)
    y = _labels()
    os.makedirs(d, exist_ok=True)
    for t in teachers:
        for L in layers:
            cache = {}  # arms with the same margin in a task get identical P(1): an exact tie, not a random one
            for role, mg in margins(t, L).items():
                if mg not in cache:
                    cache[mg] = _p1_with_margin(y, mg, rng)
                rec = _rec(role, t, L, cache[mg], y, cost=e4_cost)
                with open(os.path.join(d, f"{role}_L{L}_t{t}.json"), "w", encoding="utf-8") as f:
                    json.dump(rec, f)


def test_clear_e4_win_gives_headline():
    with tempfile.TemporaryDirectory() as d:
        _write_runs(d, lambda t, L: {"Z": 0.02, "C0": 0.05, "E4": 0.12})
        res = M.score_match(M.load_runs(d))
    assert res["headline"]["won_from_lane_1"] is True
    assert res["comparisons"]["E4 vs C0"]["fresh"]["overall"]["verdict"] == "WIN"
    assert res["checks"]["fresh_tasks"] == 4  # teacher 4 at angle 1.0 is a development task by default


def test_equal_arms_are_a_tie():
    with tempfile.TemporaryDirectory() as d:
        _write_runs(d, lambda t, L: {"Z": 0.05, "C0": 0.05, "E4": 0.05})
        res = M.score_match(M.load_runs(d))
    assert res["headline"]["won_from_lane_1"] is False
    for name in ("E4 vs C0", "E4 vs Z", "C0 vs Z"):
        assert res["comparisons"][name]["all"]["overall"]["verdict"] == "TIE", name


def test_e4_loss_is_reported_as_loss():
    with tempfile.TemporaryDirectory() as d:
        _write_runs(d, lambda t, L: {"Z": 0.02, "C0": 0.12, "E4": 0.05})
        res = M.score_match(M.load_runs(d))
    assert res["comparisons"]["E4 vs C0"]["all"]["overall"]["verdict"] == "LOSS"
    assert res["headline"]["won_from_lane_1"] is False


def test_win_only_on_the_development_task_does_not_count():
    def margins(t, L):
        return {"Z": 0.02, "C0": 0.05, "E4": 0.12 if t == 4 else 0.05}
    with tempfile.TemporaryDirectory() as d:
        _write_runs(d, margins)
        res = M.score_match(M.load_runs(d))
    assert res["headline"]["won_from_lane_1"] is False
    assert res["comparisons"]["E4 vs C0"]["fresh"]["overall"]["verdict"] == "TIE"


def test_mixed_when_tasks_disagree():
    def margins(t, L):
        return {"Z": 0.0, "C0": 0.08, "E4": 0.14 if L == 8 else 0.02}
    with tempfile.TemporaryDirectory() as d:
        _write_runs(d, margins)
        res = M.score_match(M.load_runs(d))
    assert res["comparisons"]["E4 vs C0"]["all"]["overall"]["verdict"] == "MIXED"


def test_budget_overrun_is_flagged():
    with tempfile.TemporaryDirectory() as d:
        _write_runs(d, lambda t, L: {"Z": 0.02, "C0": 0.05, "E4": 0.12}, e4_cost=5_000_000)
        res = M.score_match(M.load_runs(d))
    assert res["checks"]["e4_within_budget_all"] is False


def test_different_labels_stop():
    with tempfile.TemporaryDirectory() as d:
        _write_runs(d, lambda t, L: {"Z": 0.02, "C0": 0.05, "E4": 0.12}, teachers=(5,), layers=(8,))
        f = os.path.join(d, "E4_L8_t5.json")
        rec = json.load(open(f, encoding="utf-8"))
        rec["test_labels"][0] = -rec["test_labels"][0]
        json.dump(rec, open(f, "w", encoding="utf-8"))
        try:
            M.load_runs(d)
        except M.Stop as exc:
            assert "different test labels" in str(exc)
        else:
            raise AssertionError("arms on different labels were accepted")


def test_cli_writes_once():
    with tempfile.TemporaryDirectory() as d:
        runs = os.path.join(d, "runs")
        _write_runs(runs, lambda t, L: {"Z": 0.02, "C0": 0.05, "E4": 0.12})
        out = os.path.join(d, "score.md")
        assert M.main([runs, out, "--json", os.path.join(d, "score.json")]) == 0
        text = open(out, encoding="utf-8").read()
        assert "Won from lane 1: **YES**" in text
        assert M.main([runs, out]) == 2


def test_signed_rank_z_matches_scipy():
    from scipy.stats import wilcoxon
    rng = np.random.default_rng(3)
    d = rng.normal(0.01, 0.1, 400)
    z, p = M.signed_rank_z(d)
    ref = wilcoxon(d, zero_method="wilcox", correction=False, method="approx").pvalue
    assert abs(p - ref) < 1e-6, (p, ref)
