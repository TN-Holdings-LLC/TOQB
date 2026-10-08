"""The budgeted runner.

One process per (adapter, case, device). In it: build the circuit and the device (not timed), one warm-up compile
(discarded), then REPEATS timed compiles; the fastest and the slowest are dropped and the rest averaged. A compile
that takes longer than LIMIT_FACTOR times the largest budget stops the repeats. The parent kills the process at a
wall-clock limit. Budgets are multiples (TIERS) of the reference compiler's averaged time on the same case and
device, the reference time being taken as at least BUDGET_FLOOR_S.

    python -m toqb.runner one  --adapter qiskit:2:target --case qft:8 --device fake:FakeTorino [--limit-s 60]
    python -m toqb.runner run  --plan plan.json --out DIR [--par 6]
    python -m toqb.runner summary --out DIR

plan.json: {"cases": [...], "devices": [...], "adapters": [...]}; the reference adapter is added if missing.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

REFERENCE = "qiskit:2:target"
TIERS = (1.0, 3.0, 10.0)
BUDGET_FLOOR_S = 0.05
REPEATS = 5
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


def within(record, ref_time_s):
    """{tier: True/False} for a measurement record (False if it failed)."""
    ok = "error" not in record and record.get("valid") is True
    return {t: bool(ok and record["t_s"] <= b) for t, b in budgets(ref_time_s).items()}


def gmean(xs):
    xs = list(xs)
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else float("nan")


# ------------------------------------------------------------------ the child process

def one(args):
    from toqb.adapters import make_adapter
    from toqb.cases import get_case
    from toqb.devices import get_device
    from toqb.metrics import metrics, structural_check
    rec = dict(adapter=args.adapter, case=args.case, device=args.device)
    adapter = make_adapter(args.adapter)
    rec["adapter_version"] = adapter.version()
    circuit, device = get_case(args.case), get_device(args.device)
    stop = args.limit_s / (REPEATS + 1)
    times, out = [], None
    for k in range(REPEATS + 1):
        t0 = time.perf_counter()
        out = adapter.compile(circuit, device)
        dt = time.perf_counter() - t0
        if k > 0:
            times.append(dt)
        if dt > stop:
            break
    rec["times_s"] = [round(t, 6) for t in times] or [round(dt, 6)]
    rec["t_s"] = trimmed_mean(rec["times_s"])
    problem = structural_check(out, device)
    rec["valid"] = problem is None
    if problem:
        rec["invalid_because"] = problem
    rec.update(metrics(out, device))
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


def run(args):
    plan = json.load(open(args.plan, encoding="utf-8"))
    adapters = list(dict.fromkeys([REFERENCE] + plan["adapters"]))
    pairs = [(c, d) for c in plan["cases"] for d in plan["devices"]]
    os.makedirs(args.out, exist_ok=True)
    meta = dict(start_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), python=sys.version.split()[0],
                platform=platform.platform(), cpus=os.cpu_count(), par=args.par, plan=plan, reference=REFERENCE,
                tiers=TIERS, floor_s=BUDGET_FLOOR_S, repeats=REPEATS, limit_factor=LIMIT_FACTOR)
    path = os.path.join(args.out, "records.jsonl")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(dict(meta=meta)) + "\n")
    # the reference first: its time sets every budget, and the limit of the others
    with ThreadPoolExecutor(args.par) as ex:
        refs = dict(zip(pairs, ex.map(lambda p: measure(REFERENCE, p[0], p[1], args.ref_limit_s), pairs)))
    jobs = []
    for (c, d), r in refs.items():
        ref_t = r.get("t_s")
        limit = (LIMIT_FACTOR * max(budgets(ref_t).values()) * (REPEATS + 1)) if ref_t else args.ref_limit_s
        jobs += [(a, c, d, limit) for a in adapters if a != REFERENCE]
    with ThreadPoolExecutor(args.par) as ex:
        others = list(ex.map(lambda j: measure(*j), jobs))
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        for rec in list(refs.values()) + others:
            fh.write(json.dumps(rec) + "\n")
    summary(args)


def summary(args):
    path = os.path.join(args.out, "records.jsonl")
    lines = [json.loads(ln) for ln in open(path, encoding="utf-8")]
    recs = [r for r in lines if "meta" not in r]
    ref = {(r["case"], r["device"]): r for r in recs if r["adapter"] == REFERENCE}
    adapters = list(dict.fromkeys(r["adapter"] for r in recs))
    out = ["# TOQB summary (v0 draft: not a result)", "",
           "| adapter | " + " | ".join(f"within {t:g}x" for t in TIERS) + " | two-qubit gates / reference "
           "(geometric mean, +1) | invalid | failed |", "|" + "---|" * (4 + len(TIERS))]
    for a in adapters:
        rs = [r for r in recs if r["adapter"] == a and (r["case"], r["device"]) in ref
              and "t_s" in ref[(r["case"], r["device"])]]
        if not rs:
            continue
        w = [within(r, ref[(r["case"], r["device"])]["t_s"]) for r in rs]
        ok = [r for r in rs if "error" not in r and r.get("valid") is True]
        ratio = gmean((r["q2"] + 1) / (ref[(r["case"], r["device"])]["q2"] + 1) for r in ok
                      if "q2" in ref[(r["case"], r["device"])])
        out.append(f"| {a} | " + " | ".join(f"{sum(x[t] for x in w) / len(w):.2f}" for t in TIERS)
                   + f" | {ratio:.3f} | {sum(1 for r in rs if r.get('valid') is False)} | "
                   f"{sum(1 for r in rs if 'error' in r)} |")
    txt = "\n".join(out)
    with open(os.path.join(args.out, "summary.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt + "\n")
    print(txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("one", "run", "summary"))
    ap.add_argument("--adapter")
    ap.add_argument("--case")
    ap.add_argument("--device")
    ap.add_argument("--limit-s", type=float, default=600.0)
    ap.add_argument("--ref-limit-s", type=float, default=1800.0)
    ap.add_argument("--plan")
    ap.add_argument("--out")
    ap.add_argument("--par", type=int, default=4)
    a = ap.parse_args()
    {"one": one, "run": run, "summary": summary}[a.mode](a)


if __name__ == "__main__":
    main()
