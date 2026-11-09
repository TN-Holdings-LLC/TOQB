"""Checks of schwinger.py (no answer values printed: only differences)."""
import numpy as np
from scipy.linalg import expm
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector, SparsePauliOp
import schwinger as S


def test_can3():
    X = SparsePauliOp
    for a, b, c in [(0.1, -0.3, 0.7), (np.pi / 4 - 0.1, np.pi / 4 - 0.1, np.pi / 4 - 0.4), (0.0, 0.0, 0.0)]:
        qc = QuantumCircuit(2)
        S.can3(qc, a, b, c, 0, 1)
        M = expm(1j * (a * X("XX") + b * X("YY") + c * X("ZZ")).to_matrix())
        assert Operator(qc).equiv(Operator(M)), (a, b, c)
    # SWAP . exp(-i dt (A ZZ + hop (XX+YY)))
    qc = QuantumCircuit(2)
    A, hop, dt = 0.37, 0.5, 0.25
    S.can3(qc, np.pi / 4 - dt * hop, np.pi / 4 - dt * hop, np.pi / 4 - dt * A, 0, 1)
    sw = QuantumCircuit(2); sw.swap(0, 1)
    M = Operator(sw).data @ expm(-1j * dt * (A * X("ZZ") + hop * (X("XX") + X("YY"))).to_matrix())
    assert Operator(qc).equiv(Operator(M))


def test_expansion():
    for n in (4, 6):
        for p in S.PARAMS + [("x", 0.7, 1.3, 0.4, 0.2)]:
            H1 = S.hamiltonian(n, *p[1:])
            H2 = S.hamiltonian_direct(n, *p[1:])
            d = H2 - H1
            # equal up to a constant times identity
            c = np.trace(d) / d.shape[0]
            assert np.abs(d - c * np.eye(d.shape[0])).max() < 1e-12


def test_trotter_vs_product():
    """The circuit equals the product formula built from matrices in the same order (swap network = all pairs once)."""
    n, steps, p = 6, 3, ("x", 0.7, 1.3, 0.4, 0.2)
    A, h, hop = S.couplings(n, *p[1:])
    Hz = SparsePauliOp.from_sparse_list([("Z", [k - 1], v) for k, v in h.items()], num_qubits=n).to_matrix()
    qc = S.trotter(n, steps, p, measure=False)
    # build the same product with logical sites: after each step the network reverses the order; track like the code
    z = S.z_sites(S.trotter(n, steps, p), n, steps)
    # independent: logical-site simulation with the same gate order
    psi = np.zeros(2 ** n, complex); psi[sum(1 << (k - 1) for k in range(2, n + 1, 2))] = 1
    at = list(range(1, n + 1)); layers = [p0 for _ in range(n // 2) for p0 in (0, 1)][:n]
    for s in range(steps):
        psi = expm(-1j * S.DT * Hz) @ psi
        for p0 in (layers if s % 2 == 0 else layers[::-1]):
            for q in range(p0, n - 1, 2):
                a, b = sorted((at[q], at[q + 1]))
                terms = [("ZZ", [a - 1, b - 1], A[(a, b)])] + ([("XX", [a - 1, b - 1], hop), ("YY", [a - 1, b - 1], hop)] if b - a == 1 else [])
                G = SparsePauliOp.from_sparse_list(terms, num_qubits=n).to_matrix()
                psi = expm(-1j * S.DT * G) @ psi
                at[q], at[q + 1] = at[q + 1], at[q]
    pr = np.abs(psi) ** 2
    z2 = [sum(pr[i] * (1 - 2 * ((i >> (k - 1)) & 1)) for i in range(2 ** n)) for k in range(1, n + 1)]
    assert max(abs(x - y) for x, y in zip(z, z2)) < 1e-10, max(abs(x - y) for x, y in zip(z, z2))


def test_vacuum_and_small_dt():
    p = S.PARAMS[0]
    z0 = S.z_sites(S.trotter(6, 0, p), 6, 0)
    assert abs(S.nu(z0)) < 1e-12
    # Trotter -> continuous for small dt (made-up time 0.5)
    zt = S.z_sites(S.trotter(6, 51, p, dt=0.5 / 51), 6, 51)
    zc = S.z_continuous(6, 0.5, p)
    assert max(abs(a - b) for a, b in zip(zt, zc)) < 5e-3


def test_label_order_readout():
    """Odd step counts on a chain whose labels are not in chain order: z_sites equals the logical simulation."""
    n, p = 6, ("x", 0.7, 1.3, 0.4, 0.2)
    for steps in (1, 2, 3):
        ref = S.z_sites(S.trotter(n, steps, p), n, steps)
        ch = [40, 41, 22, 21, 20, 0]
        assert max(abs(a - b) for a, b in zip(S.z_sites(S.trotter(n, steps, p, chain=ch), n, steps, ch), ref)) < 1e-10
        # label-order clbits, as run2d reads
        qc = S.trotter(n, steps, p, chain=ch)
        got = [(qc.find_bit(i.qubits[0]).index, qc.find_bit(i.clbits[0]).index) for i in qc.data if i.operation.name == "measure"]
        assert sorted(got) == [(lab, k) for k, lab in enumerate(sorted(ch))]


def test_cz_count():
    from qiskit import transpile
    qc = S.trotter(6, 2, S.PARAMS[0], measure=False)
    assert qc.count_ops()["cx"] == S.cz_ideal(6, 2)


if __name__ == "__main__":
    for f in [test_can3, test_expansion, test_trotter_vs_product, test_vacuum_and_small_dt, test_label_order_readout, test_cz_count]:
        f(); print("ok", f.__name__)
