"""toqb.fold (2026-10-25): the hole schedule arm builds TOQB's ring classifier exactly (statevector against the
logical model, every clbit) with n + 2(m - n) two-qubit gates per layer, on a cycle placed by formula; failed
elements are avoided."""
import copy

import numpy as np
import pytest

pytest.importorskip("qiskit")
from qiskit import QuantumCircuit  # noqa: E402
from qiskit.quantum_info import Statevector  # noqa: E402
from qiskit.transpiler import InstructionProperties  # noqa: E402

from toqb import fold as F  # noqa: E402
from toqb import s2r as S  # noqa: E402
from toqb import task_loop as TL  # noqa: E402
from toqb.devices import get_device  # noqa: E402


def p1_all(c):
    act = sorted({c.find_bit(q).index for i in c.data for q in i.qubits if i.operation.name not in ("barrier", "delay")})
    idx = {q: k for k, q in enumerate(act)}
    s, meas = QuantumCircuit(len(act)), {}
    for i in c.data:
        nm = i.operation.name
        if nm in ("barrier", "delay"):
            continue
        if nm == "measure":
            meas[c.find_bit(i.clbits[0]).index] = idx[c.find_bit(i.qubits[0]).index]
            continue
        s.append(i.operation, [idx[c.find_bit(q).index] for q in i.qubits])
    sv = Statevector(s)
    return [float(sv.probabilities([meas[k]])[1]) for k in sorted(meas)]


def model(n, L, seed):
    rng = np.random.default_rng(seed)
    return TL.model_circuit(TL.angle_list(rng.uniform(-1, 1, TL.n_params(n, L)), rng.uniform(-1, 1, n), n, L,
                                          np.pi / 2), n, L)


@pytest.mark.parametrize("n", [9, 10, 11])
def test_fold_arm_is_exact(n):
    arm = S.Arm("fold:template", get_device("snapshot:marrakesh"))
    for L in (2, 4):
        qc = model(n, L, 10 * n + L)
        c = arm.compile(qc)
        assert max(abs(a - b) for a, b in zip(p1_all(c), p1_all(qc))) < 1e-9
        m = arm.arm.stats["last"]["m"]
        assert sum(1 for i in c.data if len(i.qubits) == 2) == L * (n + 2 * (m - n))
        qc2 = model(n, L, 999)  # the same structure, other angles: bound, not rebuilt
        c2 = arm.compile(qc2)
        assert max(abs(a - b) for a, b in zip(p1_all(c2), p1_all(qc2))) < 1e-9


def test_lengths_and_failed_elements():
    t = get_device("snapshot:marrakesh").target
    assert F.fold_place(t, 19)[0] == 20 and F.fold_place(t, 21)[0] == 24 and F.fold_place(t, 36)[0] == 36
    assert F.fold_place(t, 37) is None
    m, _, cyc = F.fold_place(t, 19)
    t2 = copy.deepcopy(t)
    a, b = sorted((cyc[0], cyc[1]))
    for qa in ((a, b), (b, a)):
        if qa in t2["cz"]:
            p = t2["cz"][qa]
            t2.update_instruction_properties("cz", qa, InstructionProperties(duration=p.duration, error=1.0))
    m2, _, cyc2 = F.fold_place(t2, 19)
    assert m2 == 20 and not ({a, b} <= set(cyc2) and any({cyc2[i], cyc2[(i + 1) % 20]} == {a, b} for i in range(20)))


def test_refuses_other_circuits():
    qc = QuantumCircuit(5)
    qc.cz(0, 2)
    with pytest.raises(F.FoldRefused):
        F.read_ring(qc)


@pytest.mark.parametrize("n", [13, 15, 17])
def test_pend_arm_is_exact(n):
    """fold:pend (2026-10-26): the 12-cycle with n - 12 ring nodes hung off it, n + (n - 12) two-qubit gates per
    layer, n active qubits, exact on every clbit."""
    arm = S.Arm("fold:pend", get_device("snapshot:marrakesh"))
    for L in (2, 4):
        qc = model(n, L, 10 * n + L)
        c = arm.compile(qc)
        assert max(abs(a - b) for a, b in zip(p1_all(c), p1_all(qc))) < 1e-9
        assert arm.arm.stats["last"]["m"] == 12
        assert sum(1 for i in c.data if len(i.qubits) == 2) == L * (2 * n - 12)
        assert len({c.find_bit(q).index for i in c.data for q in i.qubits}) == n


@pytest.mark.parametrize("mode", ["rule", "rulerot"])
def test_rule_arms(mode):
    """fold:rule / fold:rulerot (2026-10-26): the count rule picks holes at n = 11, pendants at 13, holes at 18; every
    choice exact on every clbit; rulerot reads ring node 0 off a qubit without a pendant."""
    arm = S.Arm(f"fold:{mode}", get_device("snapshot:marrakesh"))
    for n, want in ((11, "holes"), (13, "pend"), (18, "holes")):
        qc = model(n, 2, 10 * n + 2)
        c = arm.compile(qc)
        assert arm.arm.stats["choice"] == want
        assert max(abs(a - b) for a, b in zip(p1_all(c), p1_all(qc))) < 1e-9
