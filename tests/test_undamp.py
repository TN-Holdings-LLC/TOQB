"""The undamped readout (toqb.undamp, toqb.undamp_run): the fit recovers an affine shrink, the readout is clipped to the
physical range, with lam = 1 and delta = 0 the undamped prediction is design C's own, and on a small run the stand-in's
shots are drawn again exactly (the raw CE recomputed equals the record's)."""
import copy
import os

import numpy as np
import pytest

from toqb import undamp as U


def test_fit_recovers_an_affine_shrink():
    rng = np.random.default_rng(1)
    z = rng.uniform(-0.8, 0.8, 64)
    lam, delta, rms = U.fit(0.41 * z + 0.05, z)
    assert abs(lam - 0.41) < 1e-12 and abs(delta - 0.05) < 1e-12 and rms < 1e-12
    noisy = 0.41 * z + 0.05 + rng.normal(0, 0.05, 64)
    lam, delta, _ = U.fit(noisy, z)
    assert abs(lam - 0.41) < 0.05 and abs(delta - 0.05) < 0.03


def test_fit_stops_when_it_cannot_undamp():
    z = np.linspace(-0.5, 0.5, 10)
    with pytest.raises(U.Stop):
        U.fit(-0.3 * z, z)
    with pytest.raises(U.Stop):
        U.fit(z, np.zeros(10))
    with pytest.raises(U.Stop):
        U.fit(z[:2], z[:2])


def test_apply_clips_to_the_physical_range():
    out = U.apply([0.5, -0.5, 0.05], 0.4, 0.05)
    assert np.allclose(out, [1.0, -1.0, 0.0])


def test_identity_undamping_is_design_c_prediction():
    from toqb.s2rc import predict_job
    rng = np.random.default_rng(2)
    p1 = rng.uniform(0.1, 0.9, 40)
    y = np.where(rng.uniform(size=40) > 0.5, 1, -1)
    a = predict_job(p1, y, 200, 300, 0.99, 5, traj=64)
    b = U.predict_job_undamped(p1, y, 200, 300, 0.99, 5, 1.0, 0.0, traj=64)
    for k in ("ce_mean", "ce_interval", "acc_mean", "acc_interval", "ce_exact"):
        assert np.allclose(a[k], b[k], rtol=0, atol=1e-12), k


@pytest.mark.skipif(not os.environ.get("PSF_ZERO_REPO"), reason="needs PSF-Zero (PSF_ZERO_REPO)")
def test_undamp_run_on_a_small_run():
    pytest.importorskip("qiskit")
    from toqb import s2rc, undamp_run
    plan = {"name": "undamp test", "device": "snapshot:marrakesh",
            "task": {"n": 10, "layers": 1, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_angle": 1.0,
                     "teacher_gap": 0.2, "n_train": 8, "n_test": 20},
            "train": {"seed": 201, "init": 0.0, "pairs": 2, "sim_batch": 2, "sim_traj": 4, "h": 0.1, "lr": 0.4,
                      "loops": 6, "curve_every": 3, "curve_points": 6, "curve_traj": 4},
            "predict": {"traj": 16, "shots": 50, "reps": 50, "level": 0.99, "seed": 50001},
            "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017}}
    rec = s2rc.run_s2rc(copy.deepcopy(plan), "psfai:template")
    assert rec["valid"], rec.get("error")
    res = undamp_run.run(rec, traj=16)
    assert res["kind"] == "undamp" and len(res["points"]) == 1
    p = res["points"][0]
    assert p["raw"]["reproduced"], (p["raw"]["ce"], p["raw"]["ce_recorded"])
    assert p["lam"] > 0 and 0 <= p["undamped"]["acc"] <= 1
