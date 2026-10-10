"""Tests of TOQB v13's changes (2026-10-10): the stack dump taken with the interpreter's lock held, each process's
exit code, and the structural check and two-qubit count through control flow."""
import os
import sys
import types

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from toqb import runner as R  # noqa: E402


def test_no_faulthandler_timer_in_the_child():
    src = open(os.path.join(ROOT, "toqb", "runner.py"), encoding="utf-8").read()
    assert "dump_traceback_later" not in src.replace("faulthandler.dump_traceback_later read", "")


def test_python_stack_dump_is_read_by_stack_from(capsys):
    import threading

    def inner():
        R._dump_main_stack(threading.main_thread().ident)

    def one():  # named as the runner's child function, which stack_from looks for
        inner()

    one()
    err = capsys.readouterr().err if capsys is not None else ""
    stack = R.stack_from(err)
    assert stack and stack[0].endswith(" _dump_main_stack") and any(f.endswith(" one") for f in stack)


def fake_python(tmp_path, body):
    f = tmp_path / "fake.sh"
    f.write_text("#!/bin/sh\nexec " + sys.executable + " -c \"" + body + "\"\n", encoding="utf-8")
    f.chmod(0o755)
    return types.SimpleNamespace(executable=str(f))


@pytest.mark.skipif(not os.path.exists("/proc/self/status"), reason="needs Linux /proc")
def test_exit_code_of_a_process_without_a_record(tmp_path, monkeypatch):
    # os._exit does not flush Python's buffers, so the message is flushed first
    monkeypatch.setattr(R, "sys", fake_python(tmp_path, "import os, sys; sys.stderr.write('boom'); sys.stderr.flush(); "
                                                        "os._exit(7)"))
    rec = R.measure("a", "bp:x", "d", 1.0)
    assert rec["exit_code"] == 7 and rec["error"].startswith("no record (exit code 7): ") and "boom" in rec["error"]


@pytest.mark.skipif(not os.path.exists("/proc/self/status"), reason="needs Linux /proc")
def test_exit_code_of_a_normal_record(tmp_path, monkeypatch):
    body = "import json; print(json.dumps(dict(adapter='a', case='bp:x', device='d', t_s=0.1, valid=True, q2=3)))"
    monkeypatch.setattr(R, "sys", fake_python(tmp_path, body))
    rec = R.measure("a", "bp:x", "d", 1.0)
    assert rec["exit_code"] == 0 and "error" not in rec and rec["q2"] == 3


def _device(n=3, edges=((0, 1), (1, 2)), basis=("cx", "rz", "sx", "x")):
    return types.SimpleNamespace(basis=list(basis), edges=list(edges), num_qubits=n, two_qubit_gate="cx",
                                 failed_edges=set(), failed_qubits=set(), target=None)


def test_structural_check_through_control_flow():
    qiskit = pytest.importorskip("qiskit")
    from toqb.metrics import metrics, structural_check
    qc = qiskit.QuantumCircuit(3, 1)
    qc.cx(0, 1)
    qc.measure(0, 0)
    with qc.if_test((qc.clbits[0], 1)):
        qc.cx(1, 2)
        qc.x(0)
    dev = _device()
    assert structural_check(qc, dev) is None
    assert metrics(qc, dev)["q2"] == 2  # the body's gate is counted
    bad = qiskit.QuantumCircuit(3, 1)
    bad.measure(0, 0)
    with bad.if_test((bad.clbits[0], 1)):
        bad.cx(0, 2)  # not a coupled pair
    assert structural_check(bad, dev) == "in if_else: cx on (0, 2), not a coupled pair"
    h = qiskit.QuantumCircuit(3, 1)
    h.measure(0, 0)
    with h.if_test((h.clbits[0], 1)):
        h.h(1)  # not in the basis
    assert structural_check(h, dev) == "in if_else: operation h not in the basis"


def test_run2_scoring_on_run_1c():
    """score_run2 on run 1c's own records: S2 compares run 1c with itself; S3 reproduces run 1c's 2.53 on 17."""
    from toqb import score_run2 as S2
    S = S2.score2(S2.RUN1C)
    p = S["predictions"]
    assert p["S2"]["verdict"] == "CONFIRMED" and p["S2"]["value"]["tests"] == 122
    assert p["S3"]["n"] == 17 and abs(p["S3"]["value"] - 2.5326) < 1e-3
    assert p["S1"]["verdict"] == "REFUTED"  # run 1c's four outputs with classical control, under v12b's check
    assert set(S["run1c"]) == set(S["adapters"])
