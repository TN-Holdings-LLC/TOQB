"""gpu/du_answers.py (numpy backend) against Aer's statevector and the closed form; the GPU backend is checked the
same way on the pod before any answer is used (gpu/du_answers_pod.sh)."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gpu"))
import du_answers as A  # noqa: E402

from psf_os import dual as DU  # noqa: E402


@pytest.mark.parametrize("kick", [np.pi / 4, np.pi / 4 - 0.1, np.pi / 4 - 0.2])
def test_numpy_backend_matches_statevector(kick):
    from qiskit.quantum_info import Pauli, Statevector
    N, T, h = 9, 4, 0.15
    r = A.run(N, T, h, kick)
    for t in range(T + 1):
        sv = Statevector(DU.chain_circuit(N, t, h, kick, measure=False))
        ref = [float(sv.expectation_value(Pauli("I" * (N - 1 - n) + "X" + "I" * n)).real) for n in range(N)]
        assert np.allclose(r["x"][t], ref, atol=1e-10)
    assert np.allclose(r["norm"], 1, atol=1e-10)


def test_closed_form_at_dual_unitary_point():
    r = A.run(11, 5, 0.15, np.pi / 4, precision="single")
    for t in range(6):
        assert np.allclose(r["x"][t], DU.exact(11, t, 0.15), atol=1e-5)
