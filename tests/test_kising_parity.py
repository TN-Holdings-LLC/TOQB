"""toqb.kising_parity (2026-10-30, test 3's size probe): the global parity P = prod X_j is conserved by the circuit
itself for even n; the arms keep it after compilation with one structure; the estimator recovers it from sampled
counts; and the procedure runs end to end on a fake device."""
import json
import os
import subprocess
import sys

import numpy as np
import pytest

pytest.importorskip("qiskit")
from qiskit import QuantumCircuit  # noqa: E402
from qiskit.quantum_info import SparsePauliOp, Statevector  # noqa: E402

from toqb import kising_parity as KP  # noqa: E402
from toqb import s2r as S  # noqa: E402
from toqb.devices import get_device  # noqa: E402

TARGET = "file:data/targets/ibm_kingston_2026-10-24.pkl"
H = 0.6


@pytest.mark.parametrize("n", [6, 8])
def test_parity_is_conserved_by_the_circuit(n):
    Pz = SparsePauliOp("Z" * n)  # every qubit is read in X: the parity of the measured bits is prod X_j
    for name in KP.INPUTS:
        for L in range(1, 6):
            qc = KP.circuit(KP.input_signs(name, n), n, L, H).remove_final_measurements(inplace=False)
            assert abs(Statevector(qc).expectation_value(Pz).real - KP.SIGN[name]) < 1e-10


def test_parity_is_conserved_at_odd_n_too():
    n = 7  # the circuit conserves P at odd n as well; the probe still uses even n (input pairing)
    Pz = SparsePauliOp("Z" * n)
    for L in (1, 2, 3):
        qc = KP.circuit([1] * n, n, L, H).remove_final_measurements(inplace=False)
        assert abs(Statevector(qc).expectation_value(Pz).real - 1) < 1e-10


def _compiled_counts(c):
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
    probs = Statevector(s).probabilities([meas[k] for k in sorted(meas)])
    nm = len(meas)
    return {format(k, f"0{nm}b"): float(p) * 1e6 for k, p in enumerate(probs) if p > 1e-14}


@pytest.mark.parametrize("arm_name", ["fold:rule", "fold:zipcyc", "qiskit:2:blind:template"])
def test_compiled_arms_keep_the_parity_with_one_structure(arm_name):
    n, L = 8, 3
    arm = S.Arm(arm_name, get_device(TARGET))
    sigs, cs = set(), []
    for name in KP.INPUTS:
        c = arm.compile(KP.circuit(KP.input_signs(name, n), n, L, H))
        cs.append(c)
        m, _ = KP.parity_value(_compiled_counts(c), n)
        assert abs(m - KP.SIGN[name]) < 1e-8
        sigs.add(tuple((x.operation.name, tuple(c.find_bit(q).index for q in x.qubits)) for x in c.data))
    assert len(sigs) == 1
    for r in KP.REFS:
        rc, _ = KP.KC.reference_circuit(cs[0], KP.ref_bits(r, n))
        m, _ = KP.parity_value(_compiled_counts(rc), n)
        assert abs(m - KP.ref_sign(r, n)) < 1e-9
    assert arm.on_failed_ops == 0 and arm.structural_fail == 0


def test_estimator_and_vstar_fit():
    rng = np.random.default_rng(3)
    n, S_ = 10, 200000

    def counts(p_value, sign):
        # bit strings of n bits whose parity is +1 with probability (1 + sign p) / 2
        k = rng.binomial(S_, (1 + sign * p_value) / 2)
        even, odd = "0" * n, "1" + "0" * (n - 1)
        return {even: k, odd: S_ - k}
    lam, ro = 0.6, 0.8  # true damping and a multiplicative readout loss
    cc = {i: counts(lam * ro, KP.SIGN[i]) for i in KP.INPUTS}
    cc.update({r: counts(ro, KP.ref_sign(r, n)) for r in KP.REFS})
    e = KP.estimate(cc, n)
    assert abs(e["rho"] - lam) < 4 * e["se"] and e["se"] < 0.01
    V = 150.0
    cells = [dict(arm="fold:rule", n=20, L=L, rho=float(np.exp(-20 * L / V)), se=0.01) for L in (2, 4, 8)]
    f = KP.vstar_fit(cells)[0]
    assert abs(f["V_star"] - V) < 1e-2 * V
    j = KP.judge([f], {"fold:rule": 160.0})[0]
    assert j["verdict"] == "INSIDE"
    assert KP.judge([f], {"fold:rule": 300.0})[0]["verdict"] == "BELOW"


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
    for L in (1, 2):
        run("toqb.kising_parity", "build", F, R, "--arm", "fold:rule", "--n", "8", "--L", str(L), "--shots", "400")
    run("toqb.kising_parity", "rehearse", R, "--vstar", "fold:rule=150")
    run("toqb.s2rc_device", "assemble", "--fetch", F, "--runs", R, "--out", J, "--max-seconds", "60")
    run("toqb.s2rc_device", "submit", "--job", J, "--local")
    run("toqb.kising_parity", "score", J, R, "--vstar-pred", "fold:rule=150", "--judged-n", "8")
    res = json.load(open(os.path.join(J, "parity_score.json")))
    assert len(res["cells"]) == 2 and len(res["fits"]) == 1 and len(res["verdicts"]) == 1
    for c in res["cells"]:
        assert -0.2 < c["rho"] < 1.3 and c["se"] > 0
