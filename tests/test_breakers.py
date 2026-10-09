"""Tests of the circuit breakers of amendment 1 (no quantum package needed)."""
import json
import os
import subprocess
import sys
import textwrap
import types

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from toqb import runner as R  # noqa: E402


def test_budgets_are_capped():
    assert R.budgets(0.2) == {1.0: pytest.approx(0.2), 3.0: pytest.approx(0.6), 10.0: pytest.approx(2.0)}
    assert R.budgets(100.0) == {1.0: 100.0, 3.0: 300.0, 10.0: 600.0}
    assert R.budgets(250.0) == {1.0: 250.0, 3.0: 600.0, 10.0: 600.0}
    assert R.within({"t_s": 700.0, "valid": True}, 100.0) == {1.0: False, 3.0: False, 10.0: False}
    assert R.within({"t_s": 590.0, "valid": True}, 100.0) == {1.0: False, 3.0: False, 10.0: True}


def test_limits_and_bounds():
    assert R.compile_limits(0.5) == (30.5, 4.0, 4.0)  # timed compiles: at least 2 LONG_S
    assert R.compile_limits(600.0) == (630.0, 600.0, 600.0)
    assert R.bound_s(600.0) == 630.0 + 600.0 + R.CHECK_LIMIT_S + R.JOB_OVERHEAD_S
    assert R.backstop_s(600.0) == R.BUILD_S + 630.0 + 600.0 + R.CHECK_LIMIT_S


# ------------------------------------------------------------------ the child, with fake toqb modules

FAKES = textwrap.dedent('''
    import sys, time, types
    def mod(name, **kw):
        m = types.ModuleType(name); m.__dict__.update(kw); sys.modules[name] = m
    class A:
        def __init__(self, name): self.name = name
        def version(self): return "fake"
        def compile(self, c, d):
            time.sleep(COMPILE_S.pop(0) if COMPILE_S else 0.0)
            return "out"
    mod("toqb.adapters", make_adapter=lambda n: A(n))
    class QC:
        num_qubits = 3
        data = [types.SimpleNamespace(qubits=(0, 1)), types.SimpleNamespace(qubits=(0,)),
                types.SimpleNamespace(qubits=(0, 1, 2))]
    mod("toqb.cases", get_case=lambda c: QC())
    mod("toqb.devices", get_device=lambda d: "device")
    def equivalence(c, o, reference=None):
        time.sleep(CHECK_S)
        return dict(checked=True, equivalent=True)
    mod("toqb.metrics", equivalence=equivalence, metrics=lambda o, d: dict(q2=7), structural_check=lambda o, d: None)
''')


def run_child(compile_s, check_s, b10_s, patch="", profile=None, with_stderr=False):
    code = (f"COMPILE_S = {compile_s!r}\nCHECK_S = {check_s!r}\n" + FAKES + patch
            + "import argparse\nfrom toqb import runner as R\n"
            + f"R.one(argparse.Namespace(adapter='a', case='c', device='d', b10_s={b10_s!r}, profile={profile!r}))\n")
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT, timeout=60)
    lines = [json.loads(ln) for ln in p.stdout.splitlines() if ln.startswith("{")]
    assert len(lines) == 2 and lines[0] == {"features": {"qubits": 3, "size": 3, "two_qubit": 1, "wider": 1}}, \
        p.stdout + p.stderr
    assert lines[1]["features"] == lines[0]["features"]
    return (lines[1], p.returncode, p.stderr) if with_stderr else (lines[1], p.returncode)


def test_child_normal_measurement():
    rec, code = run_child([0.01] * 6, 0.0, 1.0)
    assert code == 0 and "error" not in rec and len(rec["times_s"]) == R.REPEATS
    assert rec["equivalence"] == {"checked": True, "equivalent": True}


def test_child_warmup_over_its_limit_is_a_time_failure():
    rec, code = run_child([3.0], 0.0, 0.05, patch="import toqb.runner as RR; RR.WARMUP_GRACE_S = 0.5\n")
    assert code == 3 and rec["error"].startswith("time: compile 0 over")


def test_child_timed_compile_over_its_limit_is_a_time_failure():
    # a long warm-up (one timed compile follows); the timed compile passes max(B10, 2 LONG_S) = 4 s
    rec, code = run_child([2.5, 6.0], 0.0, 0.05)
    assert code == 3 and rec["error"].startswith("time: compile 1 over 4 s")


def test_child_repeats_end_when_their_sum_passes_the_limit():
    # short warm-up, so REPEATS timed compiles; 1.5 s each: the sum passes 4 s after three
    rec, code = run_child([0.1, 1.5, 1.5, 1.5, 1.5, 1.5], 0.0, 0.05)
    assert code == 0 and "error" not in rec and len(rec["times_s"]) == 3


def test_child_check_over_its_limit_is_unchecked_not_a_failure():
    rec, code = run_child([0.01] * 6, 5.0, 1.0, patch="import toqb.runner as RR; RR.CHECK_LIMIT_S = 0.5\n")
    assert code == 0 and "error" not in rec and rec["q2"] == 7
    assert rec["equivalence"] == {"checked": False, "why": "check over 0.5 s"}


# ------------------------------------------------------------------ the parent

def fake_python(tmp_path, body):
    f = tmp_path / "fake.sh"
    f.write_text("#!/bin/sh\nexec " + sys.executable + " -c \"" + body + "\"\n", encoding="utf-8")
    f.chmod(0o755)
    return types.SimpleNamespace(executable=str(f))


@pytest.mark.skipif(not os.path.exists("/proc/self/status"), reason="needs Linux /proc")
def test_backstop_stops_a_process_that_outlives_its_limits(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "sys", fake_python(tmp_path, "import time; time.sleep(30)"))
    monkeypatch.setattr(R, "BUILD_S", 0.0)
    monkeypatch.setattr(R, "WARMUP_GRACE_S", 0.0)
    monkeypatch.setattr(R, "CHECK_LIMIT_S", 0.0)
    rec = R.measure("a", "bp:x", "d", 0.5)  # backstop 0.5 + 4.0
    assert rec["error"].startswith("time: harness backstop") and rec["wall_s"] < 10 and rec["b10_s"] == 0.5


@pytest.mark.skipif(not os.path.exists("/proc/self/status"), reason="needs Linux /proc")
def test_machine_breaker_interrupts_the_largest(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "sys", fake_python(tmp_path, "import time; x = bytearray(200 * 2**20); "
                                                        "x[::4096] = b'1' * len(x[::4096]); time.sleep(30)"))
    monkeypatch.setattr(R, "_available_mb", lambda: 10)
    import threading
    stop = threading.Event()
    said = []
    t = threading.Thread(target=R._breaker, args=(stop, said.append), daemon=True)
    t.start()
    try:
        rec = R.measure("a", "bp:x", "d", 600.0)
    finally:
        stop.set()
    assert rec["error"].startswith("interrupted: machine memory") and rec["wall_s"] < 20
    assert said and "machine breaker" in said[0]


# ------------------------------------------------------------------ the run, with measure() replaced

def fake_run(tmp_path, monkeypatch, ref_t=0.1, times=None, interrupt=(), budget_h=10.0, stop_after=None,
             fail_ref=()):
    calls = []

    def measure(adapter, case, device, b10_s, mem_cap_gb=None):
        calls.append((adapter, case, b10_s))
        if stop_after is not None and len(calls) == stop_after:
            (tmp_path / "out" / "STOP").write_text("")
        if adapter == R.REFERENCE:
            if case in fail_ref:
                return dict(adapter=adapter, case=case, device=device, error="time: compile 0 over 630 s")
            return dict(adapter=adapter, case=case, device=device, t_s=ref_t, valid=True, q2=10)
        if (adapter, case) in interrupt and sum(1 for c in calls if c[:2] == (adapter, case)) == 1:
            return dict(adapter=adapter, case=case, device=device, error="interrupted: machine memory")
        return dict(adapter=adapter, case=case, device=device, t_s=(times or {}).get(adapter, 0.1), valid=True,
                    q2=12, b10_s=b10_s)

    monkeypatch.setattr(R, "measure", measure)
    monkeypatch.setattr(R, "provenance", lambda: {})
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(dict(adapters=["x", "y"], pairs=[["c1", "d"], ["c2", "d"], ["c3", "d"]])))
    args = types.SimpleNamespace(plan=str(plan), out=str(tmp_path / "out"), par=2, lock=False, seed_file=None,
                                 mem_cap_gb=3.0, run_budget_h=budget_h)
    R.run(args)
    lines = [json.loads(x) for x in open(tmp_path / "out" / "records.jsonl", encoding="utf-8")]
    return lines, calls


def test_run_complete(tmp_path, monkeypatch):
    lines, calls = fake_run(tmp_path, monkeypatch)
    end = lines[-1]["end"]
    assert end["complete"] is True and end["stopped"] is None and len(lines) == 2 + 9
    assert lines[0]["meta"]["b10_cap_s"] == 600.0 and lines[0]["meta"]["check_limit_s"] == R.CHECK_LIMIT_S
    assert all(c[2] == pytest.approx(1.0) for c in calls if c[0] != R.REFERENCE)  # 10 x 0.1
    assert {c[2] for c in calls if c[0] == R.REFERENCE} == {R.REF_LIMIT_S}


def test_run_reference_failure_writes_not_run_records(tmp_path, monkeypatch):
    lines, calls = fake_run(tmp_path, monkeypatch, fail_ref=("c2",))
    recs = [x for x in lines if "adapter" in x]
    assert len(recs) == 9 and lines[-1]["end"]["complete"] is True
    assert sorted(r["adapter"] for r in recs if r.get("error") == R.NOT_RUN) == ["x", "y"]
    assert not any(c[1] == "c2" and c[0] != R.REFERENCE for c in calls)


def test_run_interrupted_measurement_runs_again(tmp_path, monkeypatch):
    lines, calls = fake_run(tmp_path, monkeypatch, interrupt=(("x", "c1"),))
    recs = [x for x in lines if "adapter" in x]
    again = [r for r in recs if r.get("run_again_after_interruption")]
    assert len(recs) == 9 and len(again) == 1 and "error" not in again[0]
    first = [json.loads(x) for x in open(tmp_path / "out" / "interrupted.jsonl", encoding="utf-8")]
    assert len(first) == 1 and first[0]["error"].startswith("interrupted")
    assert lines[-1]["end"]["complete"] is True


def test_run_stop_file(tmp_path, monkeypatch):
    lines, calls = fake_run(tmp_path, monkeypatch, stop_after=4)
    end = lines[-1]["end"]
    assert end["complete"] is False and end["stopped"] == "STOP file" and end["not_started"] > 0


def test_run_bound_over_budget_stops_after_references(tmp_path, monkeypatch):
    # references of 100 s: B10 600 s each; 6 measurements, 2 at a time: bound > 3,000 s > 0.5 h
    lines, calls = fake_run(tmp_path, monkeypatch, ref_t=100.0, budget_h=0.5)
    end = lines[-1]["end"]
    assert end["complete"] is False and end["stopped"].startswith("bound on the run")
    assert all(c[0] == R.REFERENCE for c in calls) and end["not_started"] == 6


# ------------------------------------------------------------------ scoring under amendment 1

def synthetic_run(tmp_path, n_tests=20, slow_ref=(), psf_time_fail=(), ref_fail=()):
    from toqb import score as SC
    adapters = SC.EXPECTED["adapters"]
    ids = [f"test_QASMBench_small[x{i}-linear]" for i in range(n_tests)]
    meta = dict(start_utc="2026-10-09T00:00:00Z", python="3", platform="x", cpus=1, par=1, reference=adapters[0],
                plan=dict(adapters=adapters[1:], drawn=ids), tiers=[1.0, 3.0, 10.0], floor_s=0.05, lock=True,
                **SC.EXPECTED["rules"])
    lines = [dict(meta=meta)]
    for a in adapters:
        for i, t in enumerate(ids):
            case = "bp:" + t
            r = dict(adapter=a, case=case, device=case, t_s=0.1, valid=True, q2=10, d2=5, on_failed=0,
                     equivalence=dict(checked=True, equivalent=True, trailing=0))
            if a == adapters[0] and i in slow_ref:
                r["t_s"] = 100.0
            if a == adapters[0] and i in ref_fail:
                r = dict(adapter=a, case=case, device=case, error="time: compile 0 over 630 s")
            elif i in ref_fail:
                r = dict(adapter=a, case=case, device=case, error=R.NOT_RUN)
            elif a == "psf:default" and i in psf_time_fail:
                r = dict(adapter=a, case=case, device=case, error="time: compile 1 over 600 s")
            lines.append(r)
    lines.append(dict(end=dict(end_utc="x", wall_s=1.0, complete=True, stopped=None, not_started=0)))
    (tmp_path / "records.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
    S = SC.score(str(tmp_path))
    (tmp_path / "score.json").write_text(json.dumps(S, default=str), encoding="utf-8")
    p = subprocess.run([sys.executable, "-m", "toqb.verify", "--out", str(tmp_path)], capture_output=True, text=True,
                       cwd=ROOT)
    assert "VERIFY PASS" in p.stdout, p.stdout + p.stderr
    SC.markdown(S)  # renders
    return S


def test_score_bounds_decide_when_the_cap_cannot_matter(tmp_path):
    # 20 tests; psf:default stopped by time on 1 whose reference took 100 s: within 10x 19/20 = 0.95, at most 1.00
    S = synthetic_run(tmp_path, slow_ref=(3,), psf_time_fail=(3,))
    t3, t6 = S["predictions"]["T3"], S["predictions"]["T6"]
    assert t3["bounds"] == (pytest.approx(0.95), pytest.approx(1.0)) and t3["verdict"] == "CONFIRMED"
    assert t6["bounds"] == (pytest.approx(0.0), pytest.approx(0.05))
    assert t6["verdict"] == "NOT DECIDED (the cap of amendment 1)"
    assert S["adapters"]["psf:default"]["failed_time"] == 1


def test_score_not_run_records_are_not_failures(tmp_path):
    S = synthetic_run(tmp_path, ref_fail=(0,))
    row = S["adapters"]["psf:default"]
    assert row["not_run"] == 1 and row["failed"] == 0 and row["reference_finished"] == 19
    assert S["P0"]["checks"]["the circuit breakers of amendment 1"] is True
    assert S["P0"]["checks"]["the run is complete (not stopped by a STOP file or the run budget)"] is True


def test_child_stack_dump_before_a_stop(tmp_path):
    rec, code, err = run_child([3.0], 0.0, 0.05, patch="import toqb.runner as RR; RR.WARMUP_GRACE_S = 1.0\n",
                               profile=str(tmp_path / "p.prof"), with_stderr=True)
    assert code == 3 and rec["error"].startswith("time: compile 0")
    stack = R.stack_from(err)
    assert stack and any(f.endswith(" compile") for f in stack) and any(f.endswith(" one") for f in stack)
    assert (tmp_path / "p.prof").exists()  # the profile is written although the compile was stopped
    import pstats
    assert pstats.Stats(str(tmp_path / "p.prof")).total_calls >= 1


def test_redact_and_stack_parsing():
    assert R._redact('File "/home/someone/x.py"') == 'File "/home/<user>/x.py"'
    assert R._redact("C:\\Users\\someone\\a.py") == "C:\\Users\\<user>\\a.py"
    err = ('Thread 0x1 (most recent call first):\n  File "/usr/lib/python3/threading.py", line 1 in wait\n'
           'Current thread 0x2 (most recent call first):\n'
           '  File "/home/u/v/lib/python3.12/site-packages/pytket/x.py", line 9 in apply\n'
           '  File "/home/u/toqb/toqb/runner.py", line 170 in one\n')
    assert R.stack_from(err) == ["pytket/x.py:9 apply", "runner.py:170 one"]


def test_weakness_report_groups_and_reproduces(tmp_path):
    from toqb import weakness as W
    f_big = dict(qubits=16, size=500000, two_qubit=110000, wider=0)
    f_small = dict(qubits=5, size=50, two_qubit=20, wider=0)
    recs = [dict(meta={})]
    for i, f in enumerate((f_big, f_big, f_small)):
        case = f"bp:test_feynman_transpile[c{i}.qasm]"
        recs.append(dict(adapter=W.REFERENCE, case=case, device=case, t_s=1.0, q2=100, valid=True, features=f))
        if i < 2:
            recs.append(dict(adapter="psf:recommended", case=case, device=case, error="time: compile 0 over 40 s",
                             b10_s=10.0, features=f, stack_at_stop=["psf_compile.py:2019 excitation_cost",
                                                                    "psf_compile.py:2800 _select_resynthesis",
                                                                    "runner.py:170 one"]))
        else:
            recs.append(dict(adapter="psf:recommended", case=case, device=case, t_s=5.0, q2=150, valid=True,
                             equivalence=dict(checked=True, equivalent=True)))
    recs.append('{"adapter": "tket:2", "ca')  # a line cut short is skipped
    (tmp_path / "records.jsonl").write_text("".join((json.dumps(x) if isinstance(x, dict) else x) + "\n"
                                                    for x in recs), encoding="utf-8")
    txt = W.report(W.load([str(tmp_path)]))
    assert ("| psf:recommended | time | psf_compile.py:2019 excitation_cost | 2q >=100k | qubits <=16 | "
            "Feynman, FakeTorino | 2 |") in txt
    assert "| psf:recommended | 2q <100 | qubits <=16 | Feynman, FakeTorino | 1 | 5.0 |" in txt
    assert "| psf:recommended | 2q <100 | qubits <=16 | Feynman, FakeTorino | 1 | 1.50 |" in txt
    assert "--adapter psf:recommended --case 'bp:test_feynman_transpile[c0.qasm]'" in txt and "--b10-s 10" in txt
