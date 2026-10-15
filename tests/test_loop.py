"""Tests of TOQB v15's variational-loop scenario (toqb.task_loop, toqb.score_loop, toqb.pennylane_device). The first
ones need numpy only."""
import math
import os

import pytest

from toqb.score_loop import at_budget, tier
from toqb.task_loop import (DEFAULT_COST, angle_list, exact_z0, gate_kinds, main, n_params, qpu_seconds,
                             spsa_schedule, teacher_data, z_of_counts)

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


def test_price_and_budget():
    c = dict(DEFAULT_COST)
    assert abs(qpu_seconds([2e-6, 4e-6], 100, c) - (2 * 0.036 + 100 * (2 * 0.00027 + 6e-6))) < 1e-12
    assert c["usd_per_s"] == 96 / 60
    rec = dict(evals=[dict(iteration=0, batch_usd=0.0, session_usd=0.0), dict(iteration=10, batch_usd=5.0, session_usd=6.0),
                      dict(iteration=20, batch_usd=10.0, session_usd=12.0)])
    assert at_budget(rec, "batch", 10.0)["iteration"] == 20 and at_budget(rec, "session", 10.0)["iteration"] == 10


def test_z_of_counts_reads_clbit_zero():
    assert z_of_counts({"10": 30, "01": 70}) == -0.4 and z_of_counts({"0 1": 1, "0 0": 3}) == 0.5


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
    arm.setup(dev.target)
    rng = np.random.default_rng(5)
    for _ in range(2):  # the second circuit reuses the template
        ang = angle_list(rng.uniform(-3, 3, n_params(4, 2)), rng.uniform(-1, 1, 4), 4, 2, math.pi / 2)
        out = arm.compile_circuit(model_circuit(ang, 4, 2))
        assert structural_check(out, dev) is None
        assert equivalence(model_circuit(ang, 4, 2), out)["equivalent"]
    assert arm.stats["template_builds"] == 1


@pytest.mark.skipif(not os.environ.get("PSF_ZERO_REPO"), reason="needs PSF_ZERO_REPO")
def test_psf_template_is_the_circuit():
    import numpy as np
    from toqb.devices import get_device
    from toqb.metrics import equivalence, structural_check
    from toqb.task_loop import PSFAILoop, model_circuit
    dev = get_device("fake:FakeFez")
    arm = PSFAILoop("template")
    arm.setup(dev.target)
    rng = np.random.default_rng(6)
    for _ in range(2):
        ang = angle_list(rng.uniform(-3, 3, n_params(4, 2)), rng.uniform(-1, 1, 4), 4, 2, math.pi / 2)
        out = arm.compile_circuit(model_circuit(ang, 4, 2))
        assert structural_check(out, dev) is None
        assert equivalence(model_circuit(ang, 4, 2), out)["equivalent"]
    assert arm.stats == dict(template_builds=1, template_unavailable=0)


def test_pennylane_tape_is_the_qiskit_circuit():
    pytest.importorskip("pennylane")
    import numpy as np
    import pennylane as qml
    from toqb.pennylane_device import tape_to_qiskit
    from toqb.task_loop import _qiskit_sig, model_circuit, model_ops
    rng = np.random.default_rng(7)
    ang = angle_list(rng.uniform(-3, 3, n_params(4, 3)), rng.uniform(-1, 1, 4), 4, 3, math.pi / 2)
    tape = qml.tape.QuantumScript(model_ops(ang, 4, 3), [qml.expval(qml.PauliZ(0))], shots=10)
    a, b = tape_to_qiskit(tape, [0, 1, 2, 3]), model_circuit(ang, 4, 3)
    assert _qiskit_sig(a) == _qiskit_sig(b)
    assert [float(p) for i in a.data for p in i.operation.params] == [float(p) for i in b.data for p in i.operation.params]


def test_counts_are_marginalised_in_pennylane_order():
    from toqb.pennylane_device import _counts_for
    q = {"0011": 5, "1010": 3}  # clbit 0 rightmost: "0011" has wires 0 and 1 at 1
    assert _counts_for(q, [0, 1, 2, 3], [0, 1]) == {"11": 5, "01": 3}
    assert _counts_for(q, [0, 1, 2, 3], [3]) == {"0": 5, "1": 3}


@pytest.mark.skipif(not os.environ.get("PSF_ZERO_REPO"), reason="needs PSF_ZERO_REPO")
def test_pennylane_device_runs_a_qnode():
    pytest.importorskip("pennylane")
    import numpy as np
    import pennylane as qml
    from toqb.pennylane_device import CompiledDevice
    from toqb.task_loop import model_ops
    dev = CompiledDevice(wires=4, compiler="psfai:template", seed=3)

    @qml.set_shots(4000)
    @qml.qnode(dev)
    def f(a):
        model_ops(a, 4, 2)  # operations created inside a QNode are queued as they are made
        return qml.expval(qml.PauliZ(0))
    rng = np.random.default_rng(8)
    ang = angle_list(rng.uniform(-3, 3, n_params(4, 2)), rng.uniform(-1, 1, 4), 4, 2, math.pi / 2)
    with qml.Tracker(dev) as tr:
        z = float(f(ang))
    assert abs(z - exact_z0(ang, 4, 2)) < 0.06  # TOQB noise and 4000 shots
    assert tr.totals["executions"] == 1 and tr.totals["usd"] > 0 and dev.executor.structural_fail == 0
