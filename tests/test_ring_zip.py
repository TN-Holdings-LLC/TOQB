"""toqb.ring_zip (report-only, 2026-10-22): the psfai:template_zip arm compiles the S2R model exactly (the same
outcome distribution as the input), with fewer CZ than psfai:template at L 8 on the snapshot device, and design C's
run gives the same record with the fast path (TOQB_FAST_PSF=1) as without. Needs PSF-Zero (skipped without)."""
import copy
import os

import numpy as np
import pytest

pytest.importorskip("qiskit")
if not os.environ.get("PSF_ZERO_REPO"):
    pytest.skip("needs PSF_ZERO_REPO", allow_module_level=True)

from toqb import task_loop as TL  # noqa: E402


def _model(L, seed):
    rng = np.random.default_rng(seed)
    th = rng.uniform(-np.pi, np.pi, TL.n_params(10, L))
    return TL.model_circuit(TL.angle_list(th, rng.uniform(-1, 1, 10), 10, L, np.pi / 2), 10, L)


def test_zip_arm_exact_and_shorter(monkeypatch):
    monkeypatch.delenv("TOQB_RUST_TEMPLATE", raising=False)
    from toqb.devices import get_device
    tg = get_device("snapshot:marrakesh").target
    qc = _model(8, 3)
    a, z = TL.make_loop_arm("psfai:template"), TL.make_loop_arm("psfai:template_zip")
    a.setup(tg)
    z.setup(tg)
    ca, cz = a.compile_circuit(qc), z.compile_circuit(qc)
    n2 = lambda c: sum(1 for i in c.data if len(i.qubits) == 2)  # noqa: E731
    assert (n2(ca), n2(cz)) == (224, 168)
    assert z.ai._exact(qc, cz) is True and "zipper" in z.version()


def test_zip_arm_fast_path_unchanged():
    from toqb import s2rc
    plan = {"name": "zip fast", "device": "snapshot:marrakesh",
            "task": {"n": 10, "layers": 2, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_angle": 1.0,
                     "teacher_gap": 0.2, "n_train": 8, "n_test": 12},
            "train": {"seed": 201, "init": 0.0, "pairs": 2, "sim_batch": 2, "sim_traj": 4, "h": 0.1, "lr": 0.4,
                      "loops": 4, "curve_every": 2, "curve_points": 6, "curve_traj": 4},
            "predict": {"traj": 16, "shots": 50, "reps": 50, "level": 0.99, "seed": 50001},
            "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017}}
    os.environ.pop("TOQB_FAST_PSF", None)
    slow = s2rc.run_s2rc(copy.deepcopy(plan), "psfai:template_zip")
    os.environ["TOQB_FAST_PSF"] = "1"
    try:
        fast = s2rc.run_s2rc(copy.deepcopy(plan), "psfai:template_zip")
    finally:
        os.environ.pop("TOQB_FAST_PSF", None)
    assert slow["valid"] and fast["valid"]
    assert np.array_equal(slow["final_mean"], fast["final_mean"])
    assert slow["rehearsal"]["ce"] == fast["rehearsal"]["ce"]
