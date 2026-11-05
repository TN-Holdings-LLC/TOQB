"""daily/pool.py and gpu/daily_answers.py (numpy backend) on small patches: the whole-state evolution against Qiskit's
Statevector, the light cones against the whole state, and the pool's data against the task's table. The GPU backend is
checked the same way on the pod before any answer is sealed (gpu/daily_pod.sh)."""
import importlib.util
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "gpu"))
sys.path.insert(0, os.path.join(HERE, ".."))
import daily_answers as A  # noqa: E402
import practice_circuits as PC  # noqa: E402

from daily import pool as P  # noqa: E402

# a small heavy-hex patch (rows 0-1, columns 0-4 and bridge 16), relabelled 0..10 so Statevector stays small
_QS = P._block(range(2), range(5))
_M = {q: k for k, q in enumerate(_QS)}
QS = list(range(len(_QS)))
ES = sorted(tuple(sorted((_M[a], _M[b]))) for a, b in P.heron_r2_edges() if a in _M and b in _M)
SMALL = {
    "F1": lambda t: P.f1(t, 0.53, 1.0, QS, ES),
    "F1c": lambda t: P.f1(t, 0.8, -np.pi / 2, QS, ES),
    "F2": lambda t: P.f2(t, 0.8, QS, ES),
    "F3": lambda t: P.circuit("F3", "C33", dict(h=0.3, b=P.PI4 - 0.15), t, chain=range(9)),
}


def _reference(qc):
    from qiskit.quantum_info import Pauli, Statevector
    ops, readout, basis = A.program(qc)
    sv = Statevector(qc.remove_final_measurements(inplace=False))
    n = qc.num_qubits
    # the circuit already ends with H on every site when basis is X: Z after it is X before it
    return {q: float(sv.expectation_value(Pauli("I" * (n - 1 - q) + "Z" + "I" * q)).real) for q in readout}


@pytest.mark.parametrize("fam", sorted(SMALL))
def test_full_matches_statevector(fam):
    ts = [1, 2, 3, 4]
    r = A.full({t: SMALL[fam](t) for t in ts})
    for t in ts:
        ref = _reference(SMALL[fam](t))
        assert set(r["values"][t]) == set(ref)
        assert max(abs(r["values"][t][q] - ref[q]) for q in ref) < 1e-10
        assert abs(r["norm"][t] - 1) < 1e-10


@pytest.mark.parametrize("fam", sorted(SMALL))
def test_cones_match_full(fam):
    ts = [1, 2, 3, 5]
    r = A.full({t: SMALL[fam](t) for t in ts})
    for t in ts:
        c = A.cones(SMALL[fam](t))
        assert max(abs(c["values"][q] - r["values"][t][q]) for q in c["values"]) < 1e-10


def test_cone_widens_by_one_edge_per_step():
    # F1 and F2: <Z_q> after t steps depends on the ball of radius t - 1 (as psf_os.ising2d.cone)
    from psf_os import ising2d as I
    qs, es = P.patch("P32")
    for fam in ("F1", "F2"):
        par = dict(theta_x=0.53, theta_zz=1.0) if fam == "F1" else dict(theta=0.8)
        for t in (1, 2, 3):
            s = A.cone_sizes(P.circuit(fam, "P32", par, t))
            assert all(s[q] == len(I.ball(q, t - 1, es)) for q in qs)


def test_numpy_rzz_and_z():
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Pauli, Statevector
    qc = QuantumCircuit(3)
    qc.rx(0.7, 0)
    qc.rx(1.1, 2)
    qc.rzz(0.9, 0, 2)
    qc.rx(0.4, 2)
    sv = A.NumpyDaily(3, np.complex128)
    sv.one(0, A.program(qc)[0][0][2])
    sv.one(2, A.program(qc)[0][1][2])
    sv.rzz(0, 2, 0.9)
    sv.one(2, A.program(qc)[0][3][2])
    ref = Statevector(qc)
    assert np.allclose(sv.psi, ref.data, atol=1e-12)
    assert abs(sv.z(2) - ref.expectation_value(Pauli("ZII")).real) < 1e-12


def test_pool_table():
    assert len(P.POOL) == 32 and [e[0] for e in P.POOL] == [f"D{k:02d}" for k in range(1, 33)]
    for pid, fam, pa, par, t, layers, g in P.POOL + P.FIXED:
        assert P.cz_layers(fam, par, t) == layers and P.grade(layers) == g, pid
        assert P.READOUT[fam] == A.program(P.problem_circuit(pid))[2]


def test_patches():
    from psf_os import ising2d as I
    assert P.P32 == sorted(set(I.QUBITS) - set(P.P6_DROPPED))
    sizes = {n: tuple(map(len, P.patch(n))) for n in ("P32", "B42", "B72", "C33")}
    assert sizes == {"P32": (32, 32), "B42": (42, 45), "B72": (72, 79), "C33": (33, 32)}
    assert {16, 17, 18, 36, 37, 38} <= set(P.patch("B42")[0])
    spec = importlib.util.spec_from_file_location("s1a", os.path.join(HERE, "..", "notes", "s1_2026-11-05",
                                                                      "s1_analyse.py"))
    s1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s1)
    assert P.heron_r2_edges() == s1.heron_r2_edges()
    for n in ("P32", "B42", "B72", "C33"):
        assert set(P.patch(n)[1]) <= P.heron_r2_edges()


def test_f3_is_practice_p4():
    for t in (2, 5):
        a, b = P.circuit("F3", "C33", dict(h=PC.H, b=PC.KICKS["b0.485"]), t), PC.p4(t, PC.KICKS["b0.485"])
        sig = lambda c: [(i.operation.name, [c.find_bit(x).index for x in i.qubits], i.operation.params)  # noqa: E731
                         for i in c.data]
        assert sig(a) == sig(b)
