"""Tests of toqb.kising_echo (test 2: the mirror circuit with a longitudinal field hz)."""
import json
import os
import subprocess
import sys

import numpy as np
import pytest

from toqb import kising_charge as KC
from toqb import kising_echo as E


def _flipped_probability(c, bits):
    from qiskit.quantum_info import Statevector
    n = len(bits)
    p = Statevector(c.remove_final_measurements(inplace=False)).probabilities()
    return p[sum((1 - bits[q]) << q for q in range(n))]


@pytest.mark.parametrize("n", [6, 8])
def test_noiseless_echo_returns_the_flipped_input(n):
    for hz in (0.0, 0.1, 0.3):
        for L in range(1, 6):
            for i in KC.INPUTS:
                b = KC.input_bits(i, n)
                assert _flipped_probability(E.circuit(b, n, L, 0.6, hz), b) > 1 - 1e-12


def test_forward_step_is_the_kicked_ising_step_with_hz():
    """V_0, the CZ ring and A make one step S = (RX(2h) Z RZ(2 hz))^n CZ_ring (up to a global phase)."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Operator
    n, h = 4, 0.6
    for hz in (0.0, 0.1, 0.3):
        theta, phi, lamp = E.step_angles(h, hz)
        qc = QuantumCircuit(n)
        for q in range(n):
            qc.rz(lamp, q)
        for q in range(n):
            qc.cz(q, (q + 1) % n)
        for q in range(n):
            qc.ry(theta, q)
            qc.rz(phi, q)
        rx = np.array([[np.cos(h), -1j * np.sin(h)], [-1j * np.sin(h), np.cos(h)]])
        u1 = rx @ np.diag([1.0, -1.0]) @ np.diag([np.exp(-1j * hz), np.exp(1j * hz)])
        U = np.array([[1.0]])
        for _ in range(n):
            U = np.kron(u1, U)
        cz = np.ones(2 ** n)
        for q in range(n):
            b = np.arange(2 ** n)
            cz *= np.where(((b >> q) & 1) & ((b >> ((q + 1) % n)) & 1), -1, 1)
        ref = U @ np.diag(cz)
        got = Operator(qc).data
        k = np.argmax(np.abs(ref))
        ph = got.flat[k] / ref.flat[k]
        assert np.max(np.abs(got - ph * ref)) < 1e-10 and abs(abs(ph) - 1) < 1e-10
        if hz == 0.0:  # toqb.kising's step: the same Euler angles
            assert np.allclose(E.step_angles(h, 0.0), K_step(h))


def K_step(h):
    from toqb import kising as K
    return K.step_euler(h)


@pytest.mark.parametrize("arm", ["fold:rule", "fold:zipcyc", "qiskit:2:blind:template"])
def test_compiled_arms_keep_every_two_qubit_gate_and_return(arm):
    pytest.importorskip("qiskit_ibm_runtime")
    from qiskit.quantum_info import Statevector
    from toqb import qelm as Q
    from toqb import s2r as S
    from toqb.devices import get_device
    A = S.Arm(arm, get_device("fake:FakeMarrakesh"))
    n = 12
    per = E.per_layer_q2(A, n)
    for L in (1, 2):
        for hz in (0.0, 0.3):
            b = KC.input_bits("neel", n)
            c = A.compile(E.circuit(b, n, L, 0.6, hz))
            assert E.q2_count(c) == 2 * L * per
            mm = Q.measured_map(c)
            act = sorted({c.find_bit(q).index for i in c.data for q in i.qubits
                          if i.operation.name not in ("barrier", "delay", "measure")})
            pos = {q: k for k, q in enumerate(act)}
            sv = Statevector(Q._compact(c.remove_final_measurements(inplace=False)))
            for j in range(n):
                z = 1 - 2 * sv.probabilities([pos[mm[j]]])[1]
                assert abs(z + (1 - 2 * b[j])) < 1e-9


def test_estimate_from_synthetic_counts():
    n = 4
    cc = {}
    for i in KC.INPUTS:
        b = KC.input_bits(i, n)
        flipped = "".join(str(1 - b[q]) for q in reversed(range(n)))
        same = "".join(str(b[q]) for q in reversed(range(n)))
        cc[(i, "echo")] = {flipped: 900, same: 100}  # each Z_j right with 0.9: <Z_j> s_j = 0.8
        cc[(i, "ref")] = {same: 1000}
    est = E.estimate(cc, n)
    assert abs(est["rho4"] - 0.8) < 1e-12 and est["se4"] > 0
    assert abs(est["rho_w2"] - 1.0) < 1e-12  # both flips leave Z_j Z_j+1 unchanged


def test_end_to_end_on_a_fake_device(tmp_path):
    pytest.importorskip("qiskit_aer")
    pytest.importorskip("qiskit_ibm_runtime")
    env = dict(os.environ, PYTHONWARNINGS="ignore")
    py = sys.executable
    F, R, J = str(tmp_path / "fetch"), str(tmp_path / "runs"), str(tmp_path / "job")

    def run(*args):
        r = subprocess.run([py, "-m", *args], capture_output=True, text=True, env=env, cwd=os.getcwd())
        assert r.returncode == 0, r.stdout + r.stderr
        return r.stdout
    run("toqb.s2rc_device", "fetch", "--fake", "FakeFez", "--out", F)
    for arm in ("fold:rule", "fold:zipcyc"):
        for L in (1, 2):
            run("toqb.kising_echo", "build", F, R, "--arm", arm, "--n", "12", "--L", str(L), "--hz", "0.3",
                "--shots", "400")
    out = run("toqb.kising_echo", "rehearse", R)
    assert "accepted" in out and "REJECTED" not in out
    run("toqb.s2rc_device", "assemble", "--fetch", F, "--runs", R, "--out", J, "--max-seconds", "60")
    run("toqb.s2rc_device", "submit", "--job", J, "--local")
    run("toqb.kising_echo", "score", J, R)
    res = json.load(open(os.path.join(J, "echo_score.json")))
    assert len(res["cells"]) == 4 and not res["invalid"]
    for c in res["cells"]:
        assert 0.2 < c["rho4"] < 1.2 and c["se4"] > 0
    assert len(res["duels"]) == 2 and "0.3" in res["walls"]


def test_frame_flip_keeps_the_ideal_circuit():
    from qiskit.quantum_info import Operator
    from toqb import kising_echo as KE
    qc = KE.circuit([0, 1, 0, 1, 1, 0], 6, 2, 0.6, 0.0)
    ff = KE.frame_flip(qc, 6)
    assert sum(1 for i in ff.data if i.operation.name == "x") == 2 * 3 * 2  # layers 2 and 4, before and after
    strip = lambda c: c.remove_final_measurements(inplace=False)  # noqa: E731
    assert Operator(strip(ff)).equiv(Operator(strip(qc)))
