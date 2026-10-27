"""toqb.clifford_lam (2026-10-28): the prepared input makes the noiseless <Z_0> exactly s, for the logical circuit
and for the circuit compiled by the fold arm; all circuits of an (n, L) share one structure."""
import numpy as np
import pytest

pytest.importorskip("qiskit")
from qiskit.quantum_info import Statevector  # noqa: E402

from toqb import clifford_lam as C  # noqa: E402
from toqb import s2r as S  # noqa: E402
from toqb.devices import get_device  # noqa: E402
from tests.test_fold import p1_all  # noqa: E402


@pytest.mark.parametrize("n,L", [(4, 3), (6, 5), (7, 8)])
def test_logical_value_is_the_sign(n, L):
    rng = np.random.default_rng(10 * n + L)
    for _ in range(6):
        prep, ang, s = C.clifford_case(n, L, rng)
        qc = C.circuit(prep, ang, n, L).remove_final_measurements(inplace=False)
        p1 = Statevector(qc).probabilities([0])[1]
        assert abs((1 - 2 * p1) - s) < 1e-9


@pytest.mark.parametrize("n", [8, 13])
def test_compiled_value_is_the_sign_and_one_structure(n):
    arm = S.Arm("fold:rule", get_device("snapshot:marrakesh"))
    rng = np.random.default_rng(99 + n)
    sigs = set()
    for _ in range(4):
        prep, ang, s = C.clifford_case(n, 2, rng)
        c = arm.compile(C.circuit(prep, ang, n, 2))
        assert abs((1 - 2 * p1_all(c)[0]) - s) < 1e-9
        sigs.add(tuple((i.operation.name, tuple(c.find_bit(q).index for q in i.qubits)) for i in c.data))
    assert arm.arm.stats["template_builds"] == 1
    assert len(sigs) == 1
