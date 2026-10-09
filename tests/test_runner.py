"""Tests of the runner's arithmetic (no quantum package needed) and, when Qiskit is installed, of one measurement."""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from toqb import runner as R  # noqa: E402


def test_trimmed_mean_drops_fastest_and_slowest():
    assert R.trimmed_mean([5.0, 1.0, 2.0, 3.0, 100.0]) == pytest.approx(10 / 3)
    assert R.trimmed_mean([2.0, 4.0]) == 3.0


def test_budgets_are_multiples_with_a_floor():
    b = R.budgets(0.2)
    assert b == {1.0: pytest.approx(0.2), 3.0: pytest.approx(0.6), 10.0: pytest.approx(2.0)}
    assert R.budgets(0.001) == {1.0: pytest.approx(0.05), 3.0: pytest.approx(0.15), 10.0: pytest.approx(0.5)}


def test_within_counts_failures_as_misses():
    assert R.within({"t_s": 0.5, "valid": True}, 0.2) == {1.0: False, 3.0: True, 10.0: True}
    assert R.within({"t_s": 0.1, "valid": False}, 0.2) == {1.0: False, 3.0: False, 10.0: False}
    assert R.within({"error": "timeout"}, 0.2) == {1.0: False, 3.0: False, 10.0: False}


def test_not_equivalent_is_a_miss():
    bad = {"t_s": 0.1, "valid": True, "equivalence": {"checked": True, "equivalent": False, "infidelity": 0.3}}
    unchecked = {"t_s": 0.1, "valid": True, "equivalence": {"checked": False, "why": "too wide"}}
    assert R.within(bad, 0.2) == {1.0: False, 3.0: False, 10.0: False}
    assert R.within(unchecked, 0.2) == {1.0: True, 3.0: True, 10.0: True}


def test_gmean():
    assert R.gmean([1.0, 4.0]) == pytest.approx(2.0)


@pytest.mark.skipif(importlib.util.find_spec("qiskit") is None, reason="needs Qiskit")
def test_one_measurement_with_qiskit():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    p = subprocess.run([sys.executable, "-m", "toqb.runner", "one", "--adapter", "qiskit:1", "--case", "ghz:4",
                        "--device", "linear:5", "--b10-s", "60"], capture_output=True, text=True, cwd=root)
    rec = json.loads([ln for ln in p.stdout.splitlines() if ln.startswith("{")][-1])
    assert rec["valid"] is True and rec["q2"] >= 3 and len(rec["times_s"]) == R.REPEATS
    assert rec["equivalence"]["checked"] is True and rec["equivalence"]["equivalent"] is True


@pytest.mark.skipif(importlib.util.find_spec("qiskit") is None, reason="needs Qiskit")
def test_equivalence_catches_a_wrong_output():
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from toqb.cases import get_case
    from toqb.devices import get_device
    from toqb.metrics import equivalence
    dev = get_device("linear:6")
    qc = get_case("qft:4")
    out = generate_preset_pass_manager(2, coupling_map=__import__("qiskit").transpiler.CouplingMap(dev.edges),
                                       basis_gates=dev.basis, seed_transpiler=0).run(qc)
    assert equivalence(qc, out)["equivalent"] is True
    wrong = out.copy()
    wrong.x(out.layout.final_index_layout(filter_ancillas=True)[0])
    assert equivalence(qc, wrong)["equivalent"] is False


@pytest.mark.skipif(importlib.util.find_spec("qiskit") is None, reason="needs Qiskit")
def test_measured_circuit_is_compared_by_distribution():
    """Level 3 removes a swap and a diagonal gate before the measurements: the state changes, the measured
    probabilities do not. A flipped measurement is still caught."""
    from qiskit import QuantumCircuit
    from qiskit.transpiler import CouplingMap
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from toqb.devices import get_device
    from toqb.metrics import equivalence
    dev = get_device("linear:4")
    qc = QuantumCircuit(3, 3)
    qc.h(0)
    qc.cx(0, 1)
    qc.ry(0.4, 2)
    qc.swap(1, 2)
    qc.rz(0.3, 0)
    qc.measure(range(3), range(3))
    out = generate_preset_pass_manager(3, coupling_map=CouplingMap(dev.edges), basis_gates=dev.basis,
                                       seed_transpiler=0).run(qc)
    eq = equivalence(qc, out)
    assert eq["method"] == "distribution" and eq["equivalent"] is True
    wrong = out.copy_empty_like()
    flipped = False
    for ins in out.data:
        if ins.operation.name == "measure" and not flipped:
            wrong.x(ins.qubits[0])
            flipped = True
        wrong.append(ins)
    assert equivalence(qc, wrong)["equivalent"] is False
    # a swap after the measurements (as TKET can leave one) changes no measured bit: left out, and counted
    ms = [ins.qubits[0] for ins in out.data if ins.operation.name == "measure"]
    tail = out.copy()
    tail.cz(ms[0], ms[1])
    tail.sx(ms[1])
    eq = equivalence(qc, tail)
    assert eq["equivalent"] is True and eq["trailing"] == 2
    # but a measurement after such a gate is not a final measurement
    again = tail.copy()
    again.measure(ms[1], 0)
    assert equivalence(qc, again)["checked"] is False


@pytest.mark.skipif(importlib.util.find_spec("pytket") is None, reason="needs pytket and pytket-qiskit")
def test_tket_reads_pauli_evolution_with_qiskits_conventions():
    """With commuting terms the order does not matter, so TKET's reading must equal Qiskit's gate exactly: the same
    time (U = exp(-i t H)) and the same qubit for each Pauli letter."""
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import PauliEvolutionGate
    from qiskit.quantum_info import Operator, SparsePauliOp
    from toqb.adapters import TketAdapter
    for labels, coeffs in ((["IIZ", "IZZ", "ZII"], [0.3, 0.7, -0.2]), (["IYX"], [0.4]), (["XXI", "YYI"], [0.5, 0.25])):
        qc = QuantumCircuit(3)
        qc.append(PauliEvolutionGate(SparsePauliOp(labels, coeffs), time=0.9), range(3))
        reading = TketAdapter(2).reference_input(qc)
        assert Operator(reading).equiv(Operator(qc)), labels


@pytest.mark.skipif(not os.environ.get("TOQB_BENCHPRESS"), reason="needs a Benchpress clone in $TOQB_BENCHPRESS")
def test_standard_sample_is_disjoint_from_psf_zero_development():
    from toqb import benchpress_source as B
    drawn = B.sample(B.clone(), "a test seed, not the real one")
    ids = [t for _, t in drawn]
    assert len(ids) == len(set(ids)) == 126
    assert not set(ids) & B.dev_tests()
    assert set(ids) <= B.published()


def test_score_and_verify_agree_on_synthetic_records(tmp_path):
    """The scoring script and the independent re-scoring give the same numbers; a smoke-sized run fails P0."""
    import random
    from toqb import score as SC
    rng = random.Random(3)
    adapters = ["qiskit:2:target", "qiskit:1:target", "qiskit:3:target", "tket:2", "psf:default", "psf:recommended"]
    ids = ([f"test_QASMBench_small[x{i}-linear]" for i in range(4)]
           + [f"test_hamlib_hamiltonians_transpile[ham_{i}]" for i in range(3)])
    meta = dict(start_utc="2026-10-08T00:00:00Z", python="3", platform="x", cpus=1, par=1, reference=adapters[0],
                plan=dict(adapters=adapters[1:], drawn=ids), tiers=[1.0, 3.0, 10.0], floor_s=0.05, lock=True)
    lines = [dict(meta=meta)]
    for a in adapters:
        for t in ids:
            r = dict(adapter=a, case="bp:" + t, device="bp:" + t, t_s=rng.uniform(0.01, 0.5), valid=True,
                     q2=rng.randint(5, 50), d2=rng.randint(3, 30), on_failed=0,
                     equivalence=dict(checked=True, equivalent=True, trailing=0))
            if a == "tket:2" and t.endswith("x1-linear]"):
                r = dict(adapter=a, case=r["case"], device=r["device"], error="timeout")
            lines.append(r)
    (tmp_path / "records.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
    S = SC.score(str(tmp_path))
    assert S["P0"]["verdict"] == "FAIL"
    (tmp_path / "score.json").write_text(json.dumps(S, default=str), encoding="utf-8")
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    p = subprocess.run([sys.executable, "-m", "toqb.verify", "--out", str(tmp_path)], capture_output=True, text=True,
                       cwd=root)
    assert "VERIFY PASS" in p.stdout, p.stdout + p.stderr


@pytest.mark.skipif(not os.path.exists("/proc/self/status"), reason="needs Linux /proc")
def test_memory_cap_stops_a_measurement(tmp_path, monkeypatch):
    """A measurement whose resident memory exceeds the cap is stopped and recorded as an error; its peak is kept."""
    import types
    fake = tmp_path / "alloc.sh"
    fake.write_text("#!/bin/sh\nexec " + sys.executable + " -c \"import time; x = bytearray(300 * 2**20); "
                    "x[::4096] = b'1' * len(x[::4096]); time.sleep(5); print('{}')\"\n", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setattr(R, "sys", types.SimpleNamespace(executable=str(fake)))
    rec = R.measure("a", "bp:x", "d", 60, mem_cap_gb=0.1)
    assert rec["error"] == "memory limit 0.1 GB" and rec["peak_rss_mb"] >= 100 and rec["wall_s"] < 5


@pytest.mark.skipif(importlib.util.find_spec("pytket") is None, reason="needs pytket and pytket-qiskit")
def test_tket_takes_a_gate_defined_in_the_input():
    """A gate defined in the input (as QASMBench's ctu or add4) is expanded before conversion, and the output is
    equivalent."""
    from qiskit import QuantumCircuit
    from toqb.adapters import TketAdapter
    from toqb.devices import get_device
    from toqb.metrics import equivalence
    sub = QuantumCircuit(2, name="mygate")
    sub.h(0)
    sub.cx(0, 1)
    sub.rz(0.3, 1)
    qc = QuantumCircuit(3)
    qc.append(sub.to_gate(), [0, 2])
    qc.append(sub.to_gate(), [1, 2])
    out = TketAdapter(2).compile(qc, get_device("linear:4"))
    assert equivalence(qc, out)["equivalent"] is True
