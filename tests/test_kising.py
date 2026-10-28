"""toqb.kising (2026-10-28): the circuit in model_circuit order measures SIGN_OF_READOUT * <X_0> after L Floquet
steps, the free-fermion evaluator equals the statevector, and the compiled fold arm keeps it exact with one template."""
import numpy as np
import pytest

pytest.importorskip("qiskit")
from qiskit.quantum_info import Pauli, Statevector  # noqa: E402

from toqb import kising as K  # noqa: E402
from toqb import s2r as S  # noqa: E402
from toqb.devices import get_device  # noqa: E402
from tests.test_fold import p1_all  # noqa: E402


def floquet_x(s, n, L, h):
    """<X_j> after L steps (CZ ring, Z, RX(2h)) from |s>, by a plain Qiskit circuit."""
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(n)
    for q in range(n):
        qc.h(q)
        if s[q] == -1:
            qc.z(q)
    for _ in range(L):
        for q in range(n):
            qc.cz(q, (q + 1) % n)
        for q in range(n):
            qc.z(q)
            qc.rx(2 * h, q)
    sv = Statevector(qc)
    return np.array([sv.expectation_value(Pauli("I" * (n - 1 - j) + "X" + "I" * j)).real for j in range(n)])


@pytest.mark.parametrize("n,L,h", [(5, 3, 0.6), (6, 7, 0.3), (7, 4, 0.9), (8, 9, 0.6)])
def test_exact_equals_statevector_and_the_circuit(n, L, h):
    rng = np.random.default_rng(n * 100 + L)
    for _ in range(4):
        s = rng.choice([1, -1], n)
        ref = floquet_x(s, n, L, h)
        assert np.abs(K.x_exact(s, n, [L], h)[L] - ref).max() < 1e-10
        qc = K.circuit(s, n, L, h).remove_final_measurements(inplace=False)
        z0 = 1 - 2 * Statevector(qc).probabilities([0])[1]
        assert abs(z0 - K.SIGN_OF_READOUT * ref[0]) < 1e-10
        assert abs(K.z_noiseless(s, n, L, h) - z0) < 1e-10


@pytest.mark.parametrize("n", [8, 13])
def test_compiled_is_exact_and_one_structure(n):
    arm = S.Arm("fold:rule", get_device("snapshot:marrakesh"))
    rng = np.random.default_rng(5 + n)
    sigs = set()
    for _ in range(4):
        s = rng.choice([1, -1], n)
        c = arm.compile(K.circuit(s, n, 3, 0.6))
        assert abs((1 - 2 * p1_all(c)[0]) - K.z_noiseless(s, n, 3, 0.6)) < 1e-9
        sigs.add(tuple((i.operation.name, tuple(c.find_bit(q).index for q in i.qubits)) for i in c.data))
    assert arm.arm.stats["template_builds"] == 1
    assert len(sigs) == 1


@pytest.mark.parametrize("n,L,p", [(4, 3, 0.02), (5, 6, 0.01), (6, 4, 0.04)])
def test_noisy_recursion_equals_density_matrix(n, L, p):
    """x0_noisy against an exact density matrix: each step (CZ ring, Z, RX(2h)) then depolarizing p on every qubit."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import DensityMatrix, Operator
    h = 0.6
    step = QuantumCircuit(n)
    for q in range(n):
        step.cz(q, (q + 1) % n)
    for q in range(n):
        step.z(q)
        step.rx(2 * h, q)
    U = Operator(step).data
    I2, X, Y, Z = np.eye(2), np.array([[0, 1], [1, 0]]), np.array([[0, -1j], [1j, 0]]), np.diag([1.0, -1.0])

    def on(q, m):  # Qiskit order: qubit q is bit q (rightmost factor is qubit 0)
        out = np.array([[1.0]])
        for k in reversed(range(n)):
            out = np.kron(out, m if k == q else I2)
        return out

    rng = np.random.default_rng(10 * n + L)
    s = rng.choice([1, -1], n)
    prep = QuantumCircuit(n)
    for q in range(n):
        prep.h(q)
        if s[q] == -1:
            prep.z(q)
    rho = DensityMatrix(prep).data
    for _ in range(L):
        rho = U @ rho @ U.conj().T
        for q in range(n):
            rho = (1 - p) * rho + p / 3 * sum(on(q, P) @ rho @ on(q, P).conj().T for P in (X, Y, Z))
    ref = float(np.real(np.trace(on(0, X) @ rho)))
    assert abs(K.x0_noisy(s, n, [L], h, p)[L] - ref) < 1e-10
