"""gpu/calib_beside.py offline (workplace review 2026-11-06, 06m item 1): FakeFez only, no IBM."""
import os
import sys

import pytest

pytest.importorskip("qiskit_ibm_runtime")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gpu"))
import calib_beside as C  # noqa: E402


def _runs(tmp_path):
    from qiskit import QuantumCircuit, qpy
    for name, pairs in (("p2d_a", [(26, 27), (20, 21)]), ("p2d_b", [(106, 107), (105, 117)])):
        qc = QuantumCircuit(156, 2)
        for a, b in pairs:
            qc.cz(a, b)
        qc.measure(pairs[0][0], 0)
        qc.measure(pairs[0][1], 1)
        for suf in ("", "_floor", "_mirror"):
            with open(tmp_path / f"{name}{suf}.qpy", "wb") as f:
                qpy.dump(qc, f)
    return str(tmp_path)


def _faulty_fez():
    """FakeFez with coupler 106-107 marked non-operational, and the live-style Target built from it."""
    from qiskit_ibm_runtime.fake_provider import FakeFez
    from qiskit_ibm_runtime.models import BackendProperties
    from qiskit_ibm_runtime.utils.backend_converter import convert_to_target
    b = FakeFez()
    d = b.properties().to_dict()
    for g in d["gates"]:
        if g["gate"] == "cz" and sorted(g["qubits"]) == [106, 107]:
            g["parameters"].append(dict(date=g["parameters"][0]["date"], name="operational", unit="", value=0))
    p = BackendProperties.from_dict(d)
    return p, convert_to_target(b.configuration(), p)


def test_groups_roles_into_arms(tmp_path):
    A = C.arms(_runs(tmp_path))
    assert sorted(A) == ["p2d_a", "p2d_b"]
    assert A["p2d_b"]["records"] == ["p2d_b", "p2d_b_floor", "p2d_b_mirror"]
    assert A["p2d_b"]["pairs"] == {(106, 107), (105, 117)}


def test_snapshot_dead_coupler_is_the_worst(tmp_path):
    from qiskit_ibm_runtime.fake_provider import FakeFez
    A = C.arms(_runs(tmp_path))
    r = C.worst(FakeFez().target, "cz", A["p2d_b"]["pairs"])
    assert r["at"] == [106, 107] and r["worst"] == pytest.approx(1.0) and r["missing"] == 0


def test_filtered_target_lists_the_missing_element(tmp_path):
    p, t = _faulty_fez()
    A = C.arms(_runs(tmp_path))
    r = C.worst(t, "cz", A["p2d_b"]["pairs"])
    assert r["at"] == [105, 117]          # the live Target drops 106-107 ...
    assert r["missing_at"] == [[106, 107]]  # ... so it must be listed, not lost
    q = C.worst_props(p, "cz", A["p2d_b"]["pairs"])
    assert q["at"] == [106, 107] and q["non_operational"] == [[106, 107]]
