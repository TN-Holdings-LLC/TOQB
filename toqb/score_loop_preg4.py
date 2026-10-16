"""Scores the loop budget run (n = 6, L = 8, run 1's SPSA, a hard 2-minute QPU budget, fast engine) against its
pre-registration, prereg/2026-10-16-loop-n6-budget.md.

    python -m toqb.score_loop_preg4 <run folder> [--seeds FIRST-LAST]

Each arm trains until the next job would pass the budget (`evaluation.stop_budget_usd`) and is evaluated there
(`rec["stop"]`). The comparison is at that point. The paired test is preg2's one-sided sign-flip test (exact up to
20 seeds, else 200,000 random patterns with a fixed seed). Writes score.md and score.json; never overwrites a score.
"""
import json
import math
import os
import sys

from toqb.score_loop_preg2 import sign_flip_p

PSF = "psfai:template"
QK = "qiskit:2:target:template"
FIRST, LAST = 6001, 7000
ALPHA = 0.01
WORST = {"noiseless_accuracy": -1.0, "accuracy": -1.0, "margin": -2.0}


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def collect(root, seeds):
    rows = []
    for s in seeds:
        d = os.path.join(root, f"seed{s}")
        plan = _load(os.path.join(d, "plan.json")) or {}
        budget = plan.get("evaluation", {}).get("stop_budget_usd")
        row = dict(seed=s, budget=budget)
        for tag, arm in (("psf", PSF), ("qk", QK)):
            rec = _load(os.path.join(d, f"arm-{arm.replace(':', '_')}.json"))
            stop = (rec or {}).get("stop") or {}
            done = stop.get("iterations_done")
            last = (rec or {}).get("evals", [{}])[-1] if rec and rec.get("evals") else {}
            spent = (rec or {}).get("spent", {}).get("batch_usd")
            ok = bool(rec and rec.get("valid") and done and last.get("iteration") == done and budget is not None
                      and spent is not None and spent <= budget + 1e-9)
            row[f"{tag}_ok"] = ok
            row[f"{tag}_error"] = (rec or {}).get("error", None if rec else "no record")
            row[f"{tag}_iterations"] = done
            row[f"{tag}_batch_usd"] = spent
            for key in ("accuracy", "margin", "noiseless_accuracy"):
                row[f"{tag}_{key}"] = last.get(key) if ok else None
            row[f"{tag}_q2"] = (rec or {}).get("q2_mean")
            row[f"{tag}_duration_us"] = (rec or {}).get("duration_us_mean")
            row[f"{tag}_wall_s"] = (rec or {}).get("wall_s")
            row[f"{tag}_version"] = (rec or {}).get("version")
            row[f"{tag}_engine"] = (rec or {}).get("engine")
        cl = _load(os.path.join(d, "classical.json"))
        row["classical"] = {m.get("model"): m.get("accuracy") for m in (cl or {}).get("models", [])} or None
        rows.append(row)
    return rows


def differences(rows, key):
    """PSF-Zero minus Qiskit; Qiskit failed -> seed left out; PSF-Zero failed -> its worst value."""
    ds, out = [], []
    for r in rows:
        q = r[f"qk_{key}"]
        if q is None:
            out.append(r["seed"])
            continue
        p = r[f"psf_{key}"]
        ds.append((p if p is not None else q + WORST[key]) - q)
    return ds, out


def verdict(ds):
    if not ds:
        return "NOT DECIDED", None, None
    m = sum(ds) / len(ds)
    p = sign_flip_p(ds)
    return ("REFUTED" if m <= 0 else "CONFIRMED" if p <= ALPHA else "NOT DECIDED"), m, p


def score(rows):
    res = {}
    bad = [r["seed"] for r in rows if not (r["psf_ok"] and r["qk_ok"])]
    res["B1"] = dict(verdict="CONFIRMED" if not bad else "REFUTED", seeds_not_valid=bad)
    for bid, key in (("B2", "noiseless_accuracy"), ("B3", "accuracy"), ("B4", "margin")):
        ds, out = differences(rows, key)
        v, m, p = verdict(ds)
        n = len(ds)
        sd = math.sqrt(sum((d - m) ** 2 for d in ds) / (n - 1)) if n > 1 else None
        res[bid] = dict(verdict=v, key=key, mean_difference=m, p=p, seeds=n, left_out=out,
                        interval95=[m - 1.96 * sd / math.sqrt(n), m + 1.96 * sd / math.sqrt(n)] if sd else None,
                        psf_better=sum(1 for d in ds if d > 1e-12), equal=sum(1 for d in ds if abs(d) <= 1e-12),
                        qiskit_better=sum(1 for d in ds if d < -1e-12), worst=min(ds) if ds else None)
    fewer = [r["seed"] for r in rows if r["psf_iterations"] is None or r["qk_iterations"] is None
             or r["psf_iterations"] < r["qk_iterations"]]
    res["B5"] = dict(verdict="CONFIRMED" if not fewer else "REFUTED", seeds_with_fewer_or_missing=fewer)
    return res


def _f(x, d=3):
    return "-" if x is None else f"{x:.{d}f}"


def _st(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return "-"
    m = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else 0.0
    return f"mean {m:.3f} (sd {sd:.3f}; {min(xs):.3f}-{max(xs):.3f})"


def report(rows, res, seeds):
    r = res
    L = ["# TOQB loop budget run, n = 6, L = 8, 2 minutes of QPU: the score", "",
         f"Pre-registration: `prereg/2026-10-16-loop-n6-budget.md`. Seeds {seeds[0]}-{seeds[-1]} ({len(seeds)}).", "",
         "## Verdicts", "", "| ID | prediction | verdict | numbers |", "|---|---|---|---|",
         f"| B1 | every arm run valid, stopped within the budget, evaluated at the stop | {r['B1']['verdict']} | "
         f"not valid: {len(r['B1']['seeds_not_valid'])} |"]
    names = {"B2": "noiseless accuracy at the budget, PSF-Zero > Qiskit",
             "B3": "noisy accuracy at the budget, PSF-Zero > Qiskit",
             "B4": "noisy margin at the budget, PSF-Zero > Qiskit"}
    for bid in ("B2", "B3", "B4"):
        x = r[bid]
        iv = x["interval95"]
        L.append(f"| {bid} | {names[bid]} | {x['verdict']} | mean difference {_f(x['mean_difference'], 4)} "
                 f"(95% {_f(iv[0], 4) if iv else '-'} to {_f(iv[1], 4) if iv else '-'}), p = {_f(x['p'], 6)}; "
                 f"better / equal / worse: {x['psf_better']} / {x['equal']} / {x['qiskit_better']} of {x['seeds']}; "
                 f"worst seed {_f(x['worst'])} |")
    L.append(f"| B5 | PSF-Zero gets at least as many iterations as Qiskit within the budget, every seed | "
             f"{r['B5']['verdict']} | fewer or missing: {len(r['B5']['seeds_with_fewer_or_missing'])} |")
    a_p = [x["psf_accuracy"] for x in rows if x["psf_accuracy"] is not None]
    a_q = [x["qk_accuracy"] for x in rows if x["qk_accuracy"] is not None]
    x = r["B3"]
    L += ["", "## The two numbers", "",
          f"- **Display:** mean accuracy at 2 minutes of QPU, noisy: PSF-Zero {_f(sum(a_p) / len(a_p) if a_p else None)}, "
          f"Qiskit level 2 {_f(sum(a_q) / len(a_q) if a_q else None)}.",
          f"- **Essential:** PSF-Zero gave the better model in {x['psf_better']} of {x['seeds']} seeds, the same in "
          f"{x['equal']}, a worse one in {x['qiskit_better']}; worst seed {_f(x['worst'])}.",
          "", "## Reported without prediction", "", "| quantity | PSF-Zero | Qiskit level 2 |", "|---|---|---|"]
    for key, label in (("accuracy", "accuracy at the budget, noisy"),
                       ("noiseless_accuracy", "accuracy at the budget, noiseless"), ("margin", "margin, noisy"),
                       ("iterations", "iterations within the budget"), ("batch_usd", "spent, batch $"),
                       ("q2", "two-qubit gates"), ("duration_us", "duration, us"), ("wall_s", "wall time per arm, s")):
        L.append(f"| {label} | {_st([x[f'psf_{key}'] for x in rows])} | {_st([x[f'qk_{key}'] for x in rows])} |")
    cl = next((x["classical"] for x in rows if x["classical"]), None)
    if cl:
        L += ["", "Classical reference (the same task for every seed): " +
              ", ".join(f"{m} {_f(v)}" for m, v in cl.items()) + "."]
    vs = sorted({x[k] for x in rows for k in ("psf_version", "qk_version", "psf_engine") if x[k]})
    L += ["", "Versions and engine: " + "; ".join(vs) + "."]
    return "\n".join(L) + "\n"


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    root = argv[0]
    first, last = FIRST, LAST
    if "--seeds" in argv:
        first, last = (int(v) for v in argv[argv.index("--seeds") + 1].split("-"))
    seeds = list(range(first, last + 1))
    md, js = os.path.join(root, "score.md"), os.path.join(root, "score.json")
    if os.path.exists(md) or os.path.exists(js):
        print(f"{root} already has a score: it is never overwritten", file=sys.stderr)
        return 2
    rows = collect(root, seeds)
    res = score(rows)
    text = report(rows, res, seeds)
    with open(js, "w", encoding="utf-8") as f:
        json.dump(dict(seeds=[first, last], alpha=ALPHA, verdicts=res, rows=rows), f, indent=1)
    with open(md, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
