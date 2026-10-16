"""Scores the loop reach run (n = 6, L = 8, run 1's SPSA, 1,000 iterations, test evaluations every 50) against its
pre-registration, prereg/2026-10-16-loop-n6-reach.md.

    python -m toqb.score_loop_preg5 <run folder> [--seeds FIRST-LAST]

For each arm and seed: the first evaluation whose noisy test accuracy reaches a target (0.65, 0.70), its iteration and
its batch dollars. An arm that never reaches the target counts as reaching it at 1,050 iterations, for the iteration's
price times 1,050. d = Qiskit minus PSF-Zero per seed (positive: PSF-Zero got there sooner or cheaper). The test is
preg2's one-sided sign-flip test of the mean of d (200,000 random patterns, fixed seed). Writes score.md and
score.json; never overwrites a score.
"""
import json
import math
import os
import sys

from toqb.score_loop_preg2 import sign_flip_p

PSF = "psfai:template"
QK = "qiskit:2:target:template"
FIRST, LAST = 8001, 8200
ITERATIONS, EVERY, CENSOR = 1000, 50, 1050
TARGETS = (0.65, 0.70)
ALPHA = 0.01


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def reach(rec, target):
    """(iteration, dollars, reached) for the first evaluation at or above `target`; censored at CENSOR."""
    evals = [e for e in rec["evals"] if e["iteration"] > 0]
    hit = next((e for e in evals if e["accuracy"] >= target - 1e-12), None)
    if hit is not None:
        return hit["iteration"], hit["batch_usd"], True
    last = max(evals, key=lambda e: e["iteration"])
    return CENSOR, last["batch_usd"] * CENSOR / last["iteration"], False


def collect(root, seeds):
    rows = []
    want = set(range(EVERY, ITERATIONS + 1, EVERY))
    for s in seeds:
        d = os.path.join(root, f"seed{s}")
        row = dict(seed=s)
        for tag, arm in (("psf", PSF), ("qk", QK)):
            rec = _load(os.path.join(d, f"arm-{arm.replace(':', '_')}.json"))
            its = {e["iteration"] for e in (rec or {}).get("evals", [])}
            ok = bool(rec and rec.get("valid") and want <= its)
            row[f"{tag}_ok"] = ok
            row[f"{tag}_error"] = (rec or {}).get("error", None if rec else "no record")
            if ok:
                for t in TARGETS:
                    it, usd, got = reach(rec, t)
                    row[f"{tag}_it_{t}"], row[f"{tag}_usd_{t}"], row[f"{tag}_hit_{t}"] = it, usd, got
                fin = max(rec["evals"], key=lambda e: e["iteration"])
                row[f"{tag}_final_acc"] = fin["accuracy"]
                row[f"{tag}_final_noiseless"] = fin.get("noiseless_accuracy")
                row[f"{tag}_curve"] = {e["iteration"]: e["accuracy"] for e in rec["evals"]}
                row[f"{tag}_usd_per_it"] = fin["batch_usd"] / fin["iteration"]
            row[f"{tag}_version"] = (rec or {}).get("version")
            row[f"{tag}_engine"] = (rec or {}).get("engine")
        rows.append(row)
    return rows


def verdict(ds):
    if not ds:
        return "NOT DECIDED", None, None
    m = sum(ds) / len(ds)
    p = sign_flip_p(ds)
    return ("REFUTED" if m <= 0 else "CONFIRMED" if p <= ALPHA else "NOT DECIDED"), m, p


def _pair(rows, key):
    ok = [r for r in rows if r["psf_ok"] and r["qk_ok"]]
    return [r[f"qk_{key}"] - r[f"psf_{key}"] for r in ok]


def score(rows):
    res = {}
    bad = [r["seed"] for r in rows if not (r["psf_ok"] and r["qk_ok"])]
    res["R1"] = dict(verdict="CONFIRMED" if not bad else "REFUTED", seeds_not_valid=bad)
    for rid, key in (("R2", "it_0.65"), ("R3", "it_0.7"), ("R4", "usd_0.65")):
        ds = _pair(rows, key)
        v, m, p = verdict(ds)
        n = len(ds)
        sd = math.sqrt(sum((d - m) ** 2 for d in ds) / (n - 1)) if n > 1 else None
        res[rid] = dict(verdict=v, key=key, mean_difference=m, p=p, seeds=n,
                        interval95=[m - 1.96 * sd / math.sqrt(n), m + 1.96 * sd / math.sqrt(n)] if sd else None,
                        psf_sooner=sum(1 for d in ds if d > 1e-12), equal=sum(1 for d in ds if abs(d) <= 1e-12),
                        qiskit_sooner=sum(1 for d in ds if d < -1e-12))
    return res


def _f(x, d=3):
    return "-" if x is None else f"{x:.{d}f}"


def _med(xs):
    xs = sorted(xs)
    if not xs:
        return None
    k = len(xs) // 2
    return xs[k] if len(xs) % 2 else (xs[k - 1] + xs[k]) / 2


def report(rows, res, seeds):
    ok = [r for r in rows if r["psf_ok"] and r["qk_ok"]]
    L = ["# TOQB loop reach run, n = 6, L = 8, 1,000 iterations: the score", "",
         f"Pre-registration: `prereg/2026-10-16-loop-n6-reach.md`. Seeds {seeds[0]}-{seeds[-1]} ({len(seeds)}).", "",
         "## Verdicts", "", "| ID | prediction | verdict | numbers |", "|---|---|---|---|",
         f"| R1 | every arm run valid, 1,000 iterations, evaluated every 50 | {res['R1']['verdict']} | not valid: "
         f"{len(res['R1']['seeds_not_valid'])} |"]
    names = {"R2": "iterations to a noisy test accuracy of 0.65, fewer with PSF-Zero",
             "R3": "iterations to 0.70, fewer with PSF-Zero",
             "R4": "dollars to 0.65, fewer with PSF-Zero"}
    for rid in ("R2", "R3", "R4"):
        x = res[rid]
        iv = x["interval95"]
        L.append(f"| {rid} | {names[rid]} | {x['verdict']} | mean Qiskit - PSF-Zero {_f(x['mean_difference'], 2)} "
                 f"(95% {_f(iv[0], 2) if iv else '-'} to {_f(iv[1], 2) if iv else '-'}), p = {_f(x['p'], 6)}; "
                 f"PSF-Zero sooner / equal / later: {x['psf_sooner']} / {x['equal']} / {x['qiskit_sooner']} of "
                 f"{x['seeds']} |")
    L += ["", "## Reported without prediction", "", "| quantity | PSF-Zero | Qiskit level 2 |", "|---|---|---|"]
    for t in TARGETS:
        for tag_label, key in (("reached within 1,000 iterations", "hit"), ("iterations to reach (median, censored "
                                                                            "at 1,050)", "it"),
                               ("dollars to reach (median)", "usd")):
            if key == "hit":
                p = sum(1 for r in ok if r[f"psf_hit_{t}"])
                q = sum(1 for r in ok if r[f"qk_hit_{t}"])
                L.append(f"| {t:.2f}: {tag_label} | {p} of {len(ok)} | {q} of {len(ok)} |")
            else:
                L.append(f"| {t:.2f}: {tag_label} | {_f(_med([r[f'psf_{key}_{t}'] for r in ok]), 1)} | "
                         f"{_f(_med([r[f'qk_{key}_{t}'] for r in ok]), 1)} |")
    L.append(f"| accuracy at 1,000 iterations, noisy (mean) | {_f(sum(r['psf_final_acc'] for r in ok) / len(ok))} | "
             f"{_f(sum(r['qk_final_acc'] for r in ok) / len(ok))} |" if ok else "")
    L.append(f"| dollars per iteration | {_f(_med([r['psf_usd_per_it'] for r in ok]), 4)} | "
             f"{_f(_med([r['qk_usd_per_it'] for r in ok]), 4)} |" if ok else "")
    L += ["", "Mean noisy test accuracy by iteration (PSF-Zero / Qiskit level 2):", ""]
    for it in range(0, ITERATIONS + 1, EVERY):
        p = [r["psf_curve"].get(it) for r in ok if r["psf_curve"].get(it) is not None]
        q = [r["qk_curve"].get(it) for r in ok if r["qk_curve"].get(it) is not None]
        if p and q:
            L.append(f"- {it}: {sum(p) / len(p):.3f} / {sum(q) / len(q):.3f}")
    vs = sorted({r[k] for r in rows for k in ("psf_version", "qk_version", "psf_engine") if r[k]})
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
        json.dump(dict(seeds=[first, last], alpha=ALPHA, verdicts=res,
                       rows=[{k: v for k, v in r.items() if not k.endswith("_curve")} for r in rows]), f, indent=1)
    with open(md, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
