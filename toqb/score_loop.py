"""The report of a variational-loop run (`toqb.task_loop`): one row per arm, from the arm records in OUTDIR.

Two views, as TOQB reports everything:
  - the loop's cost: compile time per loop (template build + binds, or every compile) against the reference arm's,
    in the budget tiers 1x / 3x / 10x (floor `budget_floor_s`), and the simulation's time, which no compiler pays
    for alone;
  - the loop's result: noisy test accuracy and margin at each evaluation, the noiseless accuracy of the final angles,
    and the time to the target accuracy.
An arm is invalid when it failed, returned an output that is not executable on the device or uses a failed element,
or failed an equivalence check; an invalid arm's result is listed but not compared.

    python -m toqb.score_loop OUTDIR [PLAN.json]
"""
from __future__ import annotations

import glob
import json
import os
import sys


def load(outdir):
    return [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(outdir, "arm-*.json")))]


def tier(compile_s, ref_s, floor_s):
    base = max(ref_s, floor_s)
    for k in (1, 3, 10):
        if compile_s <= k * base:
            return f"{k}x"
    return "over 10x"


def report(outdir, plan=None):
    recs = load(outdir)
    if plan is None:
        plan = json.load(open(os.path.join(outdir, "plan.json"), encoding="utf-8")) if os.path.exists(
            os.path.join(outdir, "plan.json")) else {}
    ref_name = plan.get("reference")
    floor = plan.get("budget_floor_s", 1.0)
    target = plan.get("evaluation", {}).get("target_accuracy")
    ref = next((r for r in recs if r["arm"] == ref_name and "compile_s" in r), None)
    lines = [f"# {plan.get('name', 'loop run')}: report", "",
             f"Device {plan.get('device')}; task {json.dumps(plan.get('task'))}; optimizer "
             f"{json.dumps(plan.get('optimizer'))}; evaluation {json.dumps(plan.get('evaluation'))}.", "",
             f"Reference arm: {ref_name} (compile time per loop "
             f"{ref['compile_s']:.2f} s)." if ref else f"Reference arm: {ref_name} (no record).", "",
             "## The loop's cost", "",
             "| arm | version | valid | circuits | setup s | compile s | per circuit ms | budget tier | simulation s | "
             "2q gates | duration us |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in recs:
        if "compile_s" not in r:
            lines.append(f"| {r['arm']} | {r.get('version', '-')} | no | - | - | - | - | - | - | - | - |")
            continue
        t = tier(r["compile_s"], ref["compile_s"], floor) if ref else "-"
        lines.append(f"| {r['arm']} | {r.get('version', '-')} | {'yes' if r['valid'] else 'NO'} | {r['circuits']} | "
                     f"{r['setup_s']:.2f} | {r['compile_s']:.2f} | {r['per_circuit_compile_ms']:.2f} | {t} | "
                     f"{r['sim_s']:.1f} | {r['q2_mean']:.1f} | {r['duration_us_mean']:.2f} |")
    lines += ["", "## The loop's result", "",
              f"Noisy test accuracy / margin at each evaluation (iteration: accuracy / margin); the noiseless accuracy "
              f"of the final angles; the first evaluation at or above {target}.", "",
              "| arm | evaluations | final noiseless accuracy | to target: iteration, compile s, wall s |", "|---|---|---|---|"]
    for r in recs:
        ev = r.get("evals") or []
        cells = ", ".join(f"{e['iteration']}: {e['accuracy']:.3f} / {e['margin']:.3f}" for e in ev)
        fin = f"{ev[-1]['noiseless_accuracy']:.3f}" if ev else "-"
        tt = r.get("to_target")
        tts = "not reached" if not tt else f"{tt['iteration']}, {tt['compile_s']:.2f}, {tt['wall_s']:.1f}"
        lines.append(f"| {r['arm']} | {cells} | {fin} | {tts} |")
    lines += ["", "## Checks", ""]
    for r in recs:
        eq = r.get("equivalence") or []
        ok = sum(1 for e in eq if e.get("equivalent"))
        lines.append(f"- {r['arm']}: structural failures {r.get('structural_fail')}, operations on failed elements "
                     f"{r.get('on_failed_ops')}, equivalence {ok} of {len(eq)} checked"
                     + (f"; error: {r['error']}" if r.get("error") else ""))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    out = sys.argv[1]
    plan = json.load(open(sys.argv[2], encoding="utf-8")) if len(sys.argv) > 2 else None
    print(report(out, plan))
