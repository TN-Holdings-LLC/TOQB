"""The E4v variant in toqb.s2re4_run (W13): the default stays E4 exactly; e4v costs what E4 costs and records its
checks. Small plans on the CPU; needs qiskit and PSF-Zero (skipped without), like tests/test_fruit.py."""
import copy
import os

import numpy as np
import pytest

pytest.importorskip("qiskit")
if not os.environ.get("PSF_ZERO_REPO"):
    pytest.skip("needs PSF_ZERO_REPO (and PSF_COMPILE_FILE, PSF_AI_FILE)", allow_module_level=True)

from toqb import s2re4_run  # noqa: E402

SPEC = "psfai:template"
BASE = {"name": "e4v test", "device": "snapshot:marrakesh",
        "task": {"n": 10, "layers": 1, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_angle": 1.0,
                 "teacher_gap": 0.2, "n_train": 8, "n_test": 20},
        "predict": {"traj": 16, "shots": 50, "reps": 50, "level": 0.99, "seed": 50001},
        "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017}}


def _plan(train):
    p = copy.deepcopy(BASE)
    p["train"] = dict(train)
    return p


def test_default_is_e4():
    tr = {"seed": 4, "traj": 4, "sweeps": 1}
    ref = s2re4_run.run_s2re4(_plan(tr), SPEC)
    got = s2re4_run.run_s2re4(_plan(dict(tr, variant="e4")), SPEC)
    assert ref["valid"] and got["valid"], (ref.get("error"), got.get("error"))
    assert np.array_equal(ref["final_mean"], got["final_mean"])
    assert ref["rehearsal"]["ce"] == got["rehearsal"]["ce"]
    assert "variant" not in ref and "variant" not in got


def test_e4v_cost_checkpoints_and_fields():
    tr = {"seed": 4, "traj": 8, "sweeps": 2, "checkpoints": True, "variant": "e4v"}
    got = s2re4_run.run_s2re4(_plan(tr), SPEC)
    assert got["valid"], got.get("error")
    d, m = len(got["final_mean"]), BASE["task"]["n_train"]
    assert got["n_params"] == d
    assert got["train_traj_circuits"] == 2 * 3 * d * m * 8
    assert [c["sweep"] for c in got["checkpoints"]] == [1]
    assert got["checkpoints"][0]["train_traj_circuits"] == 3 * d * m * 8
    assert got["variant"] == "e4v" and got["quarter_traj"] == 2
    assert len(got["accepted_per_sweep"]) == 2 and all(0 <= a <= d for a in got["accepted_per_sweep"])
    assert all(v <= 0 for v in got["brier_change_per_sweep"])  # only steps whose check is negative are taken
    # the same E4 cost as plain E4 with the same traj
    e4 = s2re4_run.run_s2re4(_plan({"seed": 4, "traj": 8, "sweeps": 2}), SPEC)
    assert e4["train_traj_circuits"] == got["train_traj_circuits"]


def test_e4v_needs_traj_divisible_by_four():
    with pytest.raises(ValueError):
        s2re4_run.run_s2re4(_plan({"seed": 4, "traj": 6, "sweeps": 1, "variant": "e4v"}), SPEC)


def test_unknown_variant_stops():
    with pytest.raises(ValueError):
        s2re4_run.run_s2re4(_plan({"seed": 4, "traj": 8, "sweeps": 1, "variant": "e5"}), SPEC)
