"""Tests of toqb.predscore on synthetic data with known answers (numpy and scipy only; no quantum package).

    python -m pytest tests/test_predscore.py        (from the TOQB root)
    python tests/test_predscore.py                  (same tests, without pytest)
"""
import ast
import json
import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from toqb import predscore as PS  # noqa: E402

T_PRED = 1024
N_SHOTS = 1000


def _truth(P, seed):
    rng = np.random.default_rng(seed)
    y = np.where(np.arange(P) % 2 == 0, 1, -1)
    # the label's side of 1/2, with margins spread over (0.02, 0.45); a few points on the wrong side
    side = np.where(y > 0, -1.0, 1.0)
    margin = rng.uniform(0.02, 0.45, P)
    wrong = rng.random(P) < 0.2
    p_true = 0.5 + np.where(wrong, -side, side) * margin
    return y, p_true, rng


def _pred(y, p1, traj=T_PRED, fixed_at=None):
    return dict(format=PS.FORMAT_PRED, fixed_at=fixed_at, fixed_by_hash=False,
                twin=dict(name="synthetic", traj=traj), compiler=dict(arm="synthetic"), shots=N_SHOTS,
                inputs=dict(run_record_sha256="0" * 64),
                points=[dict(i=i, label=int(y[i]), p1=float(p1[i])) for i in range(len(y))],
                job=dict(level=0.99))


def _write(d, name, obj):
    path = os.path.join(d, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return path, PS.sha256_file(path)


def _shots_meas(pred_sha, k, n, tier="device", observed_at=None):
    return dict(format=PS.FORMAT_MEAS, kind="shots", tier=tier, observed_at=observed_at,
                inputs=dict(prediction_sha256=pred_sha),
                points=[dict(i=i, k=int(k[i]), n=int(n)) for i in range(len(k))])


def _twin_p1(p_true, rng, traj=T_PRED):
    """A perfect twin: the truth plus its own Monte Carlo error only."""
    return np.clip(p_true + rng.standard_normal(len(p_true)) * np.sqrt(p_true * (1 - p_true) / traj), 1e-6, 1 - 1e-6)


def test_perfect_prediction_is_calibrated():
    y, p_true, rng = _truth(2000, 1)
    p1 = _twin_p1(p_true, rng)
    k = rng.binomial(N_SHOTS, p_true)
    with tempfile.TemporaryDirectory() as d:
        pf, ps = _write(d, "pred.json", _pred(y, p1))
        mf, ms = _write(d, "meas.json", _shots_meas(ps, k, N_SHOTS))
        sc = PS.score(PS.load_json(pf), PS.load_json(mf), ps, ms, ref=PS.load_json(pf), ref_sha=ps)
    cov = sc["coverage"]["0.99"]
    assert 0.975 <= cov <= 1.0, cov
    assert abs(sc["log_score"]["calibration_z"]) < 5, sc["log_score"]["calibration_z"]
    # against itself as the reference, the information is exactly zero
    assert sc["information"]["reference"]["total_nats"] == 0.0
    # and a perfect twin carries information over chance
    assert sc["information"]["chance"]["per_point_nats"] > 0
    assert set(sc["per_class"]) == {"+1", "-1"}


def test_shifted_prediction_is_detected():
    y, p_true, rng = _truth(2000, 2)
    good = _twin_p1(p_true, rng)
    bad = np.clip(good + 0.08, 1e-6, 1 - 1e-6)
    k = rng.binomial(N_SHOTS, p_true)
    with tempfile.TemporaryDirectory() as d:
        pf, ps = _write(d, "pred.json", _pred(y, bad))
        rf, rs = _write(d, "ref.json", _pred(y, good))
        mf, ms = _write(d, "meas.json", _shots_meas(ps, k, N_SHOTS))
        sc = PS.score(PS.load_json(pf), PS.load_json(mf), ps, ms, ref=PS.load_json(rf), ref_sha=rs)
    assert sc["coverage"]["0.99"] < 0.6, sc["coverage"]
    assert sc["log_score"]["calibration_z"] < -10, sc["log_score"]["calibration_z"]
    assert sc["information"]["reference"]["total_nats"] < -100, sc["information"]


def test_hash_mismatch_stops():
    y, p_true, rng = _truth(200, 3)
    p1 = _twin_p1(p_true, rng)
    k = rng.binomial(N_SHOTS, p_true)
    with tempfile.TemporaryDirectory() as d:
        pf, ps = _write(d, "pred.json", _pred(y, p1))
        mf, _ = _write(d, "meas.json", _shots_meas(ps, k, N_SHOTS))
        # the prediction is changed after the measurement named it
        changed = _pred(y, p1)
        changed["points"][0]["p1"] = 0.123
        with open(pf, "w", encoding="utf-8") as f:
            json.dump(changed, f)
        code = PS.main([pf, mf, os.path.join(d, "score.json")])
        assert code == 2
        assert not os.path.exists(os.path.join(d, "score.json"))


def test_one_class_is_refused():
    y, p_true, rng = _truth(200, 4)
    y = np.ones_like(y)
    p1 = _twin_p1(p_true, rng)
    k = rng.binomial(N_SHOTS, p_true)
    with tempfile.TemporaryDirectory() as d:
        pf, ps = _write(d, "pred.json", _pred(y, p1))
        mf, ms = _write(d, "meas.json", _shots_meas(ps, k, N_SHOTS))
        try:
            PS.score(PS.load_json(pf), PS.load_json(mf), ps, ms)
        except PS.Stop as exc:
            assert "one-class" in str(exc)
        else:
            raise AssertionError("a one-class evaluation was scored")


def test_no_overwrite():
    y, p_true, rng = _truth(200, 5)
    p1 = _twin_p1(p_true, rng)
    k = rng.binomial(N_SHOTS, p_true)
    with tempfile.TemporaryDirectory() as d:
        pf, ps = _write(d, "pred.json", _pred(y, p1))
        mf, _ = _write(d, "meas.json", _shots_meas(ps, k, N_SHOTS))
        out = os.path.join(d, "score.json")
        assert PS.main([pf, mf, out]) == 0
        before = open(out, "rb").read()
        assert PS.main([pf, mf, out]) == 2
        assert open(out, "rb").read() == before


def test_exact_truth_kind():
    y, p_true, rng = _truth(2000, 6)
    p1 = _twin_p1(p_true, rng)
    with tempfile.TemporaryDirectory() as d:
        pf, ps = _write(d, "pred.json", _pred(y, p1))
        meas = dict(format=PS.FORMAT_MEAS, kind="exact-no-shots", tier="stand-in", inputs=dict(prediction_sha256=ps),
                    points=[dict(i=i, p_exact=float(p_true[i])) for i in range(len(y))])
        mf, ms = _write(d, "meas.json", meas)
        sc = PS.score(PS.load_json(pf), PS.load_json(mf), ps, ms)
    assert sc["kind"] == "exact-no-shots" and sc["claimable"] is False
    assert 0.975 <= sc["coverage_twin_error"]["0.99"] <= 1.0, sc["coverage_twin_error"]
    assert any("not evidence about a device" in w for w in sc["warnings"])


def test_claimable_only_for_device_fixed_before_truth():
    y, p_true, rng = _truth(200, 7)
    p1 = _twin_p1(p_true, rng)
    k = rng.binomial(N_SHOTS, p_true)
    with tempfile.TemporaryDirectory() as d:
        pf, ps = _write(d, "pred.json", _pred(y, p1, fixed_at="2026-10-20T08:00:00+00:00"))
        pd = PS.load_json(pf)
        pd["fixed_by_hash"] = True
        pf, ps = _write(d, "pred2.json", pd)
        for tier, obs, want in (("device", "2026-10-20T12:00:00+00:00", True),
                                ("device", "2026-10-20T07:00:00+00:00", False),
                                ("stand-in", "2026-10-20T12:00:00+00:00", False)):
            mf, ms = _write(d, f"meas_{tier}_{obs[11:13]}.json", _shots_meas(ps, k, N_SHOTS, tier, obs))
            sc = PS.score(PS.load_json(pf), PS.load_json(mf), ps, ms)
            assert sc["claimable"] is want, (tier, obs, sc["claimable"])


def test_converters_from_s2rc_and_rehearsal():
    y, p_true, rng = _truth(100, 8)
    p1 = _twin_p1(p_true, rng)
    rec = dict(kind="s2rc", arm="psfai:template", seed=201, version="v", engine="cupy", dtype="complex64",
               device="snapshot:marrakesh", task=dict(n=10, layers=16), wall_s=6000.0, train_wall_s=5500.0,
               times=dict(sim=1.0, eval=2.0), predict=dict(traj=T_PRED, shots=N_SHOTS),
               test_labels=[int(v) for v in y],
               prediction=dict(twin_p1=[float(v) for v in p1], ce_mean=0.6, ce_interval=[0.59, 0.61], acc_mean=0.6,
                               acc_interval=[0.55, 0.65], ce_exact=0.6, level=0.99, reps=20000),
               prediction_shots_only=dict(ce_interval=[0.595, 0.605], acc_interval=[0.56, 0.64]),
               standin=dict(t12=0.3, over=0.01, zz_hz=10000.0, seed=20261017),
               rehearsal=dict(standin_p1=[float(v) for v in p_true]))
    with tempfile.TemporaryDirectory() as d:
        rf, _ = _write(d, "run.json", rec)
        pf = os.path.join(d, "pred.json")
        assert PS.main(["from-s2rc", rf, pf, "--price", "2.5"]) == 0
        mf = os.path.join(d, "meas.json")
        assert PS.main(["from-rehearsal", rf, mf, "--pred", pf]) == 0
        out = os.path.join(d, "score.json")
        assert PS.main([pf, mf, out]) == 0
        sc = PS.load_json(out)
        pred = PS.load_json(pf)
    assert sc["tier"] == "stand-in" and sc["kind"] == "exact-no-shots" and sc["claimable"] is False
    assert pred["cost"]["usd"] == 6000.0 / 3600 * 2.5
    assert [p["label"] for p in pred["points"]] == [int(v) for v in y]


def test_converter_from_device():
    y, p_true, rng = _truth(50, 9)
    p1 = _twin_p1(p_true, rng)
    k = rng.binomial(250, p_true)
    with tempfile.TemporaryDirectory() as d:
        job = os.path.join(d, "job")
        os.makedirs(job)
        man = dict(written="2026-10-20T08:00:00+00:00 (2026-10-20 10:00:00 CEST)", qpy_sha256="q" * 64,
                   fetch=dict(backend="ibm_test", calibration_time="t0"),
                   cells=[dict(cell=0, run_sha256="r" * 64, labels=[int(v) for v in y], twin_p1=[float(v) for v in p1])],
                   pubs=[dict(cell=0, point=i) for i in range(len(y))])
        # Qiskit keys with two classical bits: clbit 0 is the rightmost character
        rows = [dict(pub=i, counts={"01": int(k[i]), "00": int(250 - k[i])}) for i in range(len(y))]
        raw = dict(fetched="2026-10-20T12:00:00+00:00 (2026-10-20 14:00:00 CEST)", job_id="j", rows=rows)
        for name, obj in (("manifest.json", man), ("raw_counts.json", raw)):
            with open(os.path.join(job, name), "w", encoding="utf-8") as f:
                json.dump(obj, f)
        pr = _pred(y, p1)
        pr["inputs"]["run_record_sha256"] = "r" * 64
        pf, ps = _write(d, "pred.json", pr)
        mf = os.path.join(d, "meas.json")
        assert PS.main(["from-device", job, "0", mf, "--pred", pf]) == 0
        meas = PS.load_json(mf)
        out = os.path.join(d, "score.json")
        assert PS.main([pf, mf, out]) == 0
        sc = PS.load_json(out)
    assert [m["k"] for m in meas["points"]] == [int(v) for v in k]
    assert sc["claimable"] is True and sc["tier"] == "device"


def test_device_order_uses_submission_time():
    """Home review (2026-10-20): the prediction must be fixed before the job was submitted, not only before the
    results were fetched. A manifest written after the submission time is not claimable."""
    y, p_true, rng = _truth(40, 11)
    p1 = _twin_p1(p_true, rng)
    k = rng.binomial(250, p_true)
    with tempfile.TemporaryDirectory() as d:
        job = os.path.join(d, "job")
        os.makedirs(job)
        man = dict(written="2026-10-20T09:00:00+00:00 (x)", qpy_sha256="q" * 64,
                   fetch=dict(backend="ibm_test", calibration_time="t0"),
                   cells=[dict(cell=0, run_sha256="r" * 64, labels=[int(v) for v in y], twin_p1=[float(v) for v in p1])],
                   pubs=[dict(cell=0, point=i) for i in range(len(y))])
        rows = [dict(pub=i, counts={"1": int(k[i]), "0": int(250 - k[i])}) for i in range(len(y))]
        raw = dict(fetched="2026-10-20T12:00:00+00:00 (x)", job_id="j", rows=rows)
        sub = dict(job_id="j", submitted="2026-10-20T08:30:00+00:00 (x)")
        for name, obj in (("manifest.json", man), ("raw_counts.json", raw), ("submission.json", sub)):
            with open(os.path.join(job, name), "w", encoding="utf-8") as f:
                json.dump(obj, f)
        pr = _pred(y, p1)
        pr["inputs"]["run_record_sha256"] = "r" * 64
        pf, _ = _write(d, "pred.json", pr)
        mf, out = os.path.join(d, "meas.json"), os.path.join(d, "score.json")
        assert PS.main(["from-device", job, "0", mf, "--pred", pf]) == 0
        assert PS.main([pf, mf, out]) == 0
        sc = PS.load_json(out)
    assert sc["prediction_fixed_before_truth"] is False and sc["claimable"] is False


def test_scorer_cannot_produce_truth():
    """The truth / scored separation, as a rule a test can check: predscore imports no simulator or engine."""
    src = open(os.path.join(os.path.dirname(PS.__file__), "predscore.py"), encoding="utf-8").read()
    mods = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            mods |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
    allowed = {"__future__", "datetime", "hashlib", "json", "math", "os", "sys", "numpy", "scipy"}
    assert mods <= allowed, mods - allowed


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
