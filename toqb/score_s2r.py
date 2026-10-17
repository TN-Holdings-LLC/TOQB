"""Scores S2R stage 0 (`toqb.s2r`) against its pre-registration, prereg/2026-10-17-s2r-stage0.md.

    python -m toqb.score_s2r <run folder> [--seeds FIRST-LAST]

Per seed, four records in seed<S>/: s2r-<arm>.json and spsa-<arm>.json for the two compilers. Per run, the final
stand-in test accuracy is that of the last evaluation (the model the budget bought). Paired differences per seed:

- S2: S2R, PSF-Zero minus Qiskit level 2, final stand-in test accuracy;
- S3: S2R, PSF-Zero minus Qiskit level 2, the mean over loops of the Spearman correlation between the simulated and
  the stand-in's losses of the k candidates sent to the stand-in;
- S4: S2R minus device-only SPSA, final stand-in test accuracy, per compiler (two tests; both must hold).

Each is tested by the one-sided sign-flip test of the mean (`toqb.score_loop_preg2.sign_flip_p`: exact for 20 seeds
or fewer). Writes score.md and score.json; never overwrites a score.
"""
import json
import math
import os
import sys

from toqb.score_loop_preg2 import sign_flip_p

PSF = "psfai:template"
QK = "qiskit:2:target:template"
FIRST, LAST = 9001, 9020
ALPHA = 0.01


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _name(kind, arm):
    return f"{kind}-{arm.replace(':', '_')}.json"


def final_accuracy(rec):
    return rec["evals"][-1]["accuracy"]


def mean_spearman(rec):
    v = [lp["spearman"] for lp in rec["loops"] if lp.get("spearman") is not None]
    return sum(v) / len(v) if v else None


def collect(root, seeds):
    rows = []
    for s in seeds:
        d = os.path.join(root, f"seed{s}")
        row = dict(seed=s)
        for kind in ("s2r", "spsa"):
            for tag, arm in (("psf", PSF), ("qk", QK)):
                rec = _load(os.path.join(d, _name(kind, arm)))
                key = f"{kind}_{tag}"
                ok = bool(rec and rec.get("valid") and rec.get("evals"))
                if ok and kind == "s2r":
                    ok = bool(rec.get("loops"))
                row[f"{key}_ok"] = ok
                row[f"{key}_error"] = (rec or {}).get("error", None if rec else "no record")
                if ok:
                    row[f"{key}_acc"] = final_accuracy(rec)
                    row[f"{key}_usd"] = rec["spent_usd"]
                    row[f"{key}_version"] = rec.get("version")
                    if kind == "s2r":
                        row[f"{key}_rho"] = mean_spearman(rec)
                        row[f"{key}_loops"] = len(rec["loops"])
                        row[f"{key}_curve"] = [e["accuracy"] for e in rec["evals"]]
                        row[f"{key}_sim_acc"] = rec["evals"][-1].get("sim_accuracy")
                        row[f"{key}_noiseless"] = rec["evals"][-1].get("noiseless_accuracy")
                    else:
                        row[f"{key}_iterations"] = rec.get("iterations")
        rows.append(row)
    return rows


def _test(ds):
    ds = [d for d in ds if d is not None]
    if not ds:
        return dict(verdict="NOT DECIDED", mean_difference=None, p=None, seeds=0)
    m = sum(ds) / len(ds)
    p = sign_flip_p(ds)
    n = len(ds)
    sd = math.sqrt(sum((d - m) ** 2 for d in ds) / (n - 1)) if n > 1 else None
    return dict(verdict="REFUTED" if m <= 0 else "CONFIRMED" if p <= ALPHA else "NOT DECIDED", mean_difference=m,
                p=p, seeds=n, interval95=[m - 1.96 * sd / math.sqrt(n), m + 1.96 * sd / math.sqrt(n)] if sd else None,
                better=sum(1 for d in ds if d > 1e-12), equal=sum(1 for d in ds if abs(d) <= 1e-12),
                worse=sum(1 for d in ds if d < -1e-12))


def score(rows):
    res = {}
    bad = [(r["seed"], k) for r in rows for k in ("s2r_psf", "s2r_qk", "spsa_psf", "spsa_qk") if not r[f"{k}_ok"]]
    res["S1"] = dict(verdict="CONFIRMED" if not bad else "REFUTED", not_valid=bad)
    both = [r for r in rows if r["s2r_psf_ok"] and r["s2r_qk_ok"]]
    res["S2"] = _test([r["s2r_psf_acc"] - r["s2r_qk_acc"] for r in both])
    res["S3"] = _test([None if r["s2r_psf_rho"] is None or r["s2r_qk_rho"] is None else
                       r["s2r_psf_rho"] - r["s2r_qk_rho"] for r in both])
    s4 = {}
    for tag in ("psf", "qk"):
        ok = [r for r in rows if r[f"s2r_{tag}_ok"] and r[f"spsa_{tag}_ok"]]
        s4[tag] = _test([r[f"s2r_{tag}_acc"] - r[f"spsa_{tag}_acc"] for r in ok])
    v = [s4["psf"]["verdict"], s4["qk"]["verdict"]]
    s4["verdict"] = "CONFIRMED" if v == ["CONFIRMED"] * 2 else "REFUTED" if "REFUTED" in v else "NOT DECIDED"
    res["S4"] = s4
    return res


def _f(x, d=3):
    return "-" if x is None else f"{x:.{d}f}"


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _numbers(x, d=3):
    iv = x.get("interval95")
    return (f"mean {_f(x['mean_difference'], d)} (95% {_f(iv[0], d) if iv else '-'} to {_f(iv[1], d) if iv else '-'}), "
            f"p = {_f(x['p'], 6)}; better / equal / worse: {x.get('better', 0)} / {x.get('equal', 0)} / "
            f"{x.get('worse', 0)} of {x['seeds']}")


def report(rows, res, seeds):
    L = ["# TOQB S2R stage 0: the score", "",
         f"Pre-registration: `prereg/2026-10-17-s2r-stage0.md`. Seeds {seeds[0]}-{seeds[-1]} ({len(seeds)}).", "",
         "## Verdicts", "", "| ID | prediction | verdict | numbers |", "|---|---|---|---|",
         f"| S1 | every run valid | {res['S1']['verdict']} | not valid: {len(res['S1']['not_valid'])} |",
         f"| S2 | S2R: PSF-Zero's final stand-in test accuracy higher than Qiskit level 2's | {res['S2']['verdict']} | "
         f"{_numbers(res['S2'])} |",
         f"| S3 | S2R: the simulator's ranking agrees better with the stand-in's for PSF-Zero (mean Spearman) | "
         f"{res['S3']['verdict']} | {_numbers(res['S3'])} |",
         f"| S4 | S2R beats device-only SPSA at the same budget, for each compiler | {res['S4']['verdict']} | PSF-Zero: "
         f"{_numbers(res['S4']['psf'])}; Qiskit: {_numbers(res['S4']['qk'])} |", "",
         "## Reported without prediction", "", "| quantity | PSF-Zero | Qiskit level 2 |", "|---|---|---|"]
    for key, label, d in (("s2r_{}_acc", "S2R: final stand-in test accuracy (mean)", 3),
                          ("spsa_{}_acc", "device-only SPSA: final stand-in test accuracy (mean)", 3),
                          ("s2r_{}_sim_acc", "S2R: final simulated test accuracy (mean)", 3),
                          ("s2r_{}_noiseless", "S2R: final noiseless test accuracy (mean)", 3),
                          ("s2r_{}_rho", "S2R: Spearman, simulator vs stand-in, top k (mean)", 3),
                          ("s2r_{}_loops", "S2R: loops within the budget (mean)", 2),
                          ("s2r_{}_usd", "S2R: dollars spent (mean)", 2),
                          ("spsa_{}_iterations", "SPSA: iterations within the budget (mean)", 1),
                          ("spsa_{}_usd", "SPSA: dollars spent (mean)", 2)):
        L.append(f"| {label} | {_f(_mean([r.get(key.format('psf')) for r in rows]), d)} | "
                 f"{_f(_mean([r.get(key.format('qk')) for r in rows]), d)} |")
    L += ["", "S2R, mean stand-in test accuracy after each loop (PSF-Zero / Qiskit level 2):", ""]
    for t in range(max([len(r.get("s2r_psf_curve") or []) for r in rows] + [0])):
        p = [r["s2r_psf_curve"][t] for r in rows if r.get("s2r_psf_curve") and len(r["s2r_psf_curve"]) > t]
        q = [r["s2r_qk_curve"][t] for r in rows if r.get("s2r_qk_curve") and len(r["s2r_qk_curve"]) > t]
        if p and q:
            L.append(f"- loop {t}: {sum(p) / len(p):.3f} / {sum(q) / len(q):.3f} ({len(p)} / {len(q)} seeds)")
    vs = sorted({r[k] for r in rows for k in r if k.endswith("_version") and r[k]})
    L += ["", "Versions: " + "; ".join(vs) + "."]
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
        json.dump(dict(seeds=[first, last], alpha=ALPHA, verdicts=res,
                       rows=[{k: v for k, v in r.items() if not k.endswith("_curve")} for r in rows]), f, indent=1)
    with open(md, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
