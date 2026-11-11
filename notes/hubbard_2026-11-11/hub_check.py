"""Exactness check of the fermionic-swap Trotter step against exp(-i dt H_U) exp(-i dt H_even) exp(-i dt H_odd)
for the 1D Fermi-Hubbard model, H = -J sum_{i,s} (c+_{i s} c_{i+1 s} + h.c.) + U sum_i n_{i up} n_{i dn},
Jordan-Wigner in the interleaved order (u0 d0 u1 d1 ...)."""
import numpy as np
from scipy.linalg import expm
from qiskit import QuantumCircuit
from qiskit.circuit.library import XXPlusYYGate
from qiskit.quantum_info import Operator, SparsePauliOp

L, J, U, dt = 3, 1.0, 4.0, 0.25
n = 2 * L


def lowering(k):
    """c_k = Z..Z (X + iY)/2 on mode k (JW, mode k = qubit k)."""
    lab = ["I"] * n
    for j in range(k):
        lab[j] = "Z"
    a = lab.copy(); a[k] = "X"
    b = lab.copy(); b[k] = "Y"
    return SparsePauliOp(["".join(reversed(a)), "".join(reversed(b))], [0.5, 0.5j])


c = [lowering(k) for k in range(n)]
cd = [x.adjoint() for x in c]
num = [(cd[k] @ c[k]).simplify() for k in range(n)]
HU = sum((U * num[2 * i] @ num[2 * i + 1] for i in range(L)), SparsePauliOp("I" * n, 0)).simplify()


def hop(bonds):
    h = SparsePauliOp("I" * n, 0)
    for i in bonds:
        for s in (0, 1):
            a, b = 2 * i + s, 2 * i + 2 + s
            h = h + (-J) * (cd[a] @ c[b] + cd[b] @ c[a])
    return h.simplify()


He, Ho = hop(range(0, L - 1, 2)), hop(range(1, L - 1, 2))
M = lambda h: expm(-1j * dt * h.to_matrix())
target = M(Ho) @ M(He) @ M(HU)   # U first, then even, then odd

qc = QuantumCircuit(n)
for i in range(L):
    qc.rzz(U * dt / 2, 2 * i, 2 * i + 1)
    qc.rz(-U * dt / 2, 2 * i)
    qc.rz(-U * dt / 2, 2 * i + 1)
for par in (0, 1):
    for i in range(par, L - 1, 2):
        qc.swap(2 * i + 1, 2 * i + 2); qc.cz(2 * i + 1, 2 * i + 2)
        qc.append(XXPlusYYGate(-2 * J * dt), [2 * i, 2 * i + 1])
        qc.append(XXPlusYYGate(-2 * J * dt), [2 * i + 2, 2 * i + 3])
        qc.swap(2 * i + 1, 2 * i + 2); qc.cz(2 * i + 1, 2 * i + 2)
V = Operator(qc).data
f = abs(np.trace(V.conj().T @ target)) / 2 ** n
print(f"L {L} ({n} qubits): |Tr(V^dag T)|/d = {f:.15f}, 1 - f = {1 - f:.1e}")
