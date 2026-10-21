"""toqb.rustbind, the fast path of the PSF template arm: its slot angles equal the slow path's (compile, then the
skeleton reads the circuit) to rounding on random points, for both noise models, and the twin's <Z> is identical
with the same seeds. Needs PSF-Zero and its built rust/psfbind (skipped without)."""
import os

import numpy as np
import pytest

pytest.importorskip("qiskit")
if not os.environ.get("PSF_ZERO_REPO"):
    pytest.skip("needs PSF_ZERO_REPO", allow_module_level=True)

from toqb import rustbind as RB  # noqa: E402
from toqb import s2r2 as S2  # noqa: E402

PLAN = {"name": "rustbind test", "device": "snapshot:marrakesh",
        "task": {"n": 10, "layers": 2, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_angle": 1.0,
                 "teacher_gap": 0.2, "n_train": 8, "n_test": 20},
        "train": {}, "predict": {"traj": 16, "shots": 50, "reps": 50, "level": 0.99, "seed": 50001},
        "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017}}


def test_fast_path_equals_slow_path():
    R = S2.Runner(PLAN, "psfai:template")
    try:
        F = RB.FastPSF(R)
    except RB.Unsupported as exc:
        pytest.skip(str(exc))
    _, _, Xte, _ = S2.teacher_data2(PLAN["task"])
    rng = np.random.default_rng(5)
    from toqb import task_loop as TL
    d = TL.n_params(10, 2)
    ths = [rng.uniform(-np.pi, np.pi, d) for _ in range(12)]
    xs = list(Xte[:12])
    for model in ("sim", "dev"):
        assert F.check(model, ths, xs) < 1e-12
    cs = [R.compile(th, x) for th, x in zip(ths, xs)]
    assert np.array_equal(R.z("sim", cs, 8, 99), F.z("sim", ths, xs, 8, 99))
    assert np.array_equal(R.z("dev", cs, 8, 7, shots=True), F.z("dev", ths, xs, 8, 7, shots=True))
