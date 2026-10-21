"""toqb.match_score_fruit on synthetic run records shaped like the fruit match's (s2re4 for Z and E4 with sweep
checkpoints, s2rc from toqb.s2rc_ckpt for C0 with loop checkpoints). Numpy and scipy only; no quantum package."""
import json
import os
import tempfile

import numpy as np

from toqb import match_score_fruit as F

P = 300
SWEEP = 3 * 170 * 64 * 32      # 1,044,480 trajectory-circuits per E4 sweep at L 8
LOOP = 16 * 4 * 32             # 2,048 per C0 loop


def _labels():
    return np.where(np.arange(P) % 2 == 0, 1, -1)


def _p1(y, margin, rng, spread=0.05):
    m = np.clip(margin + rng.normal(0, spread, len(y)), -0.45, 0.45)
    return [float(v) for v in np.where(y > 0, 0.5 - m, 0.5 + m)]


def _rh(p1):
    return {"ce": 0.6, "acc": 0.6, "ce_inside": True, "standin_p1": p1}


def _task(t, a, L, n):
    return {"n": 10, "layers": L, "enc": 1.5707963267948966, "teacher_seed": t, "teacher_angle": a,
            "teacher_gap": 0.2, "n_train": 64, "n_test": n}


def _z(t, a, y, p1):
    return dict(kind="s2re4", arm="psfai:template", seed=t, sweeps=0, task=_task(t, a, 8, len(y)), valid=True,
                test_labels=[int(v) for v in y], rehearsal=_rh(p1), prediction={"twin_p1": p1}, train_traj_circuits=0)


def _e4(t, a, y, p1s, seed=None, cost_shift=0):
    ck = [dict(sweep=k + 1, train_traj_circuits=(k + 1) * SWEEP + cost_shift, rehearsal=_rh(p1s[k]),
               prediction={"twin_p1": p1s[k]}) for k in range(len(p1s) - 1)]
    return dict(kind="s2re4", arm="psfai:template", seed=t if seed is None else seed, sweeps=len(p1s),
                task=_task(t, a, 8, len(y)), valid=True, test_labels=[int(v) for v in y], checkpoints=ck,
                train_traj_circuits=len(p1s) * SWEEP, rehearsal=_rh(p1s[-1]), prediction={"twin_p1": p1s[-1]})


def _c0(t, a, y, p1s, seed=201):
    loops = (510, 1020, 1530)
    ck = [dict(loop=l, train_traj_circuits=l * LOOP, rehearsal=_rh(p1s[k]), prediction={"twin_p1": p1s[k]})
          for k, l in enumerate(loops)]
    return dict(kind="s2rc", runner="toqb.s2rc_ckpt", arm="psfai:template", seed=seed, loops=2000,
                train={"seed": seed, "init": 0.0}, task=_task(t, a, 8, len(y)), valid=True,
                test_labels=[int(v) for v in y], checkpoints=ck, train_traj_circuits=2000 * LOOP,
                rehearsal=_rh(p1s[3]), prediction={"twin_p1": p1s[3]})


def _write(d, name, rec):
    with open(os.path.join(d, name), "w", encoding="utf-8") as f:
        json.dump(rec, f)


def _match(d, margins, angles=(0.3, 1.0, 2.0), teachers=(7, 8, 9), seed=1, extra=None):
    """margins(angle) -> dict(Z=m, E4=[m1, m2, m3], C0=[m510, m1020, m1530, m2000])."""
    rng = np.random.default_rng(seed)
    y = _labels()
    os.makedirs(d, exist_ok=True)
    for a in angles:
        for t in teachers:
            m = margins(a)
            cache = {}

            def p(mg):
                if mg not in cache:
                    cache[mg] = _p1(y, mg, rng)
                return cache[mg]
            _write(d, f"Z_a{a}_t{t}.json", _z(t, a, y, p(m["Z"])))
            _write(d, f"E4_a{a}_t{t}.json", _e4(t, a, y, [p(v) for v in m["E4"]]))
            _write(d, f"C0_a{a}_t{t}.json", _c0(t, a, y, [p(v) for v in m["C0"]]))
    if extra:
        extra(d, y, rng)


GOOD = lambda a: {"Z": 0.0, "E4": [0.12, 0.13, 0.14], "C0": [0.03, 0.06, 0.09, 0.11]}


def test_early_win_in_every_group():
    with tempfile.TemporaryDirectory() as d:
        _match(d, GOOD)
        res = F.score_fruit(F.load_runs(d))
    assert all(h["won_in_fruit_zone"] for h in res["headline"]), res["headline"]
    assert len(res["headline"]) == 3


def test_strong_theta0_at_angle_0_3_is_reported_as_not_won():
    def margins(a):
        if a == 0.3:  # theta = 0 already strong; E4's first sweep below it
            return {"Z": 0.30, "E4": [0.12, 0.13, 0.14], "C0": [0.03, 0.06, 0.09, 0.11]}
        return GOOD(a)
    with tempfile.TemporaryDirectory() as d:
        _match(d, margins)
        res = F.score_fruit(F.load_runs(d))
    h = {(x["angle"], x["layers"]): x for x in res["headline"]}
    assert h[(0.3, 8)]["e4_vs_z"] == "LOSS" and not h[(0.3, 8)]["won_in_fruit_zone"]
    assert h[(1.0, 8)]["won_in_fruit_zone"] and h[(2.0, 8)]["won_in_fruit_zone"]


def test_equal_early_is_a_tie_and_peel_reported():
    eq = lambda a: {"Z": 0.0, "E4": [0.06, 0.08, 0.10], "C0": [0.06, 0.08, 0.10, 0.12]}
    with tempfile.TemporaryDirectory() as d:
        _match(d, eq)
        res = F.score_fruit(F.load_runs(d))
    assert all(h["e4_vs_c0"] == "TIE" for h in res["headline"])
    assert not any(h["won_in_fruit_zone"] for h in res["headline"])
    assert res["peel"]["pooled"]["verdict"] == "LOSS"  # C0's full budget beats E4's last sweep here


def test_cost_mismatch_stops():
    def extra(d, y, rng):
        os.remove(os.path.join(d, "E4_a1.0_t7.json"))
        _write(d, "E4_a1.0_t7.json", _e4(7, 1.0, y, [_p1(y, 0.1, rng)] * 3, cost_shift=7))
    with tempfile.TemporaryDirectory() as d:
        _match(d, GOOD, extra=extra)
        try:
            F.score_fruit(F.load_runs(d))
        except F.Stop as exc:
            assert "no C0 point" in str(exc)
        else:
            raise AssertionError("a cost mismatch was scored")


def test_extra_seeds_go_to_f3_only():
    def extra(d, y, rng):
        bad = [_p1(y, -0.2, rng)] * 3
        _write(d, "E4_a1.0_t7_s1007.json", _e4(7, 1.0, y, bad, seed=1007))
        _write(d, "E4_a1.0_t7_s2007.json", _e4(7, 1.0, y, bad, seed=2007))
        _write(d, "C0_a1.0_t7_s202.json", _c0(7, 1.0, y, [_p1(y, 0.05, rng)] * 4, seed=202))
        _write(d, "C0_a1.0_t7_s203.json", _c0(7, 1.0, y, [_p1(y, 0.07, rng)] * 4, seed=203))
    with tempfile.TemporaryDirectory() as d:
        _match(d, GOOD, extra=extra)
        res = F.score_fruit(F.load_runs(d))
    assert all(h["won_in_fruit_zone"] for h in res["headline"])  # the bad extra E4 seeds do not enter
    arms = {(r["arm"], r["cost"]) for r in res["f3"]}
    assert ("E4", SWEEP) in arms and ("C0", 510 * LOOP) in arms
    assert all(r["sd_ce_exact"] >= 0 for r in res["f3"])


def test_f4_and_f5():
    def margins(a):
        return {"Z": 0.0, "E4": [0.12, 0.08, 0.14], "C0": [0.03, 0.06, 0.09, 0.11]}  # E4 worsens at sweep 2
    with tempfile.TemporaryDirectory() as d:
        _match(d, margins)
        res = F.score_fruit(F.load_runs(d))
    assert res["f4"]["total"] == 9 * (1 + 3 + 4) and res["f4"]["inside"] == res["f4"]["total"]
    assert res["f5"]["non_increasing"] == 0 and res["f5"]["total"] == 9


def test_missing_primary_c0_stops():
    def extra(d, y, rng):
        os.remove(os.path.join(d, "C0_a2.0_t9.json"))
        _write(d, "C0_a2.0_t9_s202.json", _c0(9, 2.0, y, [_p1(y, 0.05, rng)] * 4, seed=202))
    with tempfile.TemporaryDirectory() as d:
        _match(d, GOOD, extra=extra)
        try:
            F.score_fruit(F.load_runs(d))
        except F.Stop as exc:
            assert "C0 seed 201" in str(exc)
        else:
            raise AssertionError("a task without the primary C0 was scored")


def test_cli_writes_once():
    with tempfile.TemporaryDirectory() as d:
        runs = os.path.join(d, "runs")
        _match(runs, GOOD)
        out = os.path.join(d, "fruit.md")
        assert F.main([runs, out, "--json", os.path.join(d, "fruit.json")]) == 0
        assert "Won in the fruit zone in 3 of 3 groups" in open(out, encoding="utf-8").read()
        assert F.main([runs, out]) == 2
