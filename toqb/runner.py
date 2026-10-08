"""The budgeted runner.

One process per (adapter, case, device). In it: build the circuit and the device (not timed), one warm-up compile
(discarded), then REPEATS timed compiles (one, if the warm-up took longer than LONG_S); the fastest and the slowest
are dropped and the rest averaged. A compile
that takes longer than LIMIT_FACTOR times the largest budget stops the repeats. The parent kills the process at a
wall-clock limit. Budgets are multiples (TIERS) of the reference compiler's averaged time on the same case and
device, the reference time being taken as at least BUDGET_FLOOR_S.

    python -m toqb.runner one  --adapter qiskit:2:target --case qft:8 --device fake:FakeTorino [--limit-s 60]
    python -m toqb.runner run  --plan plan.json --out DIR [--par 6] [--lock]
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
TOQB, PSF-Zero or Benchpress has an uncommitted change to a tracked file.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
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
LIMIT_FACTOR = 10.0
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
    that the tiers stay apart on circuits the reference compiles in a few milliseconds."""
    return {t: t * max(BUDGET_FLOOR_S, ref_time_s) for t in TIERS}


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

def one(args):
    from toqb.adapters import make_adapter
    from toqb.cases import get_case
    from toqb.devices import get_device
    from toqb.metrics import equivalence, metrics, structural_check
    rec = dict(adapter=args.adapter, case=args.case, device=args.device)
    adapter = make_adapter(args.adapter)
    rec["adapter_version"] = adapter.version()
    circuit, device = get_case(args.case), get_device(args.device)
    stop = args.limit_s / (REPEATS + 1)
    times, out, runs = [], None, REPEATS + 1
    k = 0
    while k < runs:
        t0 = time.perf_counter()
        out = adapter.compile(circuit, device)
        dt = time.perf_counter() - t0
        if k == 0 and dt > LONG_S:
            runs = 2  # a long compile varies little between runs; one timed run after the warm-up
        if k > 0:
            times.append(dt)
        if dt > stop:
            break
        k += 1
    rec["times_s"] = [round(t, 6) for t in times] or [round(dt, 6)]
    rec["t_s"] = trimmed_mean(rec["times_s"])
    problem = structural_check(out, device)
    rec["valid"] = problem is None
    if problem:
        rec["invalid_because"] = problem
    rec.update(metrics(out, device))
    try:
        # the compiler's own reading of the input, when it differs from Qiskit's (TKET and a PauliEvolutionGate)
        reading = adapter.reference_input(circuit) if hasattr(adapter, "reference_input") else None
        rec["equivalence"] = equivalence(circuit, out, reference=reading)
    except Exception as exc:  # noqa: BLE001 - recorded: the check could not be made
        rec["equivalence"] = dict(checked=False, why=f"{type(exc).__name__}: {exc}"[:200])
    print(json.dumps(rec), flush=True)


# ------------------------------------------------------------------ the parent

def measure(adapter, case, device, limit_s):
    cmd = [sys.executable, "-m", "toqb.runner", "one", "--adapter", adapter, "--case", case, "--device", device,
           "--limit-s", str(limit_s)]
    env = dict(os.environ, **ONE_THREAD)
    w0 = time.perf_counter()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=limit_s + 120, env=env,
                           encoding="utf-8", errors="replace")
        lines = [ln for ln in p.stdout.splitlines() if ln.startswith("{")]
        rec = json.loads(lines[-1]) if lines else dict(adapter=adapter, case=case, device=device,
                                                       error=(p.stderr or "")[-600:])
    except subprocess.TimeoutExpired:
        rec = dict(adapter=adapter, case=case, device=device, error=f"timeout {limit_s + 120:.0f} s")
    rec["wall_s"] = round(time.perf_counter() - w0, 3)
    return rec


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
    for pkg in ("qiskit", "qiskit-ibm-runtime", "numpy", "scipy", "rustworkx", "pytket", "pytket-qiskit"):
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
                tiers=TIERS, floor_s=BUDGET_FLOOR_S, repeats=REPEATS, long_s=LONG_S, limit_factor=LIMIT_FACTOR,
                lock=bool(args.lock), provenance=prov)
    path = os.path.join(args.out, "records.jsonl")
    guard = threading.Lock()
    total = len(pairs) * len(adapters)
    count = [0]
    t_start = time.perf_counter()
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(dict(meta=meta)) + "\n")
        fh.flush()

        def keep(rec):
            with guard:
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                count[0] += 1
                state = "error" if "error" in rec else f"{rec.get('t_s', 0):.3f} s, q2 {rec.get('q2')}"
                print(f"[{count[0]}/{total} {time.perf_counter() - t_start:7.0f} s] {rec['adapter']} "
                      f"{rec['case'][:70]}: {state}", file=sys.stderr, flush=True)
            return rec

        # the reference first: its time sets every budget, and the limit of the others
        with ThreadPoolExecutor(args.par) as ex:
            futs = {ex.submit(measure, REFERENCE, c, d, args.ref_limit_s): (c, d) for c, d in pairs}
            refs = {futs[f]: keep(f.result()) for f in as_completed(futs)}
        jobs = []
        for c, d in pairs:
            ref_t = refs[(c, d)].get("t_s")
            limit = (LIMIT_FACTOR * max(budgets(ref_t).values()) * (REPEATS + 1)) if ref_t else args.ref_limit_s
            jobs += [(a, c, d, limit) for a in adapters if a != REFERENCE]
        with ThreadPoolExecutor(args.par) as ex:
            for f in as_completed([ex.submit(measure, *j) for j in jobs]):
                keep(f.result())
        fh.write(json.dumps(dict(end=dict(end_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                          wall_s=round(time.perf_counter() - t_start, 1)))) + "\n")
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
    ap.add_argument("--limit-s", type=float, default=600.0)
    ap.add_argument("--ref-limit-s", type=float, default=1800.0)
    ap.add_argument("--plan")
    ap.add_argument("--out")
    ap.add_argument("--par", type=int, default=4)
    ap.add_argument("--seed-file")
    ap.add_argument("--lock", action="store_true")
    a = ap.parse_args()
    {"one": one, "run": run, "summary": summary, "commit": commit}[a.mode](a)


if __name__ == "__main__":
    main()
