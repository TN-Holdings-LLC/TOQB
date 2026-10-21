"""The fruit match's runners (2026-10-21): checkpoints do not change the training. s2rc_ckpt's final parameters and
scores equal design C's own (toqb.s2rc) on the same plan, and its checkpoints equal shorter s2rc runs; E4 with
checkpoints ends where E4 without them ends. Small plans on the CPU; needs qiskit and PSF-Zero (skipped without)."""
import copy
import os

import numpy as np
import pytest

pytest.importorskip("qiskit")
if not os.environ.get("PSF_ZERO_REPO"):
    pytest.skip("needs PSF_ZERO_REPO (and PSF_COMPILE_FILE, PSF_AI_FILE)", allow_module_level=True)

from toqb import s2rc  # noqa: E402
from toqb import s2rc_ckpt  # noqa: E402
from toqb import s2re4_run  # noqa: E402

SPEC = "psfai:template"
BASE = {"name": "fruit test", "device": "snapshot:marrakesh",
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


def test_checkpoints_do_not_change_design_c():
    ref = s2rc.run_s2rc(_plan(C_TRAIN), SPEC)
    got = s2rc_ckpt.run_s2rc_ckpt(_plan(dict(C_TRAIN, checkpoints=[2, 4])), SPEC)
    assert ref["valid"] and got["valid"], (ref.get("error"), got.get("error"))
    assert np.array_equal(ref["final_mean"], got["final_mean"])
    assert ref["rehearsal"]["ce"] == got["rehearsal"]["ce"]
    assert ref["prediction"]["twin_p1"] == got["prediction"]["twin_p1"]
    assert [c["loop"] for c in got["checkpoints"]] == [2, 4]
    assert got["checkpoints"][0]["train_traj_circuits"] == 2 * 2 * 2 * 2 * 4
    short = s2rc.run_s2rc(_plan(dict(C_TRAIN, loops=4)), SPEC)
    assert np.allclose(short["final_mean"], got["checkpoints"][1]["theta"], rtol=0, atol=0)
    assert short["rehearsal"]["ce"] == got["checkpoints"][1]["rehearsal"]["ce"]


def test_checkpoints_do_not_change_e4():
    tr = {"seed": 4, "traj": 4, "sweeps": 2}
    ref = s2re4_run.run_s2re4(_plan(tr), SPEC)
    got = s2re4_run.run_s2re4(_plan(dict(tr, checkpoints=True)), SPEC)
    assert ref["valid"] and got["valid"], (ref.get("error"), got.get("error"))
    assert np.array_equal(ref["final_mean"], got["final_mean"])
    assert ref["rehearsal"]["ce"] == got["rehearsal"]["ce"]
    assert [c["sweep"] for c in got["checkpoints"]] == [1]
    one = s2re4_run.run_s2re4(_plan(dict(tr, sweeps=1)), SPEC)
    assert np.array_equal(one["final_mean"], got["checkpoints"][0]["theta"])
    assert one["rehearsal"]["ce"] == got["checkpoints"][0]["rehearsal"]["ce"]
