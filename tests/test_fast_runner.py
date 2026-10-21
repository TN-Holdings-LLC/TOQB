"""TOQB_FAST_PSF=1 (the PSF arm bound in Rust, no Qiskit circuits per point) changes nothing: design C's run, C0 with
checkpoints and E4 give the same parameters, predictions and stand-in scores as the slow path. Never used for device
runs. Needs PSF-Zero and the built rust/psfbind (skipped without)."""
import copy
import os

import numpy as np
import pytest

pytest.importorskip("qiskit")
if not os.environ.get("PSF_ZERO_REPO"):
    pytest.skip("needs PSF_ZERO_REPO", allow_module_level=True)

from toqb import s2r2 as S2  # noqa: E402
from toqb import s2rc, s2rc_ckpt, s2re4_run  # noqa: E402

BASE = {"name": "fast test", "device": "snapshot:marrakesh",
        "task": {"n": 10, "layers": 1, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_angle": 1.0,
                 "teacher_gap": 0.2, "n_train": 8, "n_test": 20},
        "predict": {"traj": 16, "shots": 50, "reps": 50, "level": 0.99, "seed": 50001},
        "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017}}
C_TRAIN = {"seed": 201, "init": 0.0, "pairs": 2, "sim_batch": 2, "sim_traj": 4, "h": 0.1, "lr": 0.4, "loops": 6,
           "curve_every": 3, "curve_points": 6, "curve_traj": 4}


def _plan(train):
    p = copy.deepcopy(BASE)
    p["train"] = dict(train)
    return p


def _both(fn, plan):
    os.environ.pop("TOQB_FAST_PSF", None)
    slow = fn(copy.deepcopy(plan), "psfai:template")
    os.environ["TOQB_FAST_PSF"] = "1"
    try:
        fast = fn(copy.deepcopy(plan), "psfai:template")
    finally:
        os.environ.pop("TOQB_FAST_PSF", None)
    assert slow["valid"] and fast["valid"], (slow.get("error"), fast.get("error"))
    return slow, fast


def _same(a, b):
    assert np.array_equal(a["final_mean"], b["final_mean"])
    assert a["prediction"]["twin_p1"] == b["prediction"]["twin_p1"]
    assert a["rehearsal"]["ce"] == b["rehearsal"]["ce"]
    assert a["rehearsal"]["standin_p1"] == b["rehearsal"]["standin_p1"]


def test_fast_runner_is_active_and_slow_is_default():
    os.environ.pop("TOQB_FAST_PSF", None)
    assert S2.Runner(_plan(C_TRAIN), "psfai:template")._fast is None
    os.environ["TOQB_FAST_PSF"] = "1"
    try:
        assert S2.Runner(_plan(C_TRAIN), "psfai:template")._fast is not None
        dev = _plan(C_TRAIN)
        dev["verify"] = False
        assert S2.Runner(dev, "psfai:template")._fast is None  # never for a device run
    finally:
        os.environ.pop("TOQB_FAST_PSF", None)


def test_design_c_unchanged():
    _same(*_both(s2rc.run_s2rc, _plan(C_TRAIN)))


def test_c0_checkpoints_unchanged():
    a, b = _both(s2rc_ckpt.run_s2rc_ckpt, _plan(dict(C_TRAIN, checkpoints=[2, 4])))
    _same(a, b)
    assert [c["rehearsal"]["ce"] for c in a["checkpoints"]] == [c["rehearsal"]["ce"] for c in b["checkpoints"]]


def test_e4_unchanged():
    _same(*_both(s2re4_run.run_s2re4, _plan({"seed": 4, "traj": 4, "sweeps": 2, "checkpoints": True})))
