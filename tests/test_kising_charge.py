"""toqb.kising_charge (2026-10-29, noise wall stage 1, probe P1): the weight-2 charge commutes with the circuit's own
step; the circuits keep <Q> at its exact value at every L; the arms keep it after compilation with one structure; the
estimator recovers exact values from sampled counts; the four-input ratio removes the first-order relaxation bias
(the workplace's r2 numbers); and the procedure runs end to end on a fake device."""
import json
import os
import subprocess
import sys
from functools import reduce

import numpy as np
import pytest

pytest.importorskip("qiskit")
from qiskit import QuantumCircuit  # noqa: E402
from qiskit.quantum_info import Operator, Statevector  # noqa: E402
from scipy.linalg import expm  # noqa: E402

from toqb import kising as K  # noqa: E402
from toqb import kising_charge as KC  # noqa: E402
from toqb import s2r as S  # noqa: E402
from toqb.devices import get_device  # noqa: E402

TARGET = "file:data/targets/ibm_kingston_2026-10-24.pkl"
H = 0.6
I2, X, Y, Z = np.eye(2), np.array([[0, 1], [1, 0]], complex), np.array([[0, -1j], [1j, 0]]), np.diag([1.0, -1.0])


def q_matrix(n, coef):
    """Q in Qiskit's order (qubit q is the q-th factor from the right)."""
    b, c = coef

    def on(d):
        return reduce(np.kron, [d.get(q, I2) for q in reversed(range(n))])
    return sum(on({j: Z, (j + 1) % n: Z}) + b * on({j: Y, (j + 1) % n: Z}) + c * on({j: Z, (j + 1) % n: Y})
               for j in range(n))


def counts_of(qc_or_sv, n):
    """Exact 'counts' (probabilities x 1e6) over the n measured clbits of a logical circuit."""
    sv = Statevector(qc_or_sv.remove_final_measurements(inplace=False))
    return {k: v * 1e6 for k, v in sv.probabilities_dict().items()}


def test_charge_is_n_independent_and_two_dimensional():
    cs = [KC.charges(n, H) for n in (6, 8, 20)]
    for ch in cs:
        assert ch["dim"] == 2 and ch["edge_spread"] < 1e-10
    for ch in cs[1:]:
        assert np.allclose(ch["coef"], cs[0]["coef"], atol=1e-10)


@pytest.mark.parametrize("n", [6, 8])
def test_charge_commutes_with_the_circuit_step(n):
    coef = KC.charges(n, H)["coef"]
    Q = q_matrix(n, coef)
    # S = (RX(2h) Z)^n CZ_ring, built as a Qiskit circuit
    st = QuantumCircuit(n)
    for q in range(n):
        st.cz(q, (q + 1) % n)
    for q in range(n):
        st.z(q)
        st.rx(2 * H, q)
    Sop = Operator(st).data
    assert np.abs(Sop @ Q - Q @ Sop).max() < 1e-10
    # the model layer B A (RY(theta), RZ(phi + lam), CZ ring) conserves A^dagger Q A, A = RZ(phi) RY(theta)
    theta, phi, lam = K.step_euler(H)
    lay, a = QuantumCircuit(n), QuantumCircuit(n)
    for q in range(n):
        lay.ry(theta, q)
        lay.rz(phi + lam, q)
        a.ry(theta, q)
        a.rz(phi, q)
    for q in range(n):
        lay.cz(q, (q + 1) % n)
    F, A = Operator(lay).data, Operator(a).data
    Qc = A.conj().T @ Q @ A
    assert np.abs(F @ Qc - Qc @ F).max() < 1e-10


@pytest.mark.parametrize("n", [6, 8])
def test_noiseless_circuits_keep_q_exact(n):
    coef = KC.charges(n, H)["coef"]
    for L in range(1, 6):
        for i in KC.INPUTS:
            bits = KC.input_bits(i, n)
            tot = 0.0
            for s in KC.SETTINGS:
                m, _ = KC.setting_value(counts_of(KC.circuit(bits, s, n, L, H), n), s, n, coef)
                tot += m  # a single setting's share changes with L; only the sum is conserved
            assert abs(tot - KC.q_noiseless(bits, n)) < 1e-9


def _compiled_counts(c):
    """Exact counts over the clbits of a compiled circuit (only its active qubits simulated)."""
    act = sorted({c.find_bit(q).index for i in c.data for q in i.qubits if i.operation.name not in ("barrier", "delay")})
    idx = {q: k for k, q in enumerate(act)}
    s, meas = QuantumCircuit(len(act)), {}
    for i in c.data:
        nm = i.operation.name
        if nm in ("barrier", "delay"):
            continue
        if nm == "measure":
            meas[c.find_bit(i.clbits[0]).index] = idx[c.find_bit(i.qubits[0]).index]
            continue
        s.append(i.operation, [idx[c.find_bit(q).index] for q in i.qubits])
    probs = Statevector(s).probabilities(sorted(meas, key=lambda k: k) and [meas[k] for k in sorted(meas)])
    nm = len(meas)
    return {format(k, f"0{nm}b"): float(p) * 1e6 for k, p in enumerate(probs) if p > 1e-14}


@pytest.mark.parametrize("arm_name", ["fold:rule", "fold:zipcyc", "qiskit:2:blind:template"])
def test_compiled_arms_keep_q_exact_with_one_structure(arm_name):
    n, L = 8, 3
    coef = KC.charges(n, H)["coef"]
    arm = S.Arm(arm_name, get_device(TARGET))
    sigs, cs = set(), []
    for i in KC.INPUTS:
        bits = KC.input_bits(i, n)
        tot = 0.0
        for s in KC.SETTINGS:
            logical = KC.circuit(bits, s, n, L, H)
            c = arm.compile(logical)
            cs.append(c)
            m, _ = KC.setting_value(_compiled_counts(c), s, n, coef)
            ml, _ = KC.setting_value(counts_of(logical, n), s, n, coef)
            assert abs(m - ml) < 1e-8  # the compiled circuit reads the same setting value as the logical one
            tot += m
            sigs.add(tuple((x.operation.name, tuple(c.find_bit(q).index for q in x.qubits)) for x in c.data))
        assert abs(tot - KC.q_noiseless(bits, n)) < 1e-8
        rc, _ = KC.reference_circuit(cs[0], bits)
        mr, _ = KC.setting_value(_compiled_counts(rc), "Z", n, coef)
        assert abs(mr - KC.q_noiseless(bits, n)) < 1e-9
    assert len(sigs) == 1  # one template: every circuit of (n, L) has the same structure
    assert arm.on_failed_ops == 0 and arm.structural_fail == 0


def test_estimator_from_sampled_counts():
    n, L, shots = 6, 2, 200_000
    coef = KC.charges(n, H)["coef"]
    rng = np.random.default_rng(3)
    cc = {}
    for i in KC.INPUTS:
        bits = KC.input_bits(i, n)
        for s in KC.SETTINGS:
            ex = counts_of(KC.circuit(bits, s, n, L, H), n)
            keys = list(ex)
            p = np.array([ex[k] for k in keys]) / sum(ex.values())
            draw = rng.multinomial(shots, p)
            cc[(i, s)] = {k: int(v) for k, v in zip(keys, draw) if v}
        key = "".join(str(b) for b in reversed(bits))  # rightmost character is clbit 0
        cc[(i, "ref")] = {key: shots}
    est = KC.estimate(cc, n, L, coef)
    assert abs(est["rho4"] - 1.0) < 4 * est["se4"] + 1e-12
    for i in KC.INPUTS:
        bits = KC.input_bits(i, n)
        assert abs(est["ref"][i] - KC.q_noiseless(bits, n)) < 1e-12
        assert abs(est["Q"][i] - KC.q_noiseless(bits, n)) < 0.05
    assert abs(KC.p_eff(KC.rho_predicted(0.0051, 50), 50) - 0.0051) < 1e-12


def test_four_inputs_remove_first_order_relaxation_bias():
    """Density matrix, n = 6, S-frame step then amplitude damping (gamma) and depolarizing (p) on every qubit; the
    target is the same with the damping Pauli-twirled. Reproduces the workplace's r2 table (t1_bias.py)."""
    n = 6
    coef = KC.charges(n, H)["coef"]
    Q = q_matrix(n, coef)
    st = QuantumCircuit(n)
    for q in range(n):
        st.cz(q, (q + 1) % n)
    for q in range(n):
        st.z(q)
        st.rx(2 * H, q)
    Sop = Operator(st).data

    def on(q, m):
        return reduce(np.kron, [m if k == q else I2 for k in reversed(range(n))])

    def run(bits, gam, p, L, twirl):
        psi = np.zeros(2 ** n)
        psi[int("".join(str(b) for b in reversed(bits)), 2)] = 1
        rho, out = np.outer(psi, psi), []
        k0, k1 = np.array([[1, 0], [0, np.sqrt(1 - gam)]]), np.array([[0, np.sqrt(gam)], [0, 0]])
        px = py = gam / 4
        pz = (2 - gam - 2 * np.sqrt(1 - gam)) / 4
        out.append(np.real(np.trace(Q @ rho)))
        for _ in range(L):
            rho = Sop @ rho @ Sop.conj().T
            for q in range(n):
                if twirl:
                    rho = ((1 - px - py - pz) * rho + px * on(q, X) @ rho @ on(q, X) + py * on(q, Y) @ rho @ on(q, Y)
                           + pz * on(q, Z) @ rho @ on(q, Z))
                else:
                    a0, a1 = on(q, k0), on(q, k1)
                    rho = a0 @ rho @ a0.conj().T + a1 @ rho @ a1.conj().T
                rho = (1 - p) * rho + p / 3 * sum(on(q, P) @ rho @ on(q, P) for P in (X, Y, Z))
            out.append(np.real(np.trace(Q @ rho)))
        return np.array(out)

    gam, p, L = 0.004, 0.003, 30
    E = {i: run(KC.input_bits(i, n), gam, p, L, False) for i in KC.INPUTS}
    T = run(KC.input_bits("zero", n), gam, p, L, True)
    tgt = T / T[0]
    num = sum(KC.SIGN[i] * E[i] for i in KC.INPUTS)
    b4, b1 = num / num[0] - tgt, E["zero"] / E["zero"][0] - tgt
    assert abs(b1[10] - 0.0527) < 5e-4 and abs(b1[30] - 0.1180) < 5e-4
    assert abs(b4[10] - 0.00078) < 5e-5 and abs(b4[30] - 0.00536) < 5e-5
    assert abs(b4[30]) < abs(b1[30]) / 15


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
    for L in (2, 4):
        run("toqb.kising_charge", "build", F, R, "--arm", "fold:rule", "--n", "8", "--L", str(L), "--shots", "400")
    run("toqb.lam_device", "build", F, R, "--arm", "fold:rule", "--n", "8", "--L", "2", "--kind", "kising",
        "--twin", "none", "--P", "8", "--shots", "400")
    run("toqb.s2rc_device", "assemble", "--fetch", F, "--runs", R, "--out", J, "--max-seconds", "60")
    run("toqb.s2rc_device", "submit", "--job", J, "--local")
    out = run("toqb.lam_device", "score", J, R)
    assert "kising_n8_L2" in out and "kcharge" not in out
    out = run("toqb.kising_charge", "score", J, R, "--p", "0.0051", "--p2-job", J, "--p2-runs", R)
    res = json.load(open(os.path.join(J, "charge_score.json")))
    assert len(res["cells"]) == 2 and len(res["p1_verdicts"]) == 2 and len(res["p2"]) == 1
    for c in res["cells"]:
        assert 0.3 < c["rho4"] < 1.2 and c["se4"] > 0
