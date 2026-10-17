"""Tests of toqb/s2r.py (the stand-in device) and toqb/score_s2r.py (on synthetic records)."""
import json
import math
import os

import numpy as np
import pytest

from toqb import score_s2r as SC


# ------------------------------------------------------------------------------------------------ the stand-in

@pytest.fixture(scope="module")
def standin():
    from toqb.s2r import StandIn
    return StandIn(t12=0.3, over=0.0, zz_hz=2.0e5)  # a large ZZ, so that errors in the bookkeeping show


def _evolve_reference(standin, sc):
    """Independent reference: the noiseless state of the scheduled circuit's active qubits and their idle neighbours
    (in |0>), with H = sum over coupled pairs of (pi zz / 1) Z Z / 2 acting between the instants of the sx and x gates
    (each taken at its middle), all other gates applied at their start (they commute with H)."""
    from qiskit.quantum_info import Operator
    t = standin.target
    idx = {q: k for k, q in enumerate(sc.qubits)}
    active = sorted({idx[q] for i in sc.data if i.operation.name not in ("delay", "barrier") for q in i.qubits})
    spect = sorted({r for q in active for r in standin.nbr.get(q, ()) if r not in active})
    qs = active + spect
    pos = {q: k for k, q in enumerate(qs)}
    n = len(qs)
    pairs = [(a, b) for a, b in standin.edges if a in pos and b in pos]
    clock, ev = {}, []
    for j, ins in enumerate(sc.data):
        q_ = [idx[q] for q in ins.qubits]
        nm = ins.operation.name
        if nm == "delay":
            d = float(ins.operation.params[0]) * t.dt
        elif nm in ("barrier", "measure"):
            d = 0.0
        else:
            d = t[nm][tuple(q_)].duration or 0.0
        s = max(clock.get(q, 0.0) for q in q_)
        for q in q_:
            clock[q] = s + d
        if nm in ("delay", "barrier", "measure"):
            continue
        ev.append((s + d / 2 if nm in ("sx", "x") else s, j, ins.operation, q_))
    ev.sort(key=lambda e: (e[0], e[1]))
    psi = np.zeros(2 ** n, complex)
    psi[0] = 1
    b = np.arange(2 ** n)
    zz = np.zeros(2 ** n)
    for a, c in pairs:
        za = 1 - 2 * ((b >> pos[a]) & 1)
        zc = 1 - 2 * ((b >> pos[c]) & 1)
        zz += za * zc
    now = 0.0
    for tm, j, op, q_ in ev:
        psi = np.exp(-1j * math.pi * standin.params["zz_hz"] * (tm - now) * zz / 2) * psi
        now = tm
        U = Operator(op).data
        k = len(q_)
        tens = psi.reshape([2] * n)
        axes = [n - 1 - pos[q] for q in q_][::-1]
        tens = np.moveaxis(tens, axes, list(range(k)))
        sh = tens.shape
        tens = (U @ tens.reshape(2 ** k, -1)).reshape(sh)
        psi = np.moveaxis(tens, list(range(k)), axes).reshape(-1)
    return psi, qs


def test_crosstalk_matches_a_global_hamiltonian(standin):
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    qc = QuantumCircuit(156, 1)
    for q in (0, 1, 2):
        qc.sx(q)
    qc.cz(0, 1)
    qc.sx(1)
    qc.x(2)
    qc.delay(400, 2, unit="dt")
    qc.sx(0)
    qc.cz(1, 2)
    qc.sx(2)
    qc.rz(0.3, 1)
    qc.sx(1)
    qc.measure(0, 0)
    sc = standin.sched.run(qc)
    ref, qs = _evolve_reference(standin, sc)
    out = standin.with_crosstalk(sc)
    idx = {q: k for k, q in enumerate(out.qubits)}
    act = sorted({idx[q] for i in out.data if i.operation.name not in ("delay", "barrier", "measure") for q in i.qubits})
    assert act == [0, 1, 2]  # spectators enter only as RZ on the active qubits
    small = QuantumCircuit(3)
    for ins in out.data:
        if ins.operation.name in ("delay", "barrier", "measure"):
            continue
        small.append(ins.operation, [idx[q] for q in ins.qubits])
    got = Statevector(small).data
    # the reference carries the spectators (in |0>, untouched): its amplitudes with every spectator in 0
    ref_active = ref.reshape([2] * len(qs))
    ref_active = ref_active[(0,) * (len(qs) - 3) + (slice(None),) * 3].reshape(-1)
    ov = abs(np.vdot(ref_active, got))
    assert ov == pytest.approx(1.0, abs=1e-9)


def test_standin_without_mismatches_is_toqb_noise_on_its_target():
    from qiskit import QuantumCircuit
    from toqb.fast_noise import FastNoisyDevice
    from toqb.s2r import StandIn
    s0 = StandIn(t12=0.0, over=0.0, zz_hz=0.0)
    qc = QuantumCircuit(156, 1)
    qc.sx(0)
    qc.cz(0, 1)
    qc.sx(1)
    qc.cz(1, 0)
    qc.sx(0)
    qc.measure(0, 0)
    p_ref = FastNoisyDevice(s0.target).p1_of([qc])[0]
    r, nm = s0.prepared(qc)
    from qiskit_aer import AerSimulator
    body = r.copy_empty_like()
    for i in r.data:
        if i.operation.name != "measure":
            body.append(i.operation, i.qubits, i.clbits)
    body.save_density_matrix()
    dm = np.asarray(AerSimulator(method="density_matrix").run(body, noise_model=nm).result().data()["density_matrix"])
    p = float(np.real(sum(dm[i, i] for i in range(dm.shape[0]) if i & 1)))
    e = s0.target["measure"][(0,)].error
    assert p * (1 - e) + (1 - p) * e == pytest.approx(p_ref, abs=1e-8)  # Aer and the numpy engine: about 1e-9 apart


# ------------------------------------------------------------------------------------------------ the scorer

def _s2r(final, rho=0.5, loops=6):
    evals = [dict(loop=t, accuracy=a, sim_accuracy=a, noiseless_accuracy=a)
             for t, a in enumerate([0.3] * loops + [final])]
    return dict(valid=True, evals=evals, loops=[dict(spearman=rho)] * loops, spent_usd=180.0, version="v")


def _spsa(final):
    return dict(valid=True, evals=[dict(iteration=0, accuracy=0.3), dict(iteration=50, accuracy=final)],
                spent_usd=190.0, iterations=50, version="v")


def _write(root, seed, recs):
    d = os.path.join(root, f"seed{seed}")
    os.makedirs(d)
    for (kind, arm), rec in recs.items():
        json.dump(rec, open(os.path.join(d, SC._name(kind, arm)), "w"))


def test_score_direction(tmp_path):
    root = str(tmp_path)
    for s in range(1, 21):
        _write(root, s, {("s2r", SC.PSF): _s2r(0.70, 0.6), ("s2r", SC.QK): _s2r(0.65, 0.4),
                         ("spsa", SC.PSF): _spsa(0.5), ("spsa", SC.QK): _spsa(0.5)})
    rows = SC.collect(root, range(1, 21))
    res = SC.score(rows)
    assert res["S1"]["verdict"] == "CONFIRMED"
    assert res["S2"]["verdict"] == "CONFIRMED" and res["S2"]["mean_difference"] == pytest.approx(0.05)
    assert res["S3"]["verdict"] == "CONFIRMED"
    assert res["S4"]["verdict"] == "CONFIRMED"
    SC.report(rows, res, list(range(1, 21)))


def test_score_refuted_and_missing(tmp_path):
    root = str(tmp_path)
    for s in range(1, 21):
        recs = {("s2r", SC.PSF): _s2r(0.60), ("s2r", SC.QK): _s2r(0.65), ("spsa", SC.PSF): _spsa(0.7),
                ("spsa", SC.QK): _spsa(0.5)}
        if s == 3:
            recs.pop(("spsa", SC.QK))
        _write(root, s, recs)
    res = SC.score(SC.collect(root, range(1, 21)))
    assert res["S1"]["verdict"] == "REFUTED" and res["S1"]["not_valid"] == [(3, "spsa_qk")]
    assert res["S2"]["verdict"] == "REFUTED"
    assert res["S4"]["psf"]["verdict"] == "REFUTED" and res["S4"]["verdict"] == "REFUTED"


def test_never_overwrites(tmp_path):
    root = str(tmp_path)
    open(os.path.join(root, "score.md"), "w").write("x")
    assert SC.main([root]) == 2
