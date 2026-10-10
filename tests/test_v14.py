"""Tests of TOQB v14: the essential view (failed elements make an output unusable; the first compile's time), the
count of operations on failed elements, and failed measurements as failed qubits."""
import pytest

from toqb.essential import essential, failed_ops


def _rec(**kw):
    r = dict(adapter="psf:default", case="bp:test_feynman_transpile[x.qasm]", device="bp:test_feynman_transpile[x.qasm]",
             valid=True, q2=10, t_s=0.2, on_failed=0)
    r.update(kw)
    return r


def test_essential_marks_failed_elements_unusable_on_fake_torino_only():
    assert "error" not in essential(_rec())
    e = essential(_rec(on_failed=3))
    assert e["error"].startswith("unusable: 3")
    assert failed_ops(_rec(on_failed=1, on_failed_ops=4)) == 4  # v14 records: every operation counts
    abstract = _rec(case="bp:test_QASMBench_small[x-square]", device="bp:test_QASMBench_small[x-square]", on_failed=2)
    assert "error" not in essential(abstract)  # an abstract map has no failed elements to avoid
    failed = _rec(error="time: compile 1 over 2 s", on_failed=2)
    assert essential(failed)["error"] == failed["error"]


def test_essential_uses_the_first_compile_time():
    assert essential(_rec(t_first_s=0.9))["t_s"] == 0.9
    assert essential(_rec())["t_s"] == 0.2


def test_failed_operations_counts_every_operation():
    pytest.importorskip("qiskit")
    from qiskit import QuantumCircuit
    from toqb.devices import Device
    from toqb.metrics import failed_operations
    dev = Device("t", 4, [(0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2)], ["cz", "rz", "sx", "x"],
                 failed_edges={(0, 1)}, failed_qubits={3})
    qc = QuantumCircuit(4, 1)
    qc.cz(1, 0)        # failed coupler, other direction
    qc.cz(1, 2)        # fine
    qc.sx(3)           # failed qubit
    qc.barrier()       # not counted
    qc.measure(3, 0)   # failed qubit
    assert failed_operations(qc, dev) == 3


def test_failed_measurement_makes_a_failed_qubit():
    pytest.importorskip("qiskit")
    from qiskit.providers.fake_provider import GenericBackendV2
    from qiskit.transpiler import InstructionProperties
    from toqb.devices import _failed
    be = GenericBackendV2(num_qubits=3, basis_gates=["cz", "rz", "sx", "x"], coupling_map=[[0, 1], [1, 2]], seed=14)
    t = be.target
    t.update_instruction_properties("measure", (1,), InstructionProperties(error=0.8,
                                                                            duration=t["measure"][(1,)].duration))
    assert 1 in _failed(t)[1]
