"""Exact answers for IBM's 2023 utility observables on the Eagle graph (home, 2026-11-10; prototype, not declared).

Circuit (Kim et al., Nature 618, 500): |0...0>, t steps; each step R_X(theta_h) on every qubit, then
R_ZZ(theta_J = -pi/2) = exp(+i pi/4 ZZ) on every edge (they commute); Pauli observables measured after the last
step (an optional extra R_X layer: Fig. 4a).

Method: exact Heisenberg-picture Pauli propagation, no truncation. The observable is a Pauli string; each R_ZZ is
Clifford (a Pauli goes to one Pauli, sign tracked), each R_X splits a Pauli with Y or Z on that qubit into two. After
all layers <0|P|0> = 1 for strings of I and Z only, else 0. The conjugation tables are built numerically from the
gates' matrices (no hand-derived sign), and the whole method is checked against statevectors on small cones.

usage: python gpu/utility_exact.py check
       python gpu/utility_exact.py w10 THETA [--t 5]      (prints the exact value and the number of terms per layer)
"""
import itertools
import math
import sys

import numpy as np

I2 = np.eye(2)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]])
Z = np.diag([1.0, -1.0]).astype(complex)
P1 = {"I": I2, "X": X, "Y": Y, "Z": Z}
LETTERS = "IXYZ"
W10 = {13: "X", 29: "X", 31: "X", 9: "Y", 30: "Y", 8: "Z", 12: "Z", 17: "Z", 28: "Z", 32: "Z"}
W17 = {**{q: "X" for q in (37, 41, 52, 56, 57, 58, 62, 79)}, 75: "Y",
       **{q: "Z" for q in (38, 40, 42, 63, 72, 80, 90, 91)}}


def eagle_edges():
    from qiskit_ibm_runtime import fake_provider as fp
    return sorted({tuple(sorted(e)) for e in fp.FakeSherbrooke().configuration().coupling_map})


def _decompose(M, n):
    """M = sum_P c_P P over n-qubit Pauli strings (letters)."""
    out = {}
    for s in itertools.product(LETTERS, repeat=n):
        P = P1[s[0]]
        for c in s[1:]:
            P = np.kron(P, P1[c])
        c = np.trace(P.conj().T @ M) / 2 ** n
        if abs(c) > 1e-12:
            out["".join(s)] = c
    return out


def rx_table(theta):
    """U^dag P U for U = R_X(theta): {letter: {letter: coefficient}}."""
    U = np.cos(theta / 2) * I2 - 1j * np.sin(theta / 2) * X
    return {p: _decompose(U.conj().T @ P1[p] @ U, 1) for p in LETTERS}


def zz_table(theta_j=-math.pi / 2):
    """U^dag (P_a P_b) U for U = R_ZZ(theta_j) = exp(-i theta_j / 2 ZZ): {pair: (pair, sign)} (Clifford)."""
    ZZ = np.kron(Z, Z)
    U = np.cos(theta_j / 2) * np.eye(4) - 1j * np.sin(theta_j / 2) * ZZ
    out = {}
    for a, b in itertools.product(LETTERS, repeat=2):
        d = _decompose(U.conj().T @ np.kron(P1[a], P1[b]) @ U, 2)
        assert len(d) == 1, d
        (k, v), = d.items()
        assert abs(abs(v) - 1) < 1e-12
        out[a + b] = (k, v)
    return out


def propagate(obs, edges, theta, t, extra_rx=False, n=127):
    """Exact <0| U^dag P U |0> with the term count after each layer. obs: {qubit: letter}."""
    rx, zz = rx_table(theta), zz_table()
    terms = {tuple("I" if q not in obs else obs[q] for q in range(n)): 1.0 + 0j}
    counts = []

    def apply_rx(terms):
        out = {}
        for s, w in terms.items():
            branches = [(list(s), w)]
            for q, c in enumerate(s):
                if c in "YZ":
                    nb = []
                    for b, bw in branches:
                        for l2, cf in rx[c].items():
                            b2 = b.copy()
                            b2[q] = l2
                            nb.append((b2, bw * cf))
                    branches = nb
            for b, bw in branches:
                k = tuple(b)
                out[k] = out.get(k, 0) + bw
        return {k: v for k, v in out.items() if abs(v) > 1e-15}

    def apply_zz(terms):
        out = {}
        for s, w in terms.items():
            b = list(s)
            for a, c in edges:
                if b[a] == "I" and b[c] == "I":
                    continue
                k, v = zz[b[a] + b[c]]
                b[a], b[c] = k[0], k[1]
                w = w * v
            k = tuple(b)
            out[k] = out.get(k, 0) + w
        return out

    if extra_rx:
        terms = apply_rx(terms)
        counts.append(len(terms))
    for _ in range(t):          # backwards: the last step's ZZ first, then its RX
        terms = apply_zz(terms)
        terms = apply_rx(terms)
        counts.append(len(terms))
    val = sum(w for s, w in terms.items() if all(c in "IZ" for c in s))
    return float(np.real(val)), counts


def statevector_value(obs, edges, theta, t, extra_rx=False):
    """The same quantity by a statevector on the ball of radius t around the observable (small cases only)."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp, Statevector
    import rustworkx as rx_
    g = rx_.PyGraph()
    g.add_nodes_from(range(127))
    g.add_edges_from_no_data(edges)
    D = rx_.distance_matrix(g)
    ball = sorted(q for q in range(127) if min(D[q][s] for s in obs) <= t)
    pos = {q: i for i, q in enumerate(ball)}
    e_in = [(a, b) for a, b in edges if a in pos and b in pos]
    qc = QuantumCircuit(len(ball))
    for _ in range(t):
        for q in ball:
            qc.rx(theta, pos[q])
        for a, b in e_in:
            qc.rzz(-math.pi / 2, pos[a], pos[b])
    if extra_rx:
        for q in ball:
            qc.rx(theta, pos[q])
    label = ["I"] * len(ball)
    for q, c in obs.items():
        label[len(ball) - 1 - pos[q]] = c
    return float(np.real(Statevector(qc).expectation_value(SparsePauliOp("".join(label))))), len(ball)


def check():
    edges = eagle_edges()
    worst = 0.0
    cases = [({106: "Z"}, 2), ({106: "Z"}, 3), ({13: "X", 9: "Y", 8: "Z"}, 2), ({62: "Z", 63: "Y"}, 2),
             ({13: "X", 29: "X", 9: "Y", 8: "Z", 12: "Z"}, 1)]
    for obs, t in cases:
        for theta in (0.3, 0.9, math.pi / 2):
            for extra in (False, True):
                a, _ = propagate(obs, edges, theta, t, extra)
                b, nb = statevector_value(obs, edges, theta, t, extra)
                worst = max(worst, abs(a - b))
    print(f"Pauli propagation against statevector (cones up to {nb} qubits, theta 0.3 / 0.9 / pi/2, with and "
          f"without the extra RX): worst {worst:.2e}")
    return worst < 1e-10


if __name__ == "__main__":
    if sys.argv[1:2] == ["check"]:
        sys.exit(0 if check() else 1)
    if sys.argv[1:2] == ["w10"]:
        th = float(sys.argv[2])
        t = int(sys.argv[sys.argv.index("--t") + 1]) if "--t" in sys.argv else 5
        import time
        t0 = time.time()
        v, c = propagate(W10, eagle_edges(), th, t)
        print(f"w10 theta {th} t {t}: {v:+.6f}  terms per layer {c}  {time.time() - t0:.1f} s")


def tn_value(obs, edges, theta, t, extra_rx=False, optimize="auto-hq"):
    """The same quantity by exact tensor-network contraction (quimb) of the circuit on the ball of radius t around
    the observable: <psi| P |psi> with P the tensor product of the observable's single-qubit Paulis."""
    import quimb as qu
    import quimb.tensor as qtn
    import rustworkx as rx_
    g = rx_.PyGraph()
    g.add_nodes_from(range(127))
    g.add_edges_from_no_data(edges)
    D = rx_.distance_matrix(g)
    ball = sorted(q for q in range(127) if min(D[q][s] for s in obs) <= t)
    pos = {q: i for i, q in enumerate(ball)}
    e_in = [(a, b) for a, b in edges if a in pos and b in pos]
    circ = qtn.Circuit(len(ball))
    for _ in range(t):
        for q in ball:
            circ.apply_gate("RX", theta, pos[q])
        for a, b in e_in:
            circ.apply_gate("RZZ", -math.pi / 2, pos[a], pos[b])
    if extra_rx:
        for q in ball:
            circ.apply_gate("RX", theta, pos[q])
    where = tuple(pos[q] for q in sorted(obs))
    G = qu.kron(*[qu.pauli(obs[q]) for q in sorted(obs)])
    v = circ.local_expectation(G, where, optimize=optimize, simplify_sequence="ADCRS")
    return float(np.real(v)), len(ball)


def tn_value_product(obs, edges, theta, t, extra_rx=False, optimize="auto-hq"):
    """As tn_value, for heavy observables: <psi| (prod_q P_q) |psi> as one network, the Paulis applied as
    single-qubit tensors on a copy of the ket (no dense operator)."""
    import quimb.tensor as qtn
    import rustworkx as rx_
    g = rx_.PyGraph()
    g.add_nodes_from(range(127))
    g.add_edges_from_no_data(edges)
    D = rx_.distance_matrix(g)
    ball = sorted(q for q in range(127) if min(D[q][s] for s in obs) <= t)
    pos = {q: i for i, q in enumerate(ball)}
    e_in = [(a, b) for a, b in edges if a in pos and b in pos]

    def build(with_obs):
        c = qtn.Circuit(len(ball))
        for _ in range(t):
            for q in ball:
                c.apply_gate("RX", theta, pos[q])
            for a, b in e_in:
                c.apply_gate("RZZ", -math.pi / 2, pos[a], pos[b])
        if extra_rx:
            for q in ball:
                c.apply_gate("RX", theta, pos[q])
        if with_obs:
            for q, l in obs.items():
                c.apply_gate(P1[l], pos[q])
        return c.psi
    ket, opket = build(False), build(True)
    v = (ket.H & opket).contract(all, optimize=optimize)
    return float(np.real(v)), len(ball)
