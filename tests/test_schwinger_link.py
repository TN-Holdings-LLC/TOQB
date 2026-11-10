"""gpu/schwinger_link.py: the hop gate is the exponential it claims, the link H inside Gauss's law is the truncated
gauge-eliminated H, the circuit stays inside Gauss's law and equals the Trotter product computed on the kept
configurations. Parameters here are made up (not the declared sets)."""
import os
import sys

import numpy as np
import pytest
from scipy.linalg import expm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gpu"))
import schwinger_link as SL  # noqa: E402

P_TEST = ("T", 0.9, 1.3, 0.7, 0.0)


@pytest.mark.parametrize("n", [1, 2])
@pytest.mark.parametrize("theta", [0.17, -0.61, 1.9])
def test_hop_gate_is_the_exponential(n, theta):
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Operator
    N = 3                      # links 1 (odd) and 2 (even) on qubits 0..4
    qc = QuantumCircuit(SL.nqubits(N))
    SL.hop(qc, n, theta, SL.site_q(n), SL.link_q(n), SL.site_q(n + 1))
    U = Operator(qc).data
    V = expm(-1j * theta * SL._hop_op(n, N).to_matrix())
    assert abs(abs(np.vdot(V.flatten(), U.flatten())) - U.shape[0]) < 1e-9
    assert qc.count_ops()["cx"] == 8


@pytest.mark.parametrize("N", [2, 4, 6])
def test_link_h_inside_gauss_is_truncated_h(N):
    H = SL.link_hamiltonian(N, P_TEST).to_matrix()
    confs, chain = SL.physical_configs(N)
    idx = [chain[c] for c in confs]
    HL = H[np.ix_(idx, idx)]
    HP, _ = SL.trunc_hamiltonian(N, P_TEST)
    D = HL - HP
    shift = np.trace(D) / len(idx)            # constants dropped differently: equal up to a multiple of 1
    assert np.max(np.abs(D - shift * np.eye(len(idx)))) < 1e-12
    # the link H never leaves the physical configurations
    other = [i for i in range(H.shape[0]) if i not in set(idx)]
    assert np.max(np.abs(H[np.ix_(other, idx)])) < 1e-12


@pytest.mark.parametrize("N,steps", [(4, 3), (6, 2)])
def test_circuit_equals_reduced_trotter_and_keeps_gauss(N, steps):
    z, g = SL.circuit_answers(N, steps, P_TEST, dt=0.3)
    zr = SL.z_trotter_reduced(N, steps, P_TEST, dt=0.3)
    assert max(abs(a - b) for a, b in zip(z, zr)) < 1e-10
    assert g < 1e-10


def test_counts_and_truncation_limit():
    assert all(SL.trotter(N, 1, P_TEST).count_ops()["cx"] == SL.cz_per_step(N) for N in (4, 6, 8))
    # with no hopping nothing moves; the kept configurations include the vacuum and every single pair
    confs, _ = SL.physical_configs(6)
    vac = sum(1 << (k - 1) for k in range(2, 7, 2))
    assert vac in confs
    for n in range(1, 6):
        assert (vac ^ (1 << (n - 1)) ^ (1 << n)) in confs
