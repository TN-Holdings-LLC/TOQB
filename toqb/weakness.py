"""The weakness report: where each compiler fails, is slow or gives worse circuits than the reference, grouped by
where it was when it was stopped and by the input's features, with a command that reproduces each group's first case
under a profiler. It reads records.jsonl of one or more runs and scores nothing: it is for finding what to fix.

    python -m toqb.weakness DIR [DIR ...] [--adapter psf:recommended] [--out FILE]

Groups:
  - failures, by compiler, kind (time, memory, adapter, harness, other) and "where": the innermost frame of the
    compiler's own code in the stack dumped just before the stop (toqb.runner.stack_from);
  - slow: returned, but over 3x the reference's time;
  - worse: usable, and more than 10% more two-qubit gates than the reference;
each split by the input's size (two-qubit instructions), qubits and family.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict

REFERENCE = "qiskit:2:target"
OWN = {"psf": ("psf_",), "tket": ("pytket/",), "qiskit": ("qiskit/",)}  # how a frame of the compiler's code starts
SLOW = 3.0
WORSE = 1.10


def family(case):
    tid = case.split(":", 1)[-1]
    for prefix, name in (("test_QASMBench", "QASMBench"), ("test_hamiltonians", "HamLib"),
                         ("test_hamlib_hamiltonians_transpile", "HamLib, FakeTorino"),
                         ("test_feynman_transpile", "Feynman, FakeTorino")):
        if tid.startswith(prefix):
            return name
    return "other"


def size_bucket(f):
    if not f:
        return "size ?"
    n = f.get("two_qubit", 0) + f.get("wider", 0)
    for lim, name in ((100, "<100"), (1_000, "100-1k"), (10_000, "1k-10k"), (100_000, "10k-100k")):
        if n < lim:
            return f"2q {name}"
    return "2q >=100k"


def qubit_bucket(f):
    if not f:
        return "qubits ?"
    q = f.get("qubits", 0)
    return "qubits <=16" if q <= 16 else "qubits 17-100" if q <= 100 else "qubits >100"


def kind(err):
    err = str(err)
    for prefix, name in (("time", "time"), ("memory limit", "memory"), ("interrupted", "harness"),
                         ("not run", "not run")):
        if err.startswith(prefix):
            return name
    if any(e in err for e in ("unsupported by qiskit_to_tk", "TKET returned", "Invoked with types")):
        return "adapter"
    return "other"


def where(rec):
    """The innermost frame of the compiler's own code at the stop, or the innermost frame, or '-'."""
    stack = rec.get("stack_at_stop") or []
    own = OWN.get(rec["adapter"].split(":", 1)[0], ())
    for frame in stack:
        if frame.startswith(own):
            return frame
    return stack[0] if stack else "-"


def load(dirs):
    recs = []
    for d in dirs:
        for ln in open(os.path.join(d, "records.jsonl"), encoding="utf-8"):
            try:
                x = json.loads(ln)
            except ValueError:
                continue  # a line cut short
            if "adapter" in x:
                x["_run"] = os.path.basename(os.path.normpath(d))
                recs.append(x)
    return recs


def repro(rec):
    b10 = rec.get("b10_s")
    return (f"python -m toqb.runner one --adapter {rec['adapter']} --case '{rec['case']}' --device "
            f"'{rec['device']}'" + (f" --b10-s {b10:g}" if b10 else "") + " --profile repro.prof")


def report(recs, only=None):
    ref = {(r["_run"], r["case"], r["device"]): r for r in recs if r["adapter"] == REFERENCE}
    groups = {"failures": defaultdict(list), "slow": defaultdict(list), "worse": defaultdict(list)}
    for r in recs:
        a = r["adapter"]
        if a == REFERENCE or (only and a != only):
            continue
        q = ref.get((r["_run"], r["case"], r["device"]))
        f = r.get("features") or (q or {}).get("features")
        split = (size_bucket(f), qubit_bucket(f), family(r["case"]))
        if "error" in r:
            k = kind(r["error"])
            if k != "not run":
                groups["failures"][(a, k, where(r)) + split].append(r)
            continue
        if q is None or "t_s" not in q or "error" in q:
            continue
        if r["t_s"] > SLOW * max(0.05, q["t_s"]):
            groups["slow"][(a,) + split].append(r)
        eq = r.get("equivalence") or {}
        usable = r.get("valid") is True and not (eq.get("checked") is True and eq.get("equivalent") is False)
        if usable and "q2" in r and "q2" in q and (r["q2"] + 1) > WORSE * (q["q2"] + 1):
            groups["worse"][(a,) + split].append(r)
    L = ["# TOQB weakness report", "",
         f"{len(recs)} records from {len({r['_run'] for r in recs})} run(s). Nothing here is a score.", ""]
    L += ["## Failures (stopped or failed), by where they were stopped", "",
          "| compiler | kind | where (innermost own frame) | input size | qubits | family | n | first case |",
          "|---|---|---|---|---|---|---|---|"]
    for key, rs in sorted(groups["failures"].items(), key=lambda x: (-len(x[1]), x[0])):
        L.append("| " + " | ".join(key) + f" | {len(rs)} | {rs[0]['case'][3:60]} |")
    L += ["", f"## Slow: returned, but over {SLOW:g}x the reference's time", "",
          "| compiler | input size | qubits | family | n | median time / reference | first case |",
          "|---|---|---|---|---|---|---|"]
    for key, rs in sorted(groups["slow"].items(), key=lambda x: (-len(x[1]), x[0])):
        ratios = sorted(r["t_s"] / max(0.05, ref[(r["_run"], r["case"], r["device"])]["t_s"]) for r in rs)
        L.append("| " + " | ".join(key) + f" | {len(rs)} | {ratios[len(ratios) // 2]:.1f} | {rs[0]['case'][3:60]} |")
    L += ["", f"## Worse: more than {100 * (WORSE - 1):.0f}% more two-qubit gates than the reference", "",
          "| compiler | input size | qubits | family | n | median (q2 + 1) / (reference + 1) | first case |",
          "|---|---|---|---|---|---|---|"]
    for key, rs in sorted(groups["worse"].items(), key=lambda x: (-len(x[1]), x[0])):
        ratios = sorted((r["q2"] + 1) / (ref[(r["_run"], r["case"], r["device"])]["q2"] + 1) for r in rs)
        L.append("| " + " | ".join(key) + f" | {len(rs)} | {ratios[len(ratios) // 2]:.2f} | {rs[0]['case'][3:60]} |")
    L += ["", "## Reproducing a group's first case", "",
          "Each command runs one measurement with the same limits and writes a cProfile of its warm-up compile, also "
          "when the compile is stopped (`python -m pstats repro.prof`). Run from the TOQB clone, with the run's "
          "environment ($TOQB_BENCHPRESS, $PSF_ZERO_REPO).", ""]
    seen = 0
    for name in ("failures", "slow", "worse"):
        for key, rs in sorted(groups[name].items(), key=lambda x: (-len(x[1]), x[0]))[:5]:
            L += [f"- {name}, {' / '.join(key)}:", "", f"  ```bash\n  {repro(rs[0])}\n  ```", ""]
            seen += 1
    if not seen:
        L.append("Nothing to reproduce.")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--adapter", help="only this compiler")
    ap.add_argument("--out", help="also write the report here")
    a = ap.parse_args()
    txt = report(load(a.dirs), a.adapter)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(txt)
    print(txt)


if __name__ == "__main__":
    main()
