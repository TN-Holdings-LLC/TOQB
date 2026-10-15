"""Scores the loop standard run (n = 6, L = 8) against its pre-registration, prereg/2026-10-15-loop-n6-standard.md.

    python -m toqb.score_loop_preg <run folder> [--seeds 101,102,...]

The run folder holds one folder per seed, `seed<N>/`, each written by `python -m toqb.task_loop run`. Writes
`score.md` and `score.json` into the run folder and prints the report. It refuses to overwrite an existing score.

The paired test is an exact one-sided sign-flip test on the per-seed differences PSF-Zero minus Qiskit: under the null
hypothesis each difference is as likely to have either sign, and p is the share of the 2^n sign patterns whose mean
is at least the observed mean. numpy only.
"""
import json
import math
import os
import sys

PSF = "psfai:template"
QK = "qiskit:2:target:template"
SEEDS = list(range(101, 121))
ALPHA = 0.01           # L2-L4: confirmed if mean > 0 and p <= ALPHA; refuted if mean <= 0
EFFECT_CONFIRM = 0.10  # L5: mean noiseless difference >= this confirms
EFFECT_REFUTE = 0.05   # L5: below this refutes
WORST = {"noiseless_accuracy": -1.0, "accuracy": -1.0, "margin": -2.0}  # a failed PSF-Zero arm counts as the worst


def sign_flip_p(d):
    """Exact one-sided p of mean(d) under random sign flips: share of the 2^n patterns with mean >= the observed."""
    import numpy as np
    d = np.asarray(d, dtype=float)
    n = len(d)
    if n == 0:
        return None
    obs = d.sum()
    hits, total = 0, 1 << n
    chunk = 1 << min(n, 16)
    bits = np.arange(n)
    for start in range(0, total, chunk):
        idx = np.arange(start, min(start + chunk, total), dtype=np.int64)
        signs = 1 - 2 * ((idx[:, None] >> bits) & 1)
        hits += int(np.count_nonzero(signs @ d >= obs - 1e-12))
    return hits / total


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _final(rec, key):
    """The value at the last evaluation (iteration = the plan's iterations), or None."""
    if not rec or not rec.get("valid") or not rec.get("evals"):
        return None
    return rec["evals"][-1].get(key)


def collect(root, seeds):
    rows = []
    for s in seeds:
        d = os.path.join(root, f"seed{s}")
        psf = _load(os.path.join(d, f"arm-{PSF.replace(':', '_')}.json"))
        qk = _load(os.path.join(d, f"arm-{QK.replace(':', '_')}.json"))
        plan = _load(os.path.join(d, "plan.json")) or {}
        iters = plan.get("optimizer", {}).get("iterations")
        row = dict(seed=s, psf_valid=bool(psf and psf.get("valid")), qk_valid=bool(qk and qk.get("valid")),
                   psf_error=(psf or {}).get("error", None if psf else "no record"),
                   qk_error=(qk or {}).get("error", None if qk else "no record"))
        for rec, tag in ((psf, "psf"), (qk, "qk")):
            last = (rec or {}).get("evals", [{}])[-1] if rec and rec.get("evals") else {}
            row[f"{tag}_last_iteration"] = last.get("iteration")
            row[f"{tag}_complete"] = bool(last) and last.get("iteration") == iters
            for key in ("accuracy", "margin", "noiseless_accuracy"):
                row[f"{tag}_{key}"] = _final(rec, key) if row[f"{tag}_complete"] else None
            sp = (rec or {}).get("spent", {})
            row[f"{tag}_batch_usd"] = sp.get("batch_usd")
            row[f"{tag}_session_usd"] = sp.get("session_usd")
            row[f"{tag}_q2"] = (rec or {}).get("q2_mean")
            row[f"{tag}_duration_us"] = (rec or {}).get("duration_us_mean")
            row[f"{tag}_version"] = (rec or {}).get("version")
            row[f"{tag}_wall_s"] = (rec or {}).get("wall_s")
            eq = (rec or {}).get("equivalence", [])
            row[f"{tag}_eq"] = f"{sum(1 for e in eq if e.get('checked') and e.get('equivalent'))} of " \
                               f"{sum(1 for e in eq if e.get('checked'))}"
            tt = ((rec or {}).get("to_target") or {}).get("batch")
            row[f"{tag}_to_target_usd"] = tt["usd"] if tt else None
        cl = _load(os.path.join(d, "classical.json"))
        row["classical"] = {m.get("model"): m.get("accuracy") for m in (cl or {}).get("models", [])} or None
        rows.append(row)
    return rows


def differences(rows, key):
    """Per-seed PSF-Zero minus Qiskit. A seed whose Qiskit arm failed is left out; a failed PSF-Zero arm counts as the
    worst value. Returns (differences, seeds used, seeds left out)."""
    ds, used, out = [], [], []
    for r in rows:
        q = r[f"qk_{key}"]
        if q is None:
            out.append(r["seed"])
            continue
        p = r[f"psf_{key}"]
        ds.append((p if p is not None else q + WORST[key]) - q)
        used.append(r["seed"])
    return ds, used, out


def _stats(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return None
    m = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else 0.0
    srt = sorted(xs)
    med = srt[len(xs) // 2] if len(xs) % 2 else (srt[len(xs) // 2 - 1] + srt[len(xs) // 2]) / 2
    return dict(n=len(xs), mean=m, sd=sd, median=med, min=srt[0], max=srt[-1])


def score(rows):
    res = {}
    bad = [r["seed"] for r in rows if not (r["psf_valid"] and r["qk_valid"] and r["psf_complete"] and r["qk_complete"])]
    res["L1"] = dict(verdict="CONFIRMED" if not bad else "REFUTED", seeds_not_valid_or_incomplete=bad)
    for lid, key in (("L2", "noiseless_accuracy"), ("L3", "accuracy"), ("L4", "margin")):
        ds, used, out = differences(rows, key)
        mean = sum(ds) / len(ds) if ds else None
        p = sign_flip_p(ds) if ds else None
        if mean is None:
            v = "NOT DECIDED"
        elif mean <= 0:
            v = "REFUTED"
        elif p <= ALPHA:
            v = "CONFIRMED"
        else:
            v = "NOT DECIDED"
        res[lid] = dict(verdict=v, key=key, mean_difference=mean, p=p, seeds=len(used), left_out=out,
                        psf_better=sum(1 for d in ds if d > 1e-12), equal=sum(1 for d in ds if abs(d) <= 1e-12),
                        qiskit_better=sum(1 for d in ds if d < -1e-12), worst=min(ds) if ds else None,
                        best=max(ds) if ds else None)
    m = res["L2"]["mean_difference"]
    res["L5"] = dict(verdict="NOT DECIDED" if m is None else "CONFIRMED" if m >= EFFECT_CONFIRM else
                     "REFUTED" if m < EFFECT_REFUTE else "NOT DECIDED", mean_difference=m)
    over = [r["seed"] for r in rows if r["psf_batch_usd"] is None or r["qk_batch_usd"] is None
            or r["psf_batch_usd"] > r["qk_batch_usd"]]
    res["L6"] = dict(verdict="CONFIRMED" if not over else "REFUTED", seeds_where_psf_spent_more_or_missing=over)
    return res


def _f(x, d=3):
    return "-" if x is None else f"{x:.{d}f}"


def report(rows, res, seeds):
    L = ["# TOQB loop standard run, n = 6, L = 8: the score", "",
         "Pre-registration: `prereg/2026-10-15-loop-n6-standard.md`. Seeds: "
         f"{seeds[0]}-{seeds[-1]} ({len(seeds)}).", "", "## Verdicts", "",
         "| ID | prediction | verdict | numbers |", "|---|---|---|---|"]
    r = res
    L.append(f"| L1 | every arm run valid and complete | {r['L1']['verdict']} | not valid or incomplete: "
             f"{r['L1']['seeds_not_valid_or_incomplete'] or 'none'} |")
    names = {"L2": "noiseless final accuracy, PSF-Zero > Qiskit", "L3": "noisy final accuracy, PSF-Zero > Qiskit",
             "L4": "noisy final margin, PSF-Zero > Qiskit"}
    for lid in ("L2", "L3", "L4"):
        x = r[lid]
        L.append(f"| {lid} | {names[lid]} | {x['verdict']} | mean difference {_f(x['mean_difference'])}, "
                 f"p = {_f(x['p'], 6)}, PSF-Zero better / equal / Qiskit better: {x['psf_better']} / {x['equal']} / "
                 f"{x['qiskit_better']} of {x['seeds']}; worst seed {_f(x['worst'])}"
                 f"{'; left out ' + str(x['left_out']) if x['left_out'] else ''} |")
    L.append(f"| L5 | mean noiseless difference >= {EFFECT_CONFIRM} | {r['L5']['verdict']} | "
             f"{_f(r['L5']['mean_difference'])} |")
    L.append(f"| L6 | PSF-Zero spends no more than Qiskit on the whole training, every seed | {r['L6']['verdict']} | "
             f"seeds over or missing: {r['L6']['seeds_where_psf_spent_more_or_missing'] or 'none'} |")
    L += ["", "## The two numbers", ""]
    a_p = _stats([x["psf_accuracy"] for x in rows])
    a_q = _stats([x["qk_accuracy"] for x in rows])
    L.append("- **Display (the benchmark's headline):** mean final accuracy on the test set, noisy, for the same "
             f"money: PSF-Zero {_f(a_p and a_p['mean'])}, Qiskit level 2 {_f(a_q and a_q['mean'])}.")
    x = r["L3"]
    L.append(f"- **Essential (for someone who trains once):** PSF-Zero gave the better model in {x['psf_better']} of "
             f"{x['seeds']} seeds, the same in {x['equal']}, a worse one in {x['qiskit_better']}; the worst seed's "
             f"difference was {_f(x['worst'])}. Noiseless, i.e. how far the training itself went: mean difference "
             f"{_f(r['L2']['mean_difference'])}.")
    L += ["", "## Reported without prediction", "", "| quantity | PSF-Zero | Qiskit level 2 |", "|---|---|---|"]
    for key, label in (("accuracy", "final accuracy, noisy"), ("noiseless_accuracy", "final accuracy, noiseless"),
                       ("margin", "final margin, noisy"), ("batch_usd", "whole training, batch $"),
                       ("session_usd", "whole training, session $"), ("q2", "two-qubit gates"),
                       ("duration_us", "duration, us"), ("wall_s", "wall time per arm, s")):
        sp, sq = _stats([x[f"psf_{key}"] for x in rows]), _stats([x[f"qk_{key}"] for x in rows])
        fmt = (lambda s: "-" if s is None else
               f"mean {_f(s['mean'])} (sd {_f(s['sd'])}; median {_f(s['median'])}; {_f(s['min'])}-{_f(s['max'])})")
        L.append(f"| {label} | {fmt(sp)} | {fmt(sq)} |")
    tp = [x["psf_to_target_usd"] for x in rows if x["psf_to_target_usd"] is not None]
    tq = [x["qk_to_target_usd"] for x in rows if x["qk_to_target_usd"] is not None]
    L.append(f"| reached accuracy 0.7 (seeds; median $ to reach it, batch) | {len(tp)} of {len(rows)}; "
             f"{_f(_stats(tp)['median'], 2) if tp else '-'} | {len(tq)} of {len(rows)}; "
             f"{_f(_stats(tq)['median'], 2) if tq else '-'} |")
    cl = next((x["classical"] for x in rows if x["classical"]), None)
    if cl:
        L.append("")
        L.append("Classical reference (the same task for every seed): " +
                 ", ".join(f"{m} {_f(v)}" for m, v in cl.items()) + ".")
    vs = sorted({x["psf_version"] for x in rows if x["psf_version"]} | {x["qk_version"] for x in rows if x["qk_version"]})
    L += ["", "Versions: " + "; ".join(vs) + ".", "", "## Per seed", "",
          "| seed | PSF-Zero noisy / noiseless / margin | Qiskit noisy / noiseless / margin | $ batch PSF-Zero / Qiskit "
          "| equivalence PSF-Zero / Qiskit |", "|---|---|---|---|---|"]
    for x in rows:
        L.append(f"| {x['seed']} | {_f(x['psf_accuracy'])} / {_f(x['psf_noiseless_accuracy'])} / {_f(x['psf_margin'])}"
                 f"{' (' + str(x['psf_error']) + ')' if x['psf_error'] else ''} | {_f(x['qk_accuracy'])} / "
                 f"{_f(x['qk_noiseless_accuracy'])} / {_f(x['qk_margin'])}"
                 f"{' (' + str(x['qk_error']) + ')' if x['qk_error'] else ''} | {_f(x['psf_batch_usd'], 2)} / "
                 f"{_f(x['qk_batch_usd'], 2)} | {x['psf_eq']} / {x['qk_eq']} |")
    return "\n".join(L) + "\n"


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    root = argv[0]
    seeds = SEEDS
    if "--seeds" in argv:
        seeds = [int(s) for s in argv[argv.index("--seeds") + 1].split(",")]
    out_md, out_js = os.path.join(root, "score.md"), os.path.join(root, "score.json")
    if os.path.exists(out_md) or os.path.exists(out_js):
        print(f"{root} already has a score: it is never overwritten", file=sys.stderr)
        return 2
    rows = collect(root, seeds)
    res = score(rows)
    text = report(rows, res, seeds)
    with open(out_js, "w", encoding="utf-8") as f:
        json.dump(dict(seeds=seeds, alpha=ALPHA, effect=[EFFECT_REFUTE, EFFECT_CONFIRM], verdicts=res, rows=rows), f,
                  indent=1)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
