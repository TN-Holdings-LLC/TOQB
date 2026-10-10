"""The budgeted runner.

One process per (adapter, case, device). In it: build the circuit and the device (not timed), one warm-up compile
(discarded), then REPEATS timed compiles (one, if the warm-up took longer than LONG_S); the fastest and the slowest
are dropped and the rest averaged. Budgets are multiples (TIERS) of the reference compiler's averaged time on the same
case and device, the reference time being taken as at least BUDGET_FLOOR_S, and no budget above B10_CAP_S.

Circuit breakers (amendment 1 of the standard run's pre-registration; nothing is measured past what scoring needs):
  - a compile is stopped at the largest budget B10 (the warm-up at B10 + WARMUP_GRACE_S; timed compiles at
    max(B10, 2 LONG_S), and the timed repeats end once their sum passes that): the measurement fails ("time: ...");
  - the reference's own compiles stop at REF_LIMIT_S; a test whose reference fails is left out of every score;
  - the equivalence check stops at CHECK_LIMIT_S: the output is recorded as unchecked, not as a failure;
  - with --mem-cap-gb, a measurement whose resident memory exceeds the cap fails ("memory limit ...");
  - the parent kills a process that outlives all of these by more than BUILD_S ("time: harness backstop ...");
  - if the machine's available memory falls below MIN_AVAILABLE_MB, the running measurement with the most resident
    memory is stopped ("interrupted: ..."), and run again alone after the others; the second result is the record;
  - a file named STOP in the output directory, or the run budget (--run-budget-h), stops new measurements; the run
    is then incomplete, and is not scored;
  - after the reference's measurements, a bound on the rest of the run is computed from the budgets; if it exceeds
    the run budget, the run stops there.

    python -m toqb.runner one  --adapter qiskit:2:target --case qft:8 --device fake:FakeTorino [--b10-s 60]
    python -m toqb.runner run  --plan plan.json --out DIR [--par 4] [--lock] [--mem-cap-gb G] [--run-budget-h H]
    python -m toqb.runner summary --out DIR
    python -m toqb.runner commit --seed-file FILE     the commitment (SHA-256) of a secret seed, for a plan

plan.json: {"adapters": [...]} and any of
    "cases" + "devices"          every case on every device
    "pairs": [[case, device]]    given pairs
    "benchpress_standard": {"seed_sha256": H}
                                 the standard Benchpress sample (toqb.benchpress_source.sample), drawn from the
                                 seed in --seed-file, which must hash to H; each test is its own case and device
The reference adapter is added if missing. Records are written as each measurement finishes, with a progress line on
stderr. The run records its provenance (git heads, uncommitted changes, package versions); with --lock it stops if
TOQB, PSF-Zero or Benchpress has an uncommitted change to a tracked file. Every measurement's peak memory is recorded,
and the machine's memory is logged every 30 s in memlog.tsv (Linux).
"""
from __future__ import annotations

import argparse
import faulthandler
import json
import math
import os
import platform
import re
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

REFERENCE = "qiskit:2:target"
TIERS = (1.0, 3.0, 10.0)
BUDGET_FLOOR_S = 0.05
REPEATS = 5
LONG_S = 2.0  # a warm-up compile longer than this is followed by one timed compile, not REPEATS
B10_CAP_S = 600.0  # no budget exceeds this (amendment 1): the 10x tier is min(10 x max(floor, reference), 600 s)
WARMUP_GRACE_S = 30.0  # the warm-up compile (cold) may run this much longer than the largest budget
REF_LIMIT_S = 600.0  # the reference's compiles stop here; the test is then left out
CHECK_LIMIT_S = 60.0  # the equivalence check stops here; the output is recorded as unchecked
BUILD_S = 120.0  # building the case and device and starting Python: only the parent's backstop allows for it
JOB_OVERHEAD_S = 10.0  # per measurement, in the bound on the run's time (starting and building; an estimate)
MIN_AVAILABLE_MB = 1536  # below this, the machine breaker stops the measurement with the most resident memory
NOT_RUN = "not run: the reference failed"  # the record of another compiler on a test without a reference time
ONE_THREAD = dict(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", RAYON_NUM_THREADS="1",
                  QISKIT_PARALLEL="FALSE", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")


def trimmed_mean(times):
    """Mean after dropping the fastest and the slowest (when there are at least three)."""
    ts = sorted(times)
    if len(ts) >= 3:
        ts = ts[1:-1]
    return sum(ts) / len(ts)


def budgets(ref_time_s):
    """{tier: budget in seconds} for a reference time. The reference time is taken as at least BUDGET_FLOOR_S, so
    that the tiers stay apart on circuits the reference compiles in a few milliseconds; no budget exceeds B10_CAP_S."""
    return {t: min(t * max(BUDGET_FLOOR_S, ref_time_s), B10_CAP_S) for t in TIERS}


def compile_limits(b10_s):
    """(the warm-up's limit, a timed compile's limit and the timed compiles' total) for a largest budget."""
    timed = max(b10_s, 2 * LONG_S)
    return b10_s + WARMUP_GRACE_S, timed, timed


def bound_s(b10_s):
    """A bound on one measurement's compiles and check, plus JOB_OVERHEAD_S (for the run's bound)."""
    warm, _, total = compile_limits(b10_s)
    return warm + total + CHECK_LIMIT_S + JOB_OVERHEAD_S


def backstop_s(b10_s):
    """The wall-clock time after which the parent kills a measurement's process."""
    warm, _, total = compile_limits(b10_s)
    return BUILD_S + warm + total + CHECK_LIMIT_S


def not_equivalent(record):
    """True if the equivalence check was made and failed."""
    eq = record.get("equivalence") or {}
    return eq.get("checked") is True and eq.get("equivalent") is False


def within(record, ref_time_s):
    """{tier: True/False} for a measurement record (False if it failed, is invalid or is not equivalent)."""
    ok = "error" not in record and record.get("valid") is True and not not_equivalent(record)
    return {t: bool(ok and record["t_s"] <= b) for t, b in budgets(ref_time_s).items()}


def gmean(xs):
    xs = list(xs)
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else float("nan")


# ------------------------------------------------------------------ the child process

def _features(qc):
    """What the weakness report groups by: the input's qubits, instructions, two-qubit and wider instructions."""
    n2 = wider = 0
    for ins in qc.data:
        k = len(ins.qubits)
        n2 += k == 2
        wider += k > 2
    return dict(qubits=qc.num_qubits, size=len(qc.data), two_qubit=n2, wider=wider)


class _Once:
    """Whoever claims it first writes the measurement's one record (the main thread or a watchdog)."""

    def __init__(self):
        self._lock = threading.Lock()

    def claim(self):
        return self._lock.acquire(blocking=False)


def _dump_main_stack(main_id):
    """The main thread's stack, in faulthandler's text format (which stack_from reads), written to stderr by a Python
    thread, that is with the interpreter's lock held. v13: amendment 1's faulthandler.dump_traceback_later read the
    stacks from a C thread without that lock, which can crash the process; two measurements of standard run 1c
    probably ended that way. If the main thread holds the lock in native code, the dump waits for it (or never
    happens): it is a diagnostic only."""
    frame = sys._current_frames().get(main_id)
    lines = [f"Thread 0x{main_id:016x} (most recent call first):"]
    while frame is not None:
        lines.append(f'  File "{frame.f_code.co_filename}", line {frame.f_lineno} in {frame.f_code.co_name}')
        frame = frame.f_back
    sys.stderr.write("\n".join(lines) + "\n")
    sys.stderr.flush()


def _watchdog(limit_s, on_expire):
    t = threading.Timer(limit_s, on_expire)
    t.daemon = True
    t.start()
    return t


def one(args):
    from toqb.adapters import make_adapter
    from toqb.cases import get_case
    from toqb.devices import get_device
    from toqb.metrics import equivalence, metrics, structural_check
    rec = dict(adapter=args.adapter, case=args.case, device=args.device)
    adapter = make_adapter(args.adapter)
    rec["adapter_version"] = adapter.version()
    circuit, device = get_case(args.case), get_device(args.device)
    # diagnostics for the weakness report, none of them timed: the input's features, written first so that the
    # parent keeps them if it stops the process; a stack dump just before each compile's limit, and on SIGUSR1
    # (the parent sends it before stopping a process over its memory cap)
    rec["features"] = _features(circuit)
    print(json.dumps(dict(features=rec["features"])), flush=True)
    if hasattr(signal, "SIGUSR1"):
        faulthandler.register(signal.SIGUSR1, file=sys.stderr, all_threads=True)
    profiler = None
    if getattr(args, "profile", None):  # repro runs only: profile the warm-up compile, up to its stop
        import cProfile
        profiler = cProfile.Profile()
    once = _Once()

    def emit(r, code):
        if once.claim():
            if profiler is not None:
                profiler.disable()
                profiler.dump_stats(args.profile)
            print(json.dumps(r), flush=True)
            os._exit(code)

    def over(k, lim):
        return lambda: emit(dict(rec, error=f"time: compile {k} over {lim:g} s"), 3)

    warm_lim, timed_lim, timed_total = compile_limits(args.b10_s)
    times, out, runs = [], None, REPEATS + 1
    k = 0
    while k < runs:
        lim = warm_lim if k == 0 else timed_lim
        w = _watchdog(lim, over(k, lim))
        dump = _watchdog(max(lim - 0.5, 0.9 * lim), lambda: _dump_main_stack(threading.main_thread().ident))
        if profiler is not None and k == 0:
            profiler.enable()
        t0 = time.perf_counter()
        out = adapter.compile(circuit, device)
        dt = time.perf_counter() - t0
        if profiler is not None and k == 0:
            profiler.disable()
            profiler.dump_stats(args.profile)
        dump.cancel()
        w.cancel()
        if dt > lim:
            over(k, lim)()
        if k == 0 and dt > LONG_S:
            runs = 2  # a long compile varies little between runs; one timed run after the warm-up
        if k > 0:
            times.append(dt)
            if sum(times) > timed_total:
                break
        k += 1
    rec["times_s"] = [round(t, 6) for t in times]
    rec["t_s"] = trimmed_mean(rec["times_s"])
    problem = structural_check(out, device)
    rec["valid"] = problem is None
    if problem:
        rec["invalid_because"] = problem
    rec.update(metrics(out, device))
    w = _watchdog(CHECK_LIMIT_S, lambda: emit(dict(rec, equivalence=dict(
        checked=False, why=f"check over {CHECK_LIMIT_S:g} s")), 0))
    try:
        # the compiler's own reading of the input, when it differs from Qiskit's (TKET and a PauliEvolutionGate)
        reading = adapter.reference_input(circuit) if hasattr(adapter, "reference_input") else None
        rec["equivalence"] = equivalence(circuit, out, reference=reading)
    except Exception as exc:  # noqa: BLE001 - recorded: the check could not be made
        rec["equivalence"] = dict(checked=False, why=f"{type(exc).__name__}: {exc}"[:200])
    w.cancel()
    if once.claim():
        print(json.dumps(rec), flush=True)
    else:
        time.sleep(60)  # the watchdog is writing the record and ends the process


# ------------------------------------------------------------------ the parent

def _proc_kb(pid, field):
    """A field of /proc/<pid>/status in kB (VmRSS: resident now; VmHWM: the peak so far), or None (not Linux, or the
    process has ended)."""
    try:
        with open(f"/proc/{pid}/status", encoding="ascii") as fh:
            for ln in fh:
                if ln.startswith(field + ":"):
                    return int(ln.split()[1])
    except (OSError, ValueError):
        return None
    return None


def measure(adapter, case, device, b10_s, mem_cap_gb=None):
    """Runs one measurement in its own process, with largest budget b10_s (the child stops its own compiles and
    check). The parent stops the process at backstop_s(b10_s), with mem_cap_gb as soon as its resident memory exceeds
    that many GB, or when the machine breaker picks it; each is recorded as an error. The peak resident memory, and
    for long measurements its trace every 30 s, are recorded (Linux only)."""
    import tempfile
    cmd = [sys.executable, "-m", "toqb.runner", "one", "--adapter", adapter, "--case", case, "--device", device,
           "--b10-s", repr(float(b10_s))]
    env = dict(os.environ, **ONE_THREAD)
    w0 = time.perf_counter()
    limit = backstop_s(b10_s)
    why, peak, trace, next_trace = None, 0, [], 0.0
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        p = subprocess.Popen(cmd, stdout=out, stderr=err, env=env)
        with _RUNNING_GUARD:
            _RUNNING[p.pid] = (adapter, case)
        try:
            while True:
                try:
                    p.wait(timeout=1.0)
                    break
                except subprocess.TimeoutExpired:
                    pass
                el = time.perf_counter() - w0
                rss = _proc_kb(p.pid, "VmRSS")
                peak = max(peak, _proc_kb(p.pid, "VmHWM") or 0, rss or 0)
                if el >= next_trace:
                    trace.append([round(el), round((rss or 0) / 1024)])
                    next_trace += 30.0
                with _RUNNING_GUARD:
                    picked = p.pid in _PRESSURE
                if picked:
                    why = f"interrupted: machine memory below {MIN_AVAILABLE_MB} MB available"
                elif mem_cap_gb and rss and rss > mem_cap_gb * 1024 * 1024:
                    why = f"memory limit {mem_cap_gb:g} GB"
                elif el > limit:
                    why = f"time: harness backstop {limit:.0f} s"
                if why:
                    if not why.startswith("time") and hasattr(signal, "SIGUSR1"):
                        try:  # a stack dump for the weakness report, then the stop
                            p.send_signal(signal.SIGUSR1)
                            p.wait(timeout=1.0)
                        except (OSError, subprocess.TimeoutExpired):
                            pass
                    p.kill()
                    p.wait()
                    break
        finally:
            with _RUNNING_GUARD:
                _RUNNING.pop(p.pid, None)
                _PRESSURE.discard(p.pid)
        out.seek(0)
        err.seek(0)
        stdout = out.read().decode("utf-8", errors="replace")
        stderr = err.read().decode("utf-8", errors="replace")
    objs = []
    for ln in stdout.splitlines():
        if ln.startswith("{"):
            try:
                objs.append(json.loads(ln))
            except ValueError:
                pass
    features = next((o["features"] for o in objs if set(o) == {"features"}), None)
    finals = [o for o in objs if set(o) != {"features"}]
    if why:
        rec = dict(adapter=adapter, case=case, device=device, error=why)
    elif finals:
        rec = finals[-1]
    else:  # v13: the exit code says how a process without a record ended (a negative code: by that signal)
        rec = dict(adapter=adapter, case=case, device=device,
                   error=f"no record (exit code {p.returncode}): " + _redact(stderr[-600:]))
    if features is not None:
        rec.setdefault("features", features)
    if "error" in rec:
        stack = stack_from(stderr)
        if stack:
            rec["stack_at_stop"] = stack
    rec["b10_s"] = round(float(b10_s), 6)
    rec["wall_s"] = round(time.perf_counter() - w0, 3)
    rec["exit_code"] = p.returncode  # v13
    if peak:
        rec["peak_rss_mb"] = round(peak / 1024)
    if len(trace) > 2:
        rec["rss_trace_mb"] = trace
    return rec


_FRAME = re.compile(r'File "(.+)", line (\d+) in (\S+)')


def _short(path):
    """A frame's file without the machine's paths: from the package directory on, or the file name."""
    path = path.replace("\\", "/")
    for mark in ("site-packages/", "dist-packages/"):
        if mark in path:
            return path.split(mark, 1)[1]
    return path.rsplit("/", 1)[-1]


def _redact(text):
    """Error text without the machine's paths (home directories)."""
    return re.sub(r"(/home/|/Users/|[A-Za-z]:\\Users\\)[^/\\\s\"']+", r"\1<user>", text)


def stack_from(stderr, max_frames=25):
    """The main thread's stack (most recent call first) from the last faulthandler dump in stderr, as
    ["file:line function"], or None. The main thread is the dumped thread whose frames include the runner's one()."""
    blocks, cur = [], None
    for ln in stderr.splitlines():
        if ln.startswith(("Thread 0x", "Current thread 0x")):
            cur = []
            blocks.append(cur)
        elif cur is not None:
            m = _FRAME.search(ln)
            if m:
                cur.append(f"{_short(m.group(1))}:{m.group(2)} {m.group(3)}")
            elif ln.strip() and not ln.startswith(" "):
                cur = None
    main = [b for b in blocks if any(f.endswith(" one") and f.startswith("runner.py") for f in b)]
    return (main or blocks or [None])[-1][:max_frames] if blocks else None


_RUNNING = {}  # pid -> (adapter, case) of the measurements in progress, for the memory log
_PRESSURE = set()  # pids the machine breaker has picked; measure() stops them
_RUNNING_GUARD = threading.Lock()


def _available_mb():
    try:
        with open("/proc/meminfo", encoding="ascii") as fh:
            for ln in fh:
                if ln.startswith("MemAvailable:"):
                    return int(ln.split()[1]) // 1024
    except (OSError, ValueError):
        return None
    return None


def _breaker(stop, log):
    """Every 5 s: if the machine's available memory is below MIN_AVAILABLE_MB, picks the running measurement with the
    most resident memory (once per 30 s at most), for measure() to stop. Linux only."""
    last = 0.0
    while not stop.wait(5.0):
        avail = _available_mb()
        if avail is None or avail >= MIN_AVAILABLE_MB or time.monotonic() - last < 30.0:
            continue
        with _RUNNING_GUARD:
            running = [(pid, _proc_kb(pid, "VmRSS") or 0) for pid in _RUNNING if pid not in _PRESSURE]
            if not running:
                continue
            pid = max(running, key=lambda x: x[1])[0]
            _PRESSURE.add(pid)
            what = _RUNNING[pid]
        last = time.monotonic()
        log(f"machine breaker: {avail} MB available; stopping {what[0]} {what[1][:60]}")


def _memlog(path, stop):
    """Every 30 s: the time, the machine's available memory and swap use, and each running measurement's resident
    memory (Linux only), appended to path."""
    while not stop.wait(30.0):
        try:
            info = {}
            with open("/proc/meminfo", encoding="ascii") as fh:
                for ln in fh:
                    k, v = ln.split(":", 1)
                    info[k] = int(v.split()[0])
            with _RUNNING_GUARD:
                running = dict(_RUNNING)
            procs = [f"{a} {c[3:60]} {round((_proc_kb(pid, 'VmRSS') or 0) / 1024)}" for pid, (a, c) in running.items()]
            line = "\t".join([time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                              f"available_mb={info.get('MemAvailable', 0) // 1024}",
                              f"swap_used_mb={(info.get('SwapTotal', 0) - info.get('SwapFree', 0)) // 1024}"] + procs)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        except (OSError, ValueError):
            pass


def _git(path, *args):
    try:
        p = subprocess.run(["git", "-C", path, *args], capture_output=True, text=True, timeout=60)
        return p.stdout.strip() if p.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def provenance():
    """Git head and uncommitted tracked changes of TOQB, PSF-Zero ($PSF_ZERO_REPO) and Benchpress ($TOQB_BENCHPRESS),
    and the versions of the packages that compile or check."""
    from importlib import metadata
    info = {}
    repos = dict(toqb=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 psf_zero=os.environ.get("PSF_ZERO_REPO"), benchpress=os.environ.get("TOQB_BENCHPRESS"))
    for name, path in repos.items():
        if path:
            info[name] = dict(head=_git(path, "rev-parse", "HEAD"),
                              dirty=_git(path, "status", "--porcelain", "--untracked-files=no"))
    versions = {}
    for pkg in ("qiskit", "qiskit-ibm-runtime", "numpy", "scipy", "rustworkx", "pytket", "pytket-qiskit",
                "psf-zero-core57"):  # v13: PSF-Zero's optional Rust module of item 57b
        try:
            versions[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            versions[pkg] = None
    info["versions"] = versions
    return info


def run(args):
    plan = json.load(open(args.plan, encoding="utf-8"))
    adapters = list(dict.fromkeys([REFERENCE] + plan["adapters"]))
    pairs = [(c, d) for c in plan.get("cases", []) for d in plan.get("devices", [])]
    pairs += [tuple(p) for p in plan.get("pairs", [])]
    prov = provenance()
    if args.lock:
        dirty = [n for n, v in prov.items() if isinstance(v, dict) and "dirty" in v and v["dirty"] != ""]
        if dirty:
            raise SystemExit(f"STOP: uncommitted changes (or no git) in {', '.join(dirty)}")
    if "benchpress_standard" in plan:
        from toqb.benchpress_source import clone, sample, seed_commitment
        seed = open(args.seed_file, encoding="utf-8").read().strip()
        if seed_commitment(seed) != plan["benchpress_standard"]["seed_sha256"]:
            raise SystemExit("STOP: the seed does not match the plan's committed hash")
        drawn = sample(clone(), seed)
        pairs += [(f"bp:{tid}", f"bp:{tid}") for _, tid in drawn]
        plan = dict(plan, drawn=[tid for _, tid in drawn])
    os.makedirs(args.out, exist_ok=True)
    meta = dict(start_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), python=sys.version.split()[0],
                platform=platform.platform(), cpus=os.cpu_count(), par=args.par, plan=plan, reference=REFERENCE,
                tiers=TIERS, floor_s=BUDGET_FLOOR_S, repeats=REPEATS, long_s=LONG_S, b10_cap_s=B10_CAP_S,
                warmup_grace_s=WARMUP_GRACE_S, ref_limit_s=REF_LIMIT_S, check_limit_s=CHECK_LIMIT_S,
                build_s=BUILD_S, min_available_mb=MIN_AVAILABLE_MB, run_budget_h=args.run_budget_h,
                lock=bool(args.lock), provenance=prov, mem_cap_gb=args.mem_cap_gb)
    path = os.path.join(args.out, "records.jsonl")
    stop_path = os.path.join(args.out, "STOP")
    guard = threading.Lock()
    total = len(pairs) * len(adapters)
    count = [0]
    t_start = time.perf_counter()
    budget_s = args.run_budget_h * 3600.0
    stopped = []  # why new measurements stopped being started, once
    skipped = []
    stop_threads = threading.Event()

    def say(msg):
        print(f"[{time.perf_counter() - t_start:7.0f} s] {msg}", file=sys.stderr, flush=True)

    threading.Thread(target=_memlog, args=(os.path.join(args.out, "memlog.tsv"), stop_threads), daemon=True).start()
    threading.Thread(target=_breaker, args=(stop_threads, say), daemon=True).start()
    interrupted_fh = open(os.path.join(args.out, "interrupted.jsonl"), "a", encoding="utf-8", newline="\n")

    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(dict(meta=meta)) + "\n")
        fh.flush()

        def write(f, rec):
            f.write(json.dumps(rec) + "\n")
            f.flush()
            os.fsync(f.fileno())

        def keep(rec):
            with guard:
                write(fh, rec)
                count[0] += 1
                state = "error: " + rec["error"][:60] if "error" in rec else \
                    f"{rec.get('t_s', 0):.3f} s, q2 {rec.get('q2')}"
                print(f"[{count[0]}/{total} {time.perf_counter() - t_start:7.0f} s] {rec['adapter']} "
                      f"{rec['case'][:70]}: {state}", file=sys.stderr, flush=True)
            return rec

        def may_start():
            if stopped:
                return False
            if os.path.exists(stop_path):
                stopped.append("STOP file")
            elif time.perf_counter() - t_start > budget_s:
                stopped.append(f"run budget {args.run_budget_h:g} h")
            if stopped:
                say(f"no new measurement is started: {stopped[0]}")
            return not stopped

        def go(job):
            if not may_start():
                skipped.append(job[:3])
                return None
            return measure(*job, args.mem_cap_gb)

        def phase(jobs):
            """Runs jobs, writing each final record; a job the machine breaker interrupted runs again alone at the
            end, and its first record goes to interrupted.jsonl."""
            done, again = {}, []
            with ThreadPoolExecutor(args.par) as ex:
                for f in as_completed([ex.submit(go, j) for j in jobs]):
                    rec = f.result()
                    if rec is None:
                        continue
                    if str(rec.get("error", "")).startswith("interrupted"):
                        with guard:
                            write(interrupted_fh, rec)
                        again.append(rec)
                        say(f"interrupted, to run again alone: {rec['adapter']} {rec['case'][:60]}")
                        continue
                    done[(rec["adapter"], rec["case"], rec["device"])] = keep(rec)
            for first in again:
                job = next(j for j in jobs if j[:3] == (first["adapter"], first["case"], first["device"]))
                rec = go(job)
                if rec is None:
                    continue
                rec["run_again_after_interruption"] = True
                done[job[:3]] = keep(rec)
            return done

        # the reference first: its time sets every budget
        refs = phase([(REFERENCE, c, d, REF_LIMIT_S) for c, d in pairs])
        jobs = []
        for c, d in pairs:
            r = refs.get((REFERENCE, c, d))
            if r is None:
                continue  # not measured (the run stopped): the run is incomplete
            if "t_s" not in r or "error" in r:
                # no reference time: the test is left out of every score, so the others are not run
                for a in adapters:
                    if a != REFERENCE:
                        keep(dict(adapter=a, case=c, device=d, error=NOT_RUN))
                continue
            b10 = budgets(r["t_s"])[max(TIERS)]
            jobs += [(a, c, d, b10) for a in adapters if a != REFERENCE]
        bound = sum(bound_s(j[3]) for j in jobs) / max(args.par, 1)
        elapsed = time.perf_counter() - t_start
        say(f"references done in {elapsed:.0f} s; bound on the rest: {bound:.0f} s ({len(jobs)} measurements, "
            f"{args.par} at a time); run budget {budget_s:.0f} s")
        if elapsed + bound > budget_s and not stopped:
            stopped.append(f"bound on the run {elapsed + bound:.0f} s over the run budget {budget_s:.0f} s")
            say("not started: " + stopped[0])
            skipped.extend(j[:3] for j in jobs)
        else:
            phase(jobs)
        complete = not stopped and not skipped and count[0] == total
        write(fh, dict(end=dict(end_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                wall_s=round(time.perf_counter() - t_start, 1), complete=complete,
                                stopped=stopped[0] if stopped else None, not_started=len(skipped),
                                bound_after_references_s=round(bound, 1))))
    interrupted_fh.close()
    stop_threads.set()
    summary(args)


def summary(args):
    path = os.path.join(args.out, "records.jsonl")
    lines = [json.loads(ln) for ln in open(path, encoding="utf-8")]
    recs = [r for r in lines if "adapter" in r]
    ref = {(r["case"], r["device"]): r for r in recs if r["adapter"] == REFERENCE}
    adapters = list(dict.fromkeys(r["adapter"] for r in recs))
    out = ["# TOQB summary (v0 draft: not a result)", "",
           "| adapter | " + " | ".join(f"within {t:g}x" for t in TIERS) + " | two-qubit gates / reference "
           "(geometric mean, +1) | invalid | not equivalent | checked | failed |", "|" + "---|" * (6 + len(TIERS))]
    for a in adapters:
        rs = [r for r in recs if r["adapter"] == a and (r["case"], r["device"]) in ref
              and "t_s" in ref[(r["case"], r["device"])]]
        if not rs:
            continue
        w = [within(r, ref[(r["case"], r["device"])]["t_s"]) for r in rs]
        ok = [r for r in rs if "error" not in r and r.get("valid") is True and not not_equivalent(r)]
        ratio = gmean((r["q2"] + 1) / (ref[(r["case"], r["device"])]["q2"] + 1) for r in ok
                      if "q2" in ref[(r["case"], r["device"])])
        out.append(f"| {a} | " + " | ".join(f"{sum(x[t] for x in w) / len(w):.2f}" for t in TIERS)
                   + f" | {ratio:.3f} | {sum(1 for r in rs if r.get('valid') is False)} | "
                   f"{sum(1 for r in rs if not_equivalent(r))} | "
                   f"{sum(1 for r in rs if (r.get('equivalence') or {}).get('checked') is True)} | "
                   f"{sum(1 for r in rs if 'error' in r)} |")
    no_ref = [k for k, r in ref.items() if "t_s" not in r]
    out += ["", f"pairs: {len(ref)}; the reference failed on {len(no_ref)} (left out of every row)"
            + (": " + ", ".join(f"{c} on {d}" for c, d in no_ref[:10]) if no_ref else "")]
    txt = "\n".join(out)
    with open(os.path.join(args.out, "summary.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt + "\n")
    print(txt)


def commit(args):
    from toqb.benchpress_source import seed_commitment
    print(seed_commitment(open(args.seed_file, encoding="utf-8").read()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("one", "run", "summary", "commit"))
    ap.add_argument("--adapter")
    ap.add_argument("--case")
    ap.add_argument("--device")
    ap.add_argument("--b10-s", type=float, default=B10_CAP_S, help="one: the measurement's largest budget")
    ap.add_argument("--profile", help="one (repro runs, never a scored run): cProfile of the warm-up compile, "
                    "written here, also when the compile is stopped")
    ap.add_argument("--plan")
    ap.add_argument("--out")
    ap.add_argument("--par", type=int, default=4)
    ap.add_argument("--seed-file")
    ap.add_argument("--lock", action="store_true")
    ap.add_argument("--mem-cap-gb", type=float, default=None,
                    help="stop a measurement whose resident memory exceeds this (recorded as an error)")
    ap.add_argument("--run-budget-h", type=float, default=10.0,
                    help="no measurement starts after this; the run also stops if its bound exceeds it")
    a = ap.parse_args()
    {"one": one, "run": run, "summary": summary, "commit": commit}[a.mode](a)


if __name__ == "__main__":
    main()
