"""2026-10-28: the blind Qiskit arm sees only working couplers and the basis (no error rate), avoids failed elements,
and compiles exactly; lam_device's direct noiseless reference equals Qiskit's Statevector."""
import os

import numpy as np
import pytest

pytest.importorskip("qiskit")
from toqb import lam_device as LD  # noqa: E402
from toqb import s2r as S  # noqa: E402
from toqb import task_loop as TL  # noqa: E402
from toqb.devices import get_device  # noqa: E402
from tests.test_fold import p1_all  # noqa: E402

TARGET = "file:data/targets/ibm_kingston_2026-10-24.pkl"


def test_blind_device_drops_failed_and_numbers():
    dev = get_device(TARGET)
    edges, basis = TL.blind_device(dev.target)
    assert "cz" in basis and "measure" in basis
    bad = {tuple(e) for e in dev.failed_edges} | {(b, a) for a, b in dev.failed_edges}
    assert not bad & set(edges)
    assert not any(a in dev.failed_qubits or b in dev.failed_qubits for a, b in edges)


def test_blind_arm_is_exact_and_off_failed_elements():
    dev = get_device(TARGET)
    arm = S.Arm("qiskit:2:blind:template", dev)
    theta, X = LD.model_inputs(8, 2, 0, 3)
    for x in X:
        qc = TL.model_circuit(TL.angle_list(theta, x, 8, 2, np.pi / 2), 8, 2)
        c = arm.compile(qc)
        ref = LD.noiseless_z(theta, [x], 8, 2)[0]
        assert abs((1 - 2 * p1_all(c)[0]) - ref) < 1e-9
        arm.duration(c, (8, 2))
    assert arm.on_failed_ops == 0 and arm.structural_fail == 0


def test_direct_noiseless_equals_qiskit(monkeypatch):
    theta, X = LD.model_inputs(9, 3, 0, 4)
    monkeypatch.setenv("TOQB_NOISELESS", "qiskit")
    a = LD.noiseless_z(theta, X, 9, 3)
    monkeypatch.setenv("TOQB_NOISELESS", "numpy")
    b = LD.noiseless_z(theta, X, 9, 3)
    assert np.abs(a - b).max() < 1e-9
