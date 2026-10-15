"""The report of a variational-loop run (`toqb.task_loop`): for the same money, which compiler returns the best model?

From the arm records in OUTDIR:
  1. the result for the money. The budget of each mode is the plan's `budget_usd`, or else what the reference arm
     (Qiskit's loop practice) spent on the whole training in that mode, plus `budget_tolerance` (default 5%, so that
     cents of classical time do not move an arm to an earlier evaluation). Each arm is read at its last evaluation
     within that budget: noisy test accuracy and margin. Also the dollars to `target_accuracy` and the noiseless accuracy of
     the final angles. Batch mode bills QPU time only; session mode also bills the classical time between jobs.
  2. a reference, not a contest: the classical models (`toqb.classical`) trained on the same points, and the energy
     of every row in kWh -- a range from the plan's assumed powers (`energy`), not a measurement;
  3. the trajectory: accuracy and margin at each evaluation, with the dollars spent so far in each mode.
  4. secondary: the cost of compiling (template builds and binds, or every compile) against the reference arm's, in
     tiers 1x / 3x / 10x with the floor `budget_floor_s`.
An arm is invalid when it failed, returned an output that is not executable on the device or uses a failed element,
or failed an equivalence check; an invalid arm is listed but its result is not compared.

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


def at_budget(rec, mode, budget):
    """The last evaluation whose spending in `mode` is within `budget` dollars (None if none is)."""
    ok = [e for e in rec.get("evals") or [] if e[f"{mode}_usd"] <= budget + 1e-9]
    return ok[-1] if ok else None


def budgets(recs, plan):
    if plan.get("budget_usd") is not None:
        b = float(plan["budget_usd"])
        return {"batch": b, "session": b}, "the plan's budget_usd"
    ref = next((r for r in recs if r["arm"] == plan.get("reference") and r.get("spent")), None)
    if ref is None:
        return None, "no reference record"
    tol = float(plan.get("budget_tolerance", 0.05))
    return ({m: ref["spent"][f"{m}_usd"] * (1 + tol) for m in ("batch", "session")},
            f"what the reference arm {ref['arm']} spent on the whole training, plus {tol:.0%}")


def _kwh(seconds_qpu, seconds_cpu, energy):
    """(low, high) kWh: the QPU-held seconds at the system's power, plus the classical seconds at the CPU's power."""
    (k0, k1), (w0, w1) = energy["qpu_system_kw"], energy["cpu_w"]
    return ((seconds_qpu * k0 * 1000 + seconds_cpu * w0) / 3.6e6, (seconds_qpu * k1 * 1000 + seconds_cpu * w1) / 3.6e6)


def _fmt_kwh(r):
    lo, hi = r
    f = (lambda v: f"{v:.2g}") if hi < 0.01 else (lambda v: f"{v:.2f}")
    return f"{f(lo)}-{f(hi)}"


def classical_section(outdir, recs, plan, bud):
    """Section 2: the classical reference and the energy of every row."""
    from toqb.task_loop import DEFAULT_ENERGY
    energy = dict(DEFAULT_ENERGY, **plan.get("energy", {}))
    path = os.path.join(outdir, "classical.json")
    cl = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None
    lines = ["## 2. Reference: classical models, and energy", "",
             "Not a contest: TOQB compares compilers. The classical models (`toqb.classical`, numpy only, one fixed "
             "configuration each) are trained on the same training points and scored on the same test points, as the "
             "bar a quantum model is read against. Energy is a range from assumed powers, not a measurement: a "
             f"quantum run is charged {energy['qpu_system_kw'][0]:g}-{energy['qpu_system_kw'][1]:g} kW for the "
             f"seconds it holds the QPU ({energy['attribution']}), and every classical second "
             f"{energy['cpu_w'][0]:g}-{energy['cpu_w'][1]:g} W ({energy['source']}).", "",
             "| row | test accuracy | time | energy, kWh | money |", "|---|---|---|---|---|"]
    q_low, c_high = [], []
    if cl:
        for m in cl["models"]:
            lines.append(f"| classical: {m['model']} | {m['accuracy']:.3f} | {m['seconds']:.2f} s CPU | "
                         f"{_fmt_kwh(_kwh(0.0, m['seconds'], energy))} | - |")
            c_high.append(_kwh(0.0, m["seconds"], energy)[1])
    for r in recs:
        if not r.get("evals") or not r.get("valid"):
            continue
        sp = r.get("spent", {})
        for m in ("batch", "session"):
            e = at_budget(r, m, bud[m]) if bud else None
            if e is None:
                continue
            qpu_s = e["batch_qpu_s"] if m == "batch" else e["session_s"]
            cpu_s = r.get("setup_s", 0.0) + sum(c["classical_s"] for c in r.get("curve", [])
                                                if c["iteration"] <= e["iteration"])
            q_low.append(_kwh(qpu_s, cpu_s, energy)[0])
            lines.append(f"| quantum, {m}: {r['arm']} | {e['accuracy']:.3f} (iteration {e['iteration']}) | "
                         f"{qpu_s:.1f} s holding the QPU | {_fmt_kwh(_kwh(qpu_s, cpu_s, energy))} | ${e[f'{m}_usd']:.2f} |")
    if not cl:
        lines += ["", "(No classical.json in this run.)"]
    elif q_low and c_high and max(c_high) > 0:
        best = max(cl["models"], key=lambda m: m["accuracy"])
        lines += ["", f"The least energy any quantum row is estimated at is {min(q_low) / max(c_high):,.0f} times the "
                      f"most any classical model is; the best classical accuracy is {best['accuracy']:.3f} "
                      f"({best['model']})."]
    return lines


def report(outdir, plan=None):
    recs = load(outdir)
    if plan is None:
        path = os.path.join(outdir, "plan.json")
        plan = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    target = plan.get("evaluation", {}).get("target_accuracy")
    bud, bud_why = budgets(recs, plan)
    cost = next((r.get("qpu_cost") for r in recs if r.get("qpu_cost")), {})
    lines = [f"# {plan.get('name', 'loop run')}: for the same money, which compiler returns the best model?", "",
             f"Device {plan.get('device')}; front end {plan.get('frontend', 'qiskit')}; task "
             f"{json.dumps(plan.get('task'))}; optimizer {json.dumps(plan.get('optimizer'))}; evaluation "
             f"{json.dumps(plan.get('evaluation'))}.", "",
             f"Price: {cost.get('per_shot_s')} s per shot + {cost.get('per_circuit_s')} s per circuit + the circuit's "
             f"duration per shot, at ${cost.get('usd_per_s', 0):.2f} per QPU second ({cost.get('source', '-')}).", ""]
    if bud:
        lines += [f"Budget: batch ${bud['batch']:.2f}, session ${bud['session']:.2f} ({bud_why}).", ""]
    lines += ["## 1. The result for the money", "",
              "Accuracy / margin on the test set at the last evaluation within the budget (iteration in brackets); "
              f"dollars to reach accuracy {target}; noiseless accuracy of the final angles.", "",
              "| arm | valid | batch: within budget | session: within budget | $ to target (batch / session) | "
              "spent on the whole training (batch / session) | final noiseless accuracy |",
              "|---|---|---|---|---|---|---|"]
    for r in recs:
        if not r.get("evals"):
            lines.append(f"| {r['arm']} | no | - | - | - | - | - |")
            continue
        cells = []
        for m in ("batch", "session"):
            e = at_budget(r, m, bud[m]) if bud else None
            cells.append("-" if e is None else f"{e['accuracy']:.3f} / {e['margin']:.3f} ({e['iteration']})")
        tt = r.get("to_target") or {}
        tts = " / ".join("not reached" if not tt.get(m) else f"${tt[m]['usd']:.2f}" for m in ("batch", "session"))
        sp = r.get("spent", {})
        lines.append(f"| {r['arm']} | {'yes' if r.get('valid') else 'NO'} | {cells[0]} | {cells[1]} | {tts} | "
                     f"${sp.get('batch_usd', 0):.2f} / ${sp.get('session_usd', 0):.2f} | "
                     f"{r['evals'][-1]['noiseless_accuracy']:.3f} |")
    lines += [""] + classical_section(outdir, recs, plan, bud)
    lines += ["", "## 3. The trajectory", "",
              "iteration: accuracy / margin (dollars spent so far, batch / session)", "",
              "| arm | evaluations |", "|---|---|"]
    for r in recs:
        cells = "; ".join(f"{e['iteration']}: {e['accuracy']:.3f} / {e['margin']:.3f} (${e['batch_usd']:.1f} / "
                          f"${e['session_usd']:.1f})" for e in r.get("evals") or [])
        lines.append(f"| {r['arm']} | {cells} |")
    ref = next((r for r in recs if r["arm"] == plan.get("reference") and "compile_s" in r), None)
    floor = plan.get("budget_floor_s", 1.0)
    lines += ["", "## 4. Secondary: the cost of compiling", "",
              f"Reference {plan.get('reference')}" + (f": {ref['compile_s']:.2f} s per loop." if ref else ": no record."),
              "", "| arm | version | circuits | compile s | per circuit ms | tier | classical s per loop | "
              "templates built / not available | 2q gates | duration us |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in recs:
        if "compile_s" not in r:
            lines.append(f"| {r['arm']} | {r.get('version', '-')} | - | - | - | - | - | - | - | - |")
            continue
        t = tier(r["compile_s"], ref["compile_s"], floor) if ref else "-"
        st = r.get("arm_stats", {})
        lines.append(f"| {r['arm']} | {r.get('version', '-')} | {r['circuits']} | {r['compile_s']:.2f} | "
                     f"{r['per_circuit_compile_ms']:.2f} | {t} | {r.get('spent', {}).get('classical_s', 0):.2f} | "
                     f"{st.get('template_builds', 0)} / {st.get('template_unavailable', 0)} | {r['q2_mean']:.1f} | "
                     f"{r['duration_us_mean']:.2f} |")
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
