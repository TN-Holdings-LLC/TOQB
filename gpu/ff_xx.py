"""A second ruler exact at any size (home, 2026-11-10; prototype, not declared): the Trotterised XX chain.

Circuit (logical, N qubits in a line): start in a computational-basis product state (default Neel |0101...>); per
step, the gate G(theta) = exp(-i theta (XX + YY) / 2) on the even bonds (0,1), (2,3), ..., then on the odd bonds
(1,2), (3,4), ... (open chain). Each G is a Givens rotation of the Jordan-Wigner fermions (a matchgate), so the whole
Trotter circuit, not only the continuous evolution, maps every creation operator linearly:
c_j^dag -> sum_k U_kj c_k^dag with U the product of 2 x 2 blocks [[cos theta, -i sin theta], [-i sin theta, cos theta]].
A product state with occupied set O is a Slater determinant, so <n_i> = sum_{j in O} |U_ij|^2 and <Z_i> = 1 - 2 <n_i>,
exactly, for any N, in O(N^2 steps) time. Observables: <Z_i> per site and the imbalance I = (1/N) sum_i (-1)^i <Z_i>.

Each G costs two CZ (it is an iSWAP-family gate): CZ per step = 2 (N - 1).

usage: python gpu/ff_xx.py check     (exact against Qiskit's statevector for N up to 14)
"""
import sys

import numpy as np


def single_particle(N, steps, theta):
    """The N x N single-particle matrix of the Trotter circuit (rows: final mode, columns: initial mode)."""
    c, s = np.cos(theta), np.sin(theta)
    block = np.array([[c, -1j * s], [-1j * s, c]])
    U = np.eye(N, dtype=complex)
    for _ in range(steps):
        for start in (0, 1):
            layer = np.eye(N, dtype=complex)
            for a in range(start, N - 1, 2):
                layer[a:a + 2, a:a + 2] = block
            U = layer @ U
    return U


def z_exact(N, steps, theta, occupied=None):
    """<Z_i>, i = 0..N-1, of the Trotter circuit from the product state with the given occupied sites
    (default Neel: the odd sites hold a 1, i.e. |0101...> with qubit 0 first)."""
    occ = list(range(1, N, 2)) if occupied is None else list(occupied)
    U = single_particle(N, steps, theta)
    n = np.sum(np.abs(U[:, occ]) ** 2, axis=1)
    return 1 - 2 * n


def imbalance(z):
    return float(np.mean([(-1) ** i * v for i, v in enumerate(z)]))


def circuit(N, steps, theta, occupied=None, measure=True):
    """The logical circuit: X on the occupied sites, then the brickwork of G(theta) as two CZ each."""
    from qiskit import QuantumCircuit
    occ = list(range(1, N, 2)) if occupied is None else list(occupied)
    qc = QuantumCircuit(N, N if measure else 0)
    for q in occ:
        qc.x(q)
    for _ in range(steps):
        for start in (0, 1):
            for a in range(start, N - 1, 2):
                xxyy(qc, theta, a, a + 1)
    if measure:
        qc.measure(range(N), range(N))
    return qc


_GATE = {}


def xxyy(qc, theta, a, b):
    """exp(-i theta (XX + YY) / 2) on (a, b) with two CZ: Qiskit's XXPlusYYGate(2 theta), decomposed once per theta
    into cz / rz / sx / x (KAK: one Weyl coordinate is zero, so two CZ suffice); checked against the matrix in
    `check`."""
    if theta not in _GATE:
        from qiskit import QuantumCircuit, transpile
        from qiskit.circuit.library import XXPlusYYGate
        g = QuantumCircuit(2)
        g.append(XXPlusYYGate(2 * theta), [0, 1])
        _GATE[theta] = transpile(g, basis_gates=["cz", "rz", "sx", "x"], optimization_level=3)
        assert _GATE[theta].count_ops().get("cz", 0) == 2, _GATE[theta].count_ops()
    qc.compose(_GATE[theta], qubits=[a, b], inplace=True)


def gate_error(theta):
    """max |entry| of (circuit unitary) - (target) up to a global phase, for the two-qubit gate."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Operator
    qc = QuantumCircuit(2)
    xxyy(qc, theta, 0, 1)
    U = Operator(qc).data
    X = np.array([[0, 1], [1, 0]])
    Y = np.array([[0, -1j], [1j, 0]])
    H = (np.kron(X, X) + np.kron(Y, Y)) / 2
    w, v = np.linalg.eigh(H)
    T = v @ np.diag(np.exp(-1j * theta * w)) @ v.conj().T
    k = np.argmax(np.abs(T))
    ph = U.flat[k] / T.flat[k]
    return float(np.max(np.abs(U - ph * T)))


def check():
    from qiskit.quantum_info import Statevector
    worst_gate = max(gate_error(t) for t in (0.1, 0.37, 0.785, 1.3))
    print(f"two-qubit gate against exp(-i theta (XX+YY)/2): worst {worst_gate:.2e}")
    worst = 0.0
    for N in (4, 7, 10, 14):
        for steps in (1, 3, 6):
            for theta in (0.2, 0.6):
                qc = circuit(N, steps, theta, measure=False)
                sv = Statevector(qc)
                z_sv = np.array([1 - 2 * sv.probabilities([q])[1] for q in range(N)])
                worst = max(worst, float(np.max(np.abs(z_sv - z_exact(N, steps, theta)))))
    print(f"<Z_i> exact (free fermions) against statevector, N 4-14, steps 1-6: worst {worst:.2e}")
    for N in (51, 91, 151):
        z = z_exact(N, 24, 0.25)
        print(f"N {N}, 24 steps, theta 0.25: imbalance {imbalance(z):+.4f}, CZ {2 * (N - 1) * 24}")
    return worst_gate < 1e-10 and worst < 1e-10


if __name__ == "__main__":
    if sys.argv[1:] == ["check"]:
        sys.exit(0 if check() else 1)
    print(__doc__)
