"""Schwinger model with the gauge field kept on link qubits (VS Claude, 2026-11-10; not declared). Every interaction is
between neighbours on one chain, so the CZ count per qubit and step does not grow with N (the swap network of
gpu/schwinger.py costs 3(N - 1) CZ per qubit and step; notes/schwinger_scale_2026-11-10).

Model: the same lattice Schwinger model as gpu/schwinger.py (Martinez et al., Nature 534, 516 (2016)), Kogut-Susskind
staggered fermions, open boundary, sites n = 1..N (N even), links n = 1..N-1 between sites n and n+1, background
eps0 = 0 (L_0 = 0). Before the gauge field is eliminated:
    H = w sum_{n<N} (s+_n R_n s-_{n+1} + h.c.) + (m/2) sum_n (-1)^n Z_n + J sum_{n<N} L_n^2,
    Gauss's law  L_n - L_{n-1} = (Z_n + (-1)^n) / 2,
R_n raises the electric field L_n by one (s+ = |0><1| raises Z_n by 2, so Gauss's law needs L_n one higher).
Eliminating the links by Gauss's law gives exactly gpu/schwinger.py's H.

Truncation (the smallest: one qubit per link). From the bare vacuum (L = 0 everywhere), a pair on link n moves L_n to
-1 for odd n and to +1 for even n. Each link keeps the two values {0, -1} (odd n) or {0, +1} (even n):
    odd n:  L_n = (Z_l - 1) / 2,  R_n = s+_l = |0><1|        even n:  L_n = (1 - Z_l) / 2,  R_n = s-_l = |1><0|
    both:   L_n^2 = (1 - Z_l) / 2,  so J L_n^2 -> -(J/2) Z_l + const.
Inside Gauss's law the truncated model is the gauge-eliminated H projected onto the site configurations whose fields
(by Gauss's law) stay inside the kept values: H_trunc = P H P (a hop that would leave the kept values is the
truncated R acting on its top value, which is zero). `trunc_hamiltonian` builds P H P from gpu/schwinger.hamiltonian
independently of the circuit; the tests check that the link Pauli H restricted to Gauss's law equals it.

Chain order: site 1, link 1, site 2, link 2, ..., site N (2N - 1 qubits): site n is qubit 2(n-1), link n is qubit 2n-1.

Circuit (first-order Trotter, fixed dt; nothing searched). Per step: the diagonal layer (RZ(dt m (-1)^n) on site n, RZ(-dt J)
on every link), then the hops on odd links, then the hops on even links (hops on links n and n+2 share no qubit).
A hop exp(-i theta (s+_a R s-_b + h.c.)), theta = dt w, couples two basis states of (a, l, b) that differ on all three
qubits: odd link |1 1 0> <-> |0 0 1>, even link |1 0 0> <-> |0 1 1>. With the link qubit l as pivot:
    CX(l, a) CX(l, b)                      the two states now differ only on l (a, b fixed: odd a=0 b=1, even a=1 b=0)
    S(l) . doubly controlled exp(-i theta Y_l) on that (a, b) . S^dagger(l)   (= exp(-i theta X_l) on that (a, b))
           the controlled rotation as a Gray-code multiplexer: RY(al1) CX(a, l) RY(al2) CX(b, l) RY(al3) CX(a, l)
           RY(al4) CX(b, l), angles from the Walsh transform of 2 theta [a = a0][b = b0]
    CX(l, b) CX(l, a)                      undo
8 CX per hop, all between neighbours of the chain (a - l - b). Per step 8 (N - 1) CZ (as CX), per qubit 8 (N - 1) / (2N - 1) < 4.

Readout: <Z_n> of the site qubits; nu = (1/2N) sum_n (1 + (-1)^n <Z_n>) as in gpu/schwinger.py.
"""
from __future__ import annotations

import itertools

import numpy as np

DT = 0.25


def site_q(n):
    return 2 * (n - 1)


def link_q(n):
    return 2 * n - 1


def nqubits(N):
    return 2 * N - 1


def vacuum_bits(N):
    """{qubit: 1} of the bare vacuum: X on the even sites; every link |0> (L = 0)."""
    return [site_q(n) for n in range(2, N + 1, 2)]


def _walsh(a0, b0, theta):
    """Gray-code angles (al1..al4) for RY(f(a, b)) on the pivot, f = 2 theta [a = a0][b = b0], in the order
    RY(al1) CX(a) RY(al2) CX(b) RY(al3) CX(a) RY(al4) CX(b): f(a, b) = al1 + (-1)^a al2 + (-1)^(a+b) al3 + (-1)^b al4."""
    f = {(a, b): (2 * theta if (a, b) == (a0, b0) else 0.0) for a in (0, 1) for b in (0, 1)}
    al1 = sum(f.values()) / 4
    al2 = sum((-1) ** a * v for (a, b), v in f.items()) / 4
    al3 = sum((-1) ** (a + b) * v for (a, b), v in f.items()) / 4
    al4 = sum((-1) ** b * v for (a, b), v in f.items()) / 4
    return al1, al2, al3, al4


def hop(qc, n, theta, a, l, b):
    """exp(-i theta (s+_a R_n s-_b + h.c.)) on qubits (a, l, b) of link n (8 CX, neighbours only)."""
    a0, b0 = (0, 1) if n % 2 == 1 else (1, 0)
    qc.cx(l, a)
    qc.cx(l, b)
    al1, al2, al3, al4 = _walsh(a0, b0, theta)
    qc.s(l)
    qc.ry(al1, l)
    qc.cx(a, l)
    qc.ry(al2, l)
    qc.cx(b, l)
    qc.ry(al3, l)
    qc.cx(a, l)
    qc.ry(al4, l)
    qc.cx(b, l)
    qc.sdg(l)
    qc.cx(l, b)
    qc.cx(l, a)


def trotter(N, steps, params, dt=DT):
    """The link circuit (no measurement): bare vacuum, `steps` first-order Trotter steps."""
    from qiskit import QuantumCircuit
    _, w, J, m, eps0 = params
    if eps0 != 0:
        raise ValueError("written for the background eps0 = 0")
    qc = QuantumCircuit(nqubits(N))
    for q in vacuum_bits(N):
        qc.x(q)
    for _ in range(steps):
        for n in range(1, N + 1):
            if m:
                qc.rz(dt * m * (-1) ** n, site_q(n))       # exp(-i dt (m/2)(-1)^n Z)
        for n in range(1, N):
            if J:
                qc.rz(-dt * J, link_q(n))                  # exp(-i dt (-J/2) Z_l)
        for parity in (1, 0):
            for n in range(1, N):
                if n % 2 == parity:
                    hop(qc, n, dt * w, site_q(n), link_q(n), site_q(n + 1))
    return qc


def cz_per_step(N):
    return 8 * (N - 1)


# ---------------------------------------------------------------------------------------------------------------
# the link Hamiltonian, Gauss's law and the truncated reference
# ---------------------------------------------------------------------------------------------------------------

def _hop_op(n, N):
    """s+_a R_n s-_b + h.c. as a SparsePauliOp on the 2N - 1 chain qubits."""
    from qiskit.quantum_info import SparsePauliOp
    sp = SparsePauliOp.from_list([("X", 0.5), ("Y", 0.5j)])       # s+ = |0><1| = (X + iY)/2
    sm = SparsePauliOp.from_list([("X", 0.5), ("Y", -0.5j)])
    R = sp if n % 2 == 1 else sm
    a, l, b = site_q(n), link_q(n), site_q(n + 1)
    op = sm.tensor(R).tensor(sp)        # qubit order of tensor(): rightmost = lowest; (b, l, a) on 3 qubits
    op = op + op.adjoint()
    nq = nqubits(N)
    return SparsePauliOp.from_sparse_list([(lab.to_label()[::-1], [a, l, b], c) for lab, c in zip(op.paulis, op.coeffs)
                                           ], num_qubits=nq).simplify()


def link_hamiltonian(N, params):
    """The truncated link H (SparsePauliOp, 2N - 1 qubits), constants dropped."""
    from qiskit.quantum_info import SparsePauliOp
    _, w, J, m, eps0 = params
    nq = nqubits(N)
    terms = [("Z", [site_q(n)], 0.5 * m * (-1) ** n) for n in range(1, N + 1) if m]
    terms += [("Z", [link_q(n)], -0.5 * J) for n in range(1, N) if J]
    H = SparsePauliOp.from_sparse_list(terms or [("", [], 0.0)], num_qubits=nq)
    for n in range(1, N):
        H = H + w * _hop_op(n, N)
    return H.simplify()


def field_of_bits(sites):
    """[L_1 .. L_{N-1}] by Gauss's law from site Z values (sites: list of +-1, site n at index n-1), eps0 = 0."""
    L, out = 0.0, []
    for n, z in enumerate(sites[:-1], start=1):
        L += 0.5 * (z + (-1) ** n)
        out.append(L)
    return out


def kept(L, n):
    return L == 0 or L == (-1 if n % 2 == 1 else 1)


def physical_configs(N):
    """Site configurations (integers, bit k-1 = site k, 1 = Z -1) whose Gauss's-law fields stay in the kept values,
    with their link bits; returns (configs, {config: full chain index})."""
    confs, chain = [], {}
    for c in range(2 ** N):
        z = [1 - 2 * ((c >> (k - 1)) & 1) for k in range(1, N + 1)]
        L = field_of_bits(z)
        if not all(kept(v, n) for n, v in enumerate(L, start=1)):
            continue
        idx = 0
        for k in range(1, N + 1):
            if z[k - 1] == -1:
                idx |= 1 << site_q(k)
        for n, v in enumerate(L, start=1):
            if v != 0:
                idx |= 1 << link_q(n)
        confs.append(c)
        chain[c] = idx
    return confs, chain


def trunc_hamiltonian(N, params):
    """P H P on the kept configurations (from gpu/schwinger.hamiltonian, the gauge-eliminated H); returns (H_P, confs)."""
    import schwinger as S
    _, w, J, m, eps0 = params
    H = S.hamiltonian(N, w, J, m, eps0)
    confs, _ = physical_configs(N)
    return H[np.ix_(confs, confs)], confs


def z_of_state(psi, confs, N):
    """<Z_n> (n = 1..N) of a state on the kept configurations."""
    p = np.abs(psi) ** 2
    bits = (np.array(confs)[:, None] >> np.arange(N)[None, :]) & 1
    return [float(v) for v in p @ (1 - 2 * bits)]


def vacuum_index(confs, N):
    c = sum(1 << (k - 1) for k in range(2, N + 1, 2))
    return confs.index(c)


def z_trunc_continuous(N, t, params):
    """<Z_n> under exp(-i P H P t) from the bare vacuum (truncated, no Trotter error)."""
    HP, confs = trunc_hamiltonian(N, params)
    E, V = np.linalg.eigh(HP)
    c0 = V.conj().T[:, vacuum_index(confs, N)]
    return z_of_state(V @ (np.exp(-1j * E * t) * c0), confs, N)


def trotter_groups(N, params):
    """The three groups of a step as matrices on the kept configurations: diagonal, odd-link hops, even-link hops,
    from the gauge-eliminated terms of gpu/schwinger.couplings projected onto the kept configurations (P H_g P; equal
    to the link groups inside Gauss's law up to constants). Sparse until projected."""
    import schwinger as S
    _, w, J, m, eps0 = params
    A, h, hop_ = S.couplings(N, w, J, m, eps0)
    from qiskit.quantum_info import SparsePauliOp
    nq = N
    confs, _ = physical_configs(N)

    def proj(op):
        return op.to_matrix(sparse=True).tocsr()[confs][:, confs].toarray()
    diag = SparsePauliOp.from_sparse_list([("ZZ", [k - 1, l - 1], a) for (k, l), a in A.items() if a]
                                          + [("Z", [k - 1], v) for k, v in h.items() if v] or [("", [], 0.0)],
                                          num_qubits=nq)
    out = [proj(diag)]
    for parity in (1, 0):
        terms = [(p, [n - 1, n], hop_) for n in range(1, N) if n % 2 == parity for p in ("XX", "YY")]
        out.append(proj(SparsePauliOp.from_sparse_list(terms, num_qubits=nq)))
    return out, confs


def z_trotter_reduced(N, steps, params, dt=DT):
    """<Z_n> of the same first-order Trotter product, computed on the kept configurations only (independent of the
    gates): exp(-i dt H_diag), then exp(-i dt H_odd hops), then exp(-i dt H_even hops), per step."""
    from scipy.linalg import expm
    groups, confs = trotter_groups(N, params)
    Us = [expm(-1j * dt * G) for G in groups]
    psi = np.zeros(len(confs), complex)
    psi[vacuum_index(confs, N)] = 1.0
    for _ in range(steps):
        for U in Us:
            psi = U @ psi
    return z_of_state(psi, confs, N)


def gauss_ops(N):
    """G_n^2 (n = 1..N) as SparsePauliOps, G_n = L_n - L_{n-1} - (Z_n + (-1)^n)/2; zero on physical states."""
    from qiskit.quantum_info import SparsePauliOp
    nq = nqubits(N)

    def L(n):
        if n == 0 or n == N:
            return SparsePauliOp.from_sparse_list([("", [], 0.0)], num_qubits=nq)
        s = 1 if n % 2 == 1 else -1        # odd: (Z - 1)/2; even: (1 - Z)/2
        return SparsePauliOp.from_sparse_list([("Z", [link_q(n)], 0.5 * s), ("", [], -0.5 * s)], num_qubits=nq)
    out = []
    for n in range(1, N + 1):
        G = L(n) - L(n - 1) - SparsePauliOp.from_sparse_list([("Z", [site_q(n)], 0.5), ("", [], 0.5 * (-1) ** n)],
                                                             num_qubits=nq)
        out.append(G.compose(G).simplify())
    return out


def circuit_answers(N, steps, params, dt=DT, method="auto"):
    """(<Z_n> of the sites, max_n <G_n^2>) of the link circuit by statevector (Aer above 20 qubits; up to 28)."""
    from qiskit.quantum_info import SparsePauliOp
    nq = nqubits(N)
    if nq > 28:
        raise ValueError("statevector only up to 28 qubits (N 14)")
    qc = trotter(N, steps, params, dt)
    zs = [SparsePauliOp.from_sparse_list([("Z", [site_q(n)], 1.0)], num_qubits=nq) for n in range(1, N + 1)]
    gs = gauss_ops(N)
    if method == "auto":
        method = "statevector" if nq <= 20 else "aer"
    if method == "statevector":
        from qiskit.quantum_info import Statevector
        sv = Statevector(qc)
        z = [float(np.real(sv.expectation_value(o))) for o in zs]
        g = max(float(np.real(sv.expectation_value(o))) for o in gs)
        return z, g
    from qiskit_aer import AerSimulator
    q2 = qc.copy()
    for k, o in enumerate(zs):
        q2.save_expectation_value(o, list(range(nq)), label=f"z{k}")
    for k, o in enumerate(gs):
        q2.save_expectation_value(o, list(range(nq)), label=f"g{k}")
    d = AerSimulator(method="statevector").run(q2).result().data()
    return [float(np.real(d[f"z{k}"])) for k in range(N)], max(float(np.real(d[f"g{k}"])) for k in range(N))


def nu(z):
    n = len(z)
    return sum(1 + (-1) ** k * z[k - 1] for k in range(1, n + 1)) / (2 * n)
