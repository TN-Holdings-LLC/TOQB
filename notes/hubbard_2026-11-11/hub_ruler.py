"""Hubbard Trotter circuit at U = 0 as a ruler exact at any size: every gate (FSWAP, XX+YY hopping, RZ) is a matchgate,
so the circuit maps the 2L Jordan-Wigner modes linearly; <n_k> = sum_{j occupied} |W_kj|^2. Checked against the
statevector; CZ counts of the U = 0 and U > 0 circuits compared. Also: from the Neel start (one fermion per site,
spins alternating) the charge on every site stays exactly 1 at any U (particle-hole with spin flip), so
Z_up(i) + Z_dn(i) = 0 per site is a raw check for the device (recorded, never used to correct)."""
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import XXPlusYYGate
from qiskit.quantum_info import Statevector
from qiskit.transpiler import CouplingMap

J, dt = 1.0, 0.25


def circ(L, steps, U):
    qc = QuantumCircuit(2 * L)
    for i in range(L):
        qc.x(2 * i + (i % 2))
    for _ in range(steps):
        if U:
            for i in range(L):
                qc.rzz(U * dt / 2, 2 * i, 2 * i + 1); qc.rz(-U * dt / 2, 2 * i); qc.rz(-U * dt / 2, 2 * i + 1)
        for par in (0, 1):
            for i in range(par, L - 1, 2):
                qc.swap(2 * i + 1, 2 * i + 2); qc.cz(2 * i + 1, 2 * i + 2)
                qc.append(XXPlusYYGate(-2 * J * dt), [2 * i, 2 * i + 1])
                qc.append(XXPlusYYGate(-2 * J * dt), [2 * i + 2, 2 * i + 3])
                qc.swap(2 * i + 1, 2 * i + 2); qc.cz(2 * i + 1, 2 * i + 2)
    return qc


def ruler_z(L, steps):
    n = 2 * L
    W = np.eye(n, dtype=complex)
    a = J * dt                          # XXPlusYYGate(-2 J dt) = exp(+i J dt/2 (XX+YY)) -> Givens angle -J dt
    g = np.array([[np.cos(a), 1j * np.sin(a)], [1j * np.sin(a), np.cos(a)]])
    sw = np.array([[0, 1], [1, 0]], dtype=complex)

    def apply(M, p):
        G = np.eye(n, dtype=complex); G[p:p + 2, p:p + 2] = M
        return G

    for _ in range(steps):
        for par in (0, 1):
            for i in range(par, L - 1, 2):
                W = apply(sw, 2 * i + 1) @ W
                W = apply(g, 2 * i) @ W
                W = apply(g, 2 * i + 2) @ W
                W = apply(sw, 2 * i + 1) @ W
    occ = [2 * i + (i % 2) for i in range(L)]
    return 1 - 2 * np.sum(np.abs(W[:, occ]) ** 2, axis=1)


worst = 0
for L in (2, 3, 4, 5):
    for s in (1, 2, 3, 4):
        p = Statevector(circ(L, s, 0)).probabilities()
        idx = np.arange(len(p))
        z = np.array([np.sum(p * (1 - 2 * ((idx >> k) & 1))) for k in range(2 * L)])
        worst = max(worst, float(np.max(np.abs(z - ruler_z(L, s)))))
print("U = 0 ruler against statevector, L 2-5, steps 1-4: worst", f"{worst:.1e}")
w = 0
for L in (3, 4, 5):
    for s in (1, 3, 5):
        p = Statevector(circ(L, s, 4.0)).probabilities()
        idx = np.arange(len(p))
        z = np.array([np.sum(p * (1 - 2 * ((idx >> k) & 1))) for k in range(2 * L)])
        w = max(w, float(np.max(np.abs(z[0::2] + z[1::2]))))
print("U = 4, L 3-5, steps 1/3/5: per-site charge check |Z_up + Z_dn| worst", f"{w:.1e}")
for L in (20, 30, 45):
    cm = CouplingMap.from_line(2 * L)
    out = []
    for U in (0, 4.0):
        t = transpile(circ(L, 1, U), coupling_map=cm, basis_gates=["cz", "rz", "sx", "x"], optimization_level=1,
                      initial_layout=list(range(2 * L)), routing_method="none", seed_transpiler=0)
        out.append((t.count_ops().get("cz", 0), t.depth(lambda i: i.operation.name == "cz")))
    import time; t0 = time.time(); zr = ruler_z(L, 8); dt_r = time.time() - t0
    print(f"L {L} ({2*L} qubits): CZ / CZ layers per step U=0 {out[0]}, U=4 {out[1]}; ruler at 8 steps in {dt_r:.2f} s")
