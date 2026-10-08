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
                        "--device", "linear:5", "--limit-s", "60"], capture_output=True, text=True, cwd=root)
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
