"""Tests of TOQB v15's variational-loop scenario (toqb.task_loop, toqb.score_loop). The first ones need numpy only."""
import math
import os

import pytest

from toqb.score_loop import tier
from toqb.task_loop import angle_list, exact_z0, gate_kinds, main, n_params, spsa_schedule, teacher_data

TASK = dict(n=4, layers=2, enc=math.pi / 2, teacher_seed=4, teacher_gap=0.2, n_train=16, n_test=8)
OPT = dict(iterations=5, batch=4, a=3.0, c=0.2, A=2, init=0.5, loop_seed=11)


def test_angles_follow_the_gate_order():
    theta = list(range(n_params(4, 2)))
    a = angle_list(theta, [1, 0, 0, 0], 4, 2, 2.0)
    assert len(a) == len(gate_kinds(4, 2)) == 2 * (4 + 8) + 4
    assert a[:4] == [2.0, 0, 0, 0] and a[4:12] == [0, 1, 2, 3, 4, 5, 6, 7] and a[-4:] == [16, 17, 18, 19]


def test_teacher_data_is_drawn_by_rule():
    a = teacher_data(TASK)
    b = teacher_data(TASK)
    assert all((x == y).all() for x, y in zip(a, b))
    Xtr, ytr, Xte, yte = a
    assert Xtr.shape == (16, 4) and Xte.shape == (8, 4) and set(ytr) <= {-1.0, 1.0}
    assert abs(Xtr).max() <= 1


def test_spsa_draws_do_not_depend_on_results():
    t1, s1 = spsa_schedule(TASK, OPT)
    t2, s2 = spsa_schedule(TASK, OPT)
    assert (t1 == t2).all() and s1 == s2 and len(s1) == 5
    assert all(len(set(idx)) == 4 and set(map(abs, d)) == {1.0} for idx, d in s1)


def test_budget_tiers():
    assert tier(0.5, 0.2, 1.0) == "1x" and tier(2.5, 0.2, 1.0) == "3x" and tier(9.0, 2.0, 1.0) == "10x"
    assert tier(25.0, 2.0, 1.0) == "over 10x"


def test_a_run_never_overwrites(tmp_path):
    (tmp_path / "x").write_text("earlier")
    assert main(["run", "plan_loop_smoke.json", str(tmp_path)]) == 2


def test_model_circuit_matches_the_numpy_model():
    pytest.importorskip("qiskit")
    import numpy as np
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from toqb.task_loop import model_circuit
    rng = np.random.default_rng(3)
    ang = angle_list(rng.uniform(-3, 3, n_params(4, 2)), rng.uniform(-1, 1, 4), 4, 2, math.pi / 2)
    qc = model_circuit(ang, 4, 2)
    qc.remove_final_measurements()
    z = Statevector(qc).expectation_value(SparsePauliOp("IIIZ")).real
    assert abs(z - exact_z0(ang, 4, 2)) < 1e-12


def test_qiskit_template_is_the_circuit():
    pytest.importorskip("qiskit_ibm_runtime")
    import numpy as np
    from toqb.devices import get_device
    from toqb.metrics import equivalence, structural_check
    from toqb.task_loop import QiskitLoop, model_circuit
    dev = get_device("fake:FakeFez")
    arm = QiskitLoop(2, "template")
    arm.setup(TASK, dev.target)
    rng = np.random.default_rng(5)
    ang = angle_list(rng.uniform(-3, 3, n_params(4, 2)), rng.uniform(-1, 1, 4), 4, 2, math.pi / 2)
    out = arm.compile(ang)
    assert structural_check(out, dev) is None
    assert equivalence(model_circuit(ang, 4, 2), out)["equivalent"]


@pytest.mark.skipif(not os.environ.get("PSF_ZERO_REPO"), reason="needs PSF_ZERO_REPO")
def test_psf_template_is_the_circuit():
    import numpy as np
    from toqb.devices import get_device
    from toqb.metrics import equivalence, structural_check
    from toqb.task_loop import PSFAILoop, model_circuit
    dev = get_device("fake:FakeFez")
    arm = PSFAILoop("template")
    arm.setup(TASK, dev.target)
    rng = np.random.default_rng(6)
    ang = angle_list(rng.uniform(-3, 3, n_params(4, 2)), rng.uniform(-1, 1, 4), 4, 2, math.pi / 2)
    out = arm.compile(ang)
    assert structural_check(out, dev) is None
    assert equivalence(model_circuit(ang, 4, 2), out)["equivalent"]
