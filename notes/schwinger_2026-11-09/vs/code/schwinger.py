"""Schwinger model candidates (DRAFT, not declared; home, 2026-11-09). Real-time pair production from the bare vacuum,
as a user circuit for psf-os run2d, answers exact (the Trotter circuit's own output), no correction.

Model (standard form, Martinez et al., Nature 534, 516 (2016), arXiv:1605.04570, Eq. (1) and Box I): Kogut-Susskind
staggered fermions, open boundary, gauge field eliminated by Gauss's law, Jordan-Wigner; sites n = 1..N (N even):
    H = w sum_{n<N} (s+_n s-_{n+1} + h.c.) + (m/2) sum_n (-1)^n Z_n + J sum_{n<N} L_n^2,
    L_n = eps0 + 1/2 sum_{k<=n} (Z_k + (-1)^k).
Expanded (constants dropped, a global phase):
    s+s- + h.c. = (XX + YY) / 2
    J sum_n L_n^2 -> sum_{k<l} A_kl Z_k Z_l + sum_k hJ_k Z_k,  A_kl = (J/2)(N - l),  hJ_k = J sum_{n=k}^{N-1} c_n,
    c_n = eps0 + 1/2 sum_{k<=n} (-1)^k.
Bare vacuum: (-1)^n Z_n = -1 on every site (odd sites Z = +1, even sites Z = -1, i.e. X on the even sites); nu = 0.
Observables: <Z_n> per site and nu = (1/2N) sum_n (1 + (-1)^n <Z_n>); readout Z only.

Circuit: first-order Trotter, fixed dt; per step the single-Z layer (RZ on the qubit holding each site), then the swap
network: N layers of neighbour gates on the chain positions (even pairs, odd pairs, alternating), each gate
SWAP . exp(-i dt [A_ab ZZ + (w/2)(XX + YY) if |a - b| = 1]) on the sites (a, b) it holds; every pair of sites meets once
per step. The gate is the canonical gate Can(pi/4 - dt w/2 [adjacent], same, pi/4 - dt A_ab), written with 3 CX
(Vatan-Williams), checked against the matrix in tests. Even steps run the layers in reverse order. The site -> qubit
map is tracked; site n is measured into clbit n - 1.
"""
from __future__ import annotations

import numpy as np

# parameter sets (all from Martinez et al. 2016): (name, w, J, m, eps0)
PARAMS = [
    ("M1", 1.0, 1.0, 0.5, 0.0),   # Fig. 2(a): J = w, m = 0.5 w
    ("M2", 1.0, 1.0, 0.0, 0.0),   # Fig. 3: m = 0, J = w
    ("M3", 1.0, 2.0, 0.0, 0.0),   # Fig. 3: m = 0, J = 2 w
]
DT = 0.25          # fixed time step, in units of 1/w (fixed before any answer was computed)
NS = (6, 8, 10, 12)
STEPS = tuple(range(1, 9))


def couplings(n, w, J, m, eps0):
    """(A[k][l] for k < l (1-based dict), h[k], hop) of the expanded Hamiltonian."""
    c = {nn: eps0 + 0.5 * sum((-1) ** k for k in range(1, nn + 1)) for nn in range(1, n)}
    A = {(k, l): 0.5 * J * (n - l) for k in range(1, n + 1) for l in range(k + 1, n + 1)}
    h = {k: 0.5 * m * (-1) ** k + J * sum(c[nn] for nn in range(k, n)) for k in range(1, n + 1)}
    return A, h, 0.5 * w


def hamiltonian(n, w, J, m, eps0):
    """Dense H (2^n) of the expanded form; qubit k-1 <-> site k (qiskit little-endian)."""
    from qiskit.quantum_info import SparsePauliOp
    A, h, hop = couplings(n, w, J, m, eps0)
    terms = [("ZZ", [k - 1, l - 1], a) for (k, l), a in A.items() if a != 0]
    terms += [("Z", [k - 1], v) for k, v in h.items() if v != 0]
    terms += [(p, [k - 1, k], hop) for k in range(1, n) for p in ("XX", "YY")]
    return SparsePauliOp.from_sparse_list(terms, num_qubits=n).to_matrix()


def hamiltonian_direct(n, w, J, m, eps0):
    """Dense H from the unexpanded form (L_n as operators), for the test of the expansion."""
    I2, Z, X, Y = np.eye(2), np.diag([1.0, -1.0]), np.array([[0, 1], [1, 0]]), np.array([[0, -1j], [1j, 0]])

    def op(single, k):  # site k (1-based) <-> qubit k-1, little-endian: kron from the highest qubit down
        mats = [single if q == k - 1 else I2 for q in range(n)]
        out = np.array([[1.0]])
        for mtx in reversed(mats):
            out = np.kron(out, mtx)
        return out
    dim = 2 ** n
    H = np.zeros((dim, dim), complex)
    for k in range(1, n):
        H += w * 0.5 * (op(X, k) @ op(X, k + 1) + op(Y, k) @ op(Y, k + 1))
    for k in range(1, n + 1):
        H += 0.5 * m * (-1) ** k * op(Z, k)
    for nn in range(1, n):
        L = eps0 * np.eye(dim) + 0.5 * sum(op(Z, k) + (-1) ** k * np.eye(dim) for k in range(1, nn + 1))
        H += J * L @ L
    return H


def can3(qc, alpha, beta, gamma, q0, q1):
    """exp(i(alpha XX + beta YY + gamma ZZ)) with 3 CX, up to a global phase (Vatan-Williams)."""
    qc.rz(-np.pi / 2, q1)
    qc.cx(q1, q0)
    qc.rz(np.pi / 2 - 2 * gamma, q0)
    qc.ry(2 * alpha - np.pi / 2, q1)
    qc.cx(q0, q1)
    qc.ry(np.pi / 2 - 2 * beta, q1)
    qc.cx(q1, q0)
    qc.rz(np.pi / 2, q0)


def swap_gate(qc, a, b, qa, qb, A, hop, dt):
    """SWAP . exp(-i dt [A_ab ZZ + hop (XX + YY) if adjacent]) on qubits (qa, qb) holding sites (a, b)."""
    k, l = min(a, b), max(a, b)
    hx = hop if l - k == 1 else 0.0
    can3(qc, np.pi / 4 - dt * hx, np.pi / 4 - dt * hx, np.pi / 4 - dt * A[(k, l)], qa, qb)


def trotter(n, steps, params, chain=None, dt=DT, measure=True):
    """The user circuit: bare vacuum, `steps` Trotter steps on the chain's labels (default 0..n-1)."""
    from qiskit import QuantumCircuit
    _, w, J, m, eps0 = params
    A, h, hop = couplings(n, w, J, m, eps0)
    chain = list(range(n)) if chain is None else list(chain)
    qc = QuantumCircuit(max(chain) + 1, n if measure else 0)
    at = list(range(1, n + 1))  # at[p] = site held at chain position p
    for p in range(n):
        if at[p] % 2 == 0:
            qc.x(chain[p])
    layers = [p0 for _ in range(n // 2) for p0 in (0, 1)][:n]  # starting position of each layer: 0, 1, 0, 1, ...
    for s in range(steps):
        for p in range(n):
            if h[at[p]] != 0:
                qc.rz(2 * dt * h[at[p]], chain[p])
        for p0 in (layers if s % 2 == 0 else layers[::-1]):
            for p in range(p0, n - 1, 2):
                swap_gate(qc, at[p], at[p + 1], chain[p], chain[p + 1], A, hop, dt)
                at[p], at[p + 1] = at[p + 1], at[p]
    if measure:  # psf-os run2d reads every touched qubit in label order (clbit k = k-th label): measure the same way
        lab = sorted(chain)
        for p in range(n):
            qc.measure(chain[p], lab.index(chain[p]))
    return qc


def final_at(n, steps):
    """Site held at each chain position after `steps` steps (the swap network's permutation)."""
    at = list(range(1, n + 1))
    layers = [p0 for _ in range(n // 2) for p0 in (0, 1)][:n]
    for s in range(steps):
        for p0 in (layers if s % 2 == 0 else layers[::-1]):
            for p in range(p0, n - 1, 2):
                at[p], at[p + 1] = at[p + 1], at[p]
    return at


def site_of_clbit(n, steps, chain=None):
    """[site of clbit k] under the label-order readout."""
    chain = list(range(n)) if chain is None else list(chain)
    at = final_at(n, steps)
    return [at[chain.index(lab)] for lab in sorted(chain)]


def z_sites(qc, n, steps, chain=None):
    """<Z_site> (site 1..n) of a measured circuit (the user circuit or run2d's compiled one, both label-order)."""
    zc = z_from_circuit(qc, n)  # per clbit
    sc = site_of_clbit(n, steps, chain)
    out = [None] * n
    for k, s in enumerate(sc):
        out[s - 1] = zc[k]
    return out


def z_from_circuit(qc, n):
    """Exact <Z> per clbit (0..n-1) of a measured circuit, by statevector on its touched qubits."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    used = sorted({qc.find_bit(q).index for ins in qc.data for q in ins.qubits})
    idx = {p: k for k, p in enumerate(used)}
    body, site = QuantumCircuit(len(used)), {}
    for ins in qc.data:
        qs = [idx[qc.find_bit(q).index] for q in ins.qubits]
        if ins.operation.name == "measure":
            site[qc.find_bit(ins.clbits[0]).index] = qs[0]
        elif ins.operation.name not in ("barrier", "delay"):
            body.append(ins.operation, qs)
    p = Statevector(body).probabilities_dict()
    out = {}
    for s, q in site.items():
        out[s] = float(sum(v * (1 - 2 * int(b[::-1][q])) for b, v in p.items()))
    return [out[k] for k in range(n)]


_EIG = {}


def z_continuous(n, t, params):
    """<Z_n> under exp(-i H t) from the bare vacuum (the reference for the Trotter error); H diagonalised once per
    (n, params)."""
    _, w, J, m, eps0 = params
    key = (n, tuple(params[1:]))
    if key not in _EIG:
        E, V = np.linalg.eigh(hamiltonian(n, w, J, m, eps0))
        idx = sum(1 << (k - 1) for k in range(2, n + 1, 2))  # even sites flipped
        _EIG[key] = (E, V, V.conj().T[:, idx])
    E, V, c0 = _EIG[key]
    psi = V @ (np.exp(-1j * E * t) * c0)
    pr = np.abs(psi) ** 2
    bits = (np.arange(2 ** n)[:, None] >> np.arange(n)[None, :]) & 1
    return [float(v) for v in pr @ (1 - 2 * bits)]


def nu(z):
    n = len(z)
    return sum(1 + (-1) ** k * z[k - 1] for k in range(1, n + 1)) / (2 * n)


def cz_ideal(n, steps):
    return 3 * n * (n - 1) // 2 * steps
