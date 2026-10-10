"""v14: a run's results twice, side by side -- as scored ("display") and as a user who runs the output on the device
sees them ("essential").

Essential differs from display in two rules only:
  1. On a device with a Target, an output with an operation on a failed element (`on_failed_ops`; run 1 and 2's
     records have only `on_failed`, the two-qubit gates) is unusable: its result is noise and nothing says so. It
     counts as a failure, as an invalid output does.
  2. Time is the first compile in the process (`t_first_s`), which a user always pays, not the mean of the repeated
     compiles after it. Records without `t_first_s` (runs 1 and 2) keep the display time, and the table says so.
The reference's own time stays the denominator of the tiers; a pair whose reference output is unusable is left out of
the two-qubit ratio (as an unusable reference is in display), but its tiers still count.

    python -m toqb.essential --out DIR        (writes essential.md and essential.json into DIR)
"""
from __future__ import annotations

import argparse
import json
import math
import os

from toqb.runner import REFERENCE, TIERS, within
from toqb.score import family, load, usable


def failed_ops(r):
    return r.get("on_failed_ops", r.get("on_failed", 0)) or 0


def essential(r):
    """The record as the essential view reads it."""
    e = dict(r)
    if "error" not in r and family(r["case"]).endswith("FakeTorino") and failed_ops(r) > 0:
        e["error"] = f"unusable: {failed_ops(r)} operations on failed elements"
    if "t_first_s" in r:
        e["t_s"] = r["t_first_s"]
    return e


def table(recs, adapters, pairs):
    ref = {(r["case"], r["device"]): r for r in recs if r["adapter"] == REFERENCE}
    by = {(r["adapter"], r["case"], r["device"]): r for r in recs}
    rows = {}
    for a in adapters:
        rs = [by[(a, c, d)] for c, d in pairs if (a, c, d) in by and "t_s" in ref.get((c, d), {})]
        w = [within(r, ref[(r["case"], r["device"])]["t_s"]) for r in rs]
        logs = [math.log((r["q2"] + 1) / (ref[(r["case"], r["device"])]["q2"] + 1)) for r in rs
                if usable(r) and usable(ref[(r["case"], r["device"])])]
        torino = [r for r in rs if family(r["case"]).endswith("FakeTorino")]
        rows[a] = dict(n=len(rs), **{f"within_{t:g}x": sum(x[t] for x in w) / len(w) if w else float("nan")
                                     for t in TIERS},
                       q_all=math.exp(sum(logs) / len(logs)) if logs else float("nan"), q_n=len(logs),
                       unusable=sum(1 for r in torino if str(r.get("error", "")).startswith("unusable")),
                       usable_torino=sum(1 for r in torino if usable(r)), torino=len(torino),
                       failed=sum(1 for r in rs if "error" in r))
    return rows


def run(out):
    meta, recs, _ = load(out)
    plan = meta["plan"]
    adapters = list(dict.fromkeys([REFERENCE] + plan["adapters"]))
    pairs = [(f"bp:{t}", f"bp:{t}") for t in plan["drawn"]]
    disp = table(recs, adapters, pairs)
    ess = table([essential(r) for r in recs], adapters, pairs)
    first = all("t_first_s" in r for r in recs if "error" not in r)
    L = ["# Display and essential results", "",
         "Display: as scored. Essential: an output with an operation on a failed element (FakeTorino) is unusable, "
         "and time is the first compile in the process."
         + ("" if first else " **These records have no first-compile time: essential time = display time.**"), "",
         "| compiler | within 1x (display / essential) | within 3x | within 10x | two-qubit / reference (display / "
         "essential) | FakeTorino outputs usable on the device | failed (display / essential) |",
         "|---|---|---|---|---|---|---|"]
    for a in adapters:
        d, e = disp[a], ess[a]
        L.append(f"| {a} | " + " | ".join(f"{d[f'within_{t:g}x']:.3f} / {e[f'within_{t:g}x']:.3f}" for t in TIERS)
                 + f" | {d['q_all']:.3f} / {e['q_all']:.3f} | {e['usable_torino']} of {e['torino']} "
                 f"({e['unusable']} unusable) | {d['failed']} / {e['failed']} |")
    txt = "\n".join(L) + "\n"
    open(os.path.join(out, "essential.md"), "w", encoding="utf-8", newline="\n").write(txt)
    with open(os.path.join(out, "essential.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(dict(display=disp, essential=ess, first_compile_time=first), fh, indent=1)
    print(txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    run(ap.parse_args().out)


if __name__ == "__main__":
    main()
