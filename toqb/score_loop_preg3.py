"""Scores the loop long run (n = 6, L = 8, the pilot's SPSA, 100,000 iterations, fast engine) against its pre-registration,
prereg/2026-10-15-loop-n6-long.md.

    python -m toqb.score_loop_preg3 <run folder> [--seeds FIRST-LAST] [--partial]

The run folder holds `seed<N>/` per seed, each written by `python -m toqb.task_loop run`. Writes `score.md` and
`score.json` into the run folder; never overwrites a score.

The paired test is a one-sided sign-flip test of the mean of per-seed differences (PSF-Zero minus Qiskit): exact for
at most 20 seeds, otherwise over 200,000 random sign patterns drawn with a fixed seed (p counted with the observed
pattern included). With 5 seeds the test is exact (32 patterns): p <= 0.05 needs every seed
on one side, or nearly. numpy only.
"""
import json
import math
import os
import sys

from toqb.score_loop_preg import sign_flip_p as _exact_p

PSF = "psfai:template"
QK = "qiskit:2:target:template"
FIRST, LAST = 3001, 3005
ALPHA = 0.05
EARLY = 60           # N5: the difference at this iteration against the final one
PATTERNS = 200_000
PATTERN_SEED = 20261015
WORST = {"noiseless_accuracy": -1.0, "accuracy": -1.0, "margin": -2.0}


def sign_flip_p(d):
    import numpy as np
    d = np.asarray(d, dtype=float)
    if len(d) == 0:
        return None
    if len(d) <= 20:
        return _exact_p(d)
    rng = np.random.default_rng(PATTERN_SEED)
    obs = d.sum()
    hits = 0
    left = PATTERNS
    while left:
        m = min(left, 20_000)
        signs = rng.choice([-1.0, 1.0], size=(m, len(d)))
        hits += int(np.count_nonzero(signs @ d >= obs - 1e-12))
        left -= m
    return (hits + 1) / (PATTERNS + 1)


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _at(rec, it, key):
    for e in (rec or {}).get("evals", []):
        if e.get("iteration") == it:
            return e.get(key)
    return None


def collect(root, seeds):
    rows = []
    for s in seeds:
        d = os.path.join(root, f"seed{s}")
        plan = _load(os.path.join(d, "plan.json")) or {}
        iters = plan.get("optimizer", {}).get("iterations")
        row = dict(seed=s)
        for tag, arm in (("psf", PSF), ("qk", QK)):
            rec = _load(os.path.join(d, f"arm-{arm.replace(':', '_')}.json"))
            ok = bool(rec and rec.get("valid") and rec.get("evals") and rec["evals"][-1].get("iteration") == iters)
            row[f"{tag}_ok"] = ok
            row[f"{tag}_error"] = (rec or {}).get("error", None if rec else "no record")
            for key in ("accuracy", "margin", "noiseless_accuracy"):
                row[f"{tag}_{key}"] = _at(rec, iters, key) if ok else None
                row[f"{tag}_{key}_early"] = _at(rec, EARLY, key) if ok else None
            sp = (rec or {}).get("spent", {})
            row[f"{tag}_batch_usd"] = sp.get("batch_usd")
            row[f"{tag}_q2"] = (rec or {}).get("q2_mean")
            row[f"{tag}_duration_us"] = (rec or {}).get("duration_us_mean")
            row[f"{tag}_wall_s"] = (rec or {}).get("wall_s")
            row[f"{tag}_version"] = (rec or {}).get("version")
            row[f"{tag}_engine"] = (rec or {}).get("engine")
            tt = ((rec or {}).get("to_target") or {}).get("batch")
            row[f"{tag}_to_target_usd"] = tt["usd"] if tt else None
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
        ds.append((p if p is not None else q + WORST[key.replace("_early", "")]) - q)
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
    res["N1"] = dict(verdict="CONFIRMED" if not bad else "REFUTED", seeds_not_valid_or_incomplete=bad)
    for mid, key in (("N2", "noiseless_accuracy"), ("N3", "accuracy"), ("N4", "margin")):
        ds, out = differences(rows, key)
        v, m, p = verdict(ds)
        res[mid] = dict(verdict=v, key=key, mean_difference=m, p=p, seeds=len(ds), left_out=out,
                        psf_better=sum(1 for d in ds if d > 1e-12), equal=sum(1 for d in ds if abs(d) <= 1e-12),
                        qiskit_better=sum(1 for d in ds if d < -1e-12), worst=min(ds) if ds else None)
    # N5: does the noiseless difference grow from iteration EARLY to the end? Per seed: d_final - d_early.
    growth = []
    for r in rows:
        if r["psf_ok"] and r["qk_ok"]:
            growth.append((r["psf_noiseless_accuracy"] - r["qk_noiseless_accuracy"])
                          - (r["psf_noiseless_accuracy_early"] - r["qk_noiseless_accuracy_early"]))
    v, m, p = verdict(growth)
    d_early, _ = differences(rows, "noiseless_accuracy_early")
    res["N5"] = dict(verdict=v, mean_growth=m, p=p, seeds=len(growth),
                     mean_difference_early=sum(d_early) / len(d_early) if d_early else None,
                     mean_difference_final=res["N2"]["mean_difference"])
    over = [r["seed"] for r in rows if r["psf_batch_usd"] is None or r["qk_batch_usd"] is None
            or r["psf_batch_usd"] > r["qk_batch_usd"]]
    res["N6"] = dict(verdict="CONFIRMED" if not over else "REFUTED", seeds_over_or_missing=over)
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
    L = ["# TOQB loop long run, n = 6, L = 8, 100,000 iterations: the score", "",
         f"Pre-registration: `prereg/2026-10-15-loop-n6-long.md`. Seeds {seeds[0]}-{seeds[-1]} ({len(seeds)}).",
         "", "## Verdicts", "", "| ID | prediction | verdict | numbers |", "|---|---|---|---|",
         f"| N1 | every arm run valid and complete | {r['N1']['verdict']} | not valid or incomplete: "
         f"{len(r['N1']['seeds_not_valid_or_incomplete'])} |"]
    names = {"N2": "noiseless final accuracy, PSF-Zero > Qiskit", "N3": "noisy final accuracy, PSF-Zero > Qiskit",
             "N4": "noisy final margin, PSF-Zero > Qiskit"}
    for mid in ("N2", "N3", "N4"):
        x = r[mid]
        L.append(f"| {mid} | {names[mid]} | {x['verdict']} | mean difference {_f(x['mean_difference'])}, "
                 f"p = {_f(x['p'], 6)}; PSF-Zero better / equal / Qiskit better: {x['psf_better']} / {x['equal']} / "
                 f"{x['qiskit_better']} of {x['seeds']}; worst seed {_f(x['worst'])} |")
    x = r["N5"]
    L.append(f"| N5 | the noiseless difference grows from iteration {EARLY} to the end | {x['verdict']} | "
             f"{_f(x['mean_difference_early'])} at {EARLY}, {_f(x['mean_difference_final'])} at the end; mean growth "
             f"{_f(x['mean_growth'])}, p = {_f(x['p'], 6)} |")
    L.append(f"| N6 | PSF-Zero spends no more than Qiskit, every seed | {r['N6']['verdict']} | over or missing: "
             f"{len(r['N6']['seeds_over_or_missing'])} |")
    a_p = [x["psf_accuracy"] for x in rows if x["psf_accuracy"] is not None]
    a_q = [x["qk_accuracy"] for x in rows if x["qk_accuracy"] is not None]
    x = r["N3"]
    L += ["", "## The two numbers", "",
          f"- **Display:** mean final accuracy, noisy, for the same money: PSF-Zero {_f(sum(a_p) / len(a_p) if a_p else None)}"
          f", Qiskit level 2 {_f(sum(a_q) / len(a_q) if a_q else None)}.",
          f"- **Essential:** PSF-Zero gave the better model in {x['psf_better']} of {x['seeds']} seeds, a worse one in "
          f"{x['qiskit_better']}; worst seed {_f(x['worst'])}. Seeds reaching 0.7 (noisy, final): PSF-Zero "
          f"{sum(1 for v in a_p if v >= 0.7)}, Qiskit {sum(1 for v in a_q if v >= 0.7)}.",
          "", "## Reported without prediction", "", "| quantity | PSF-Zero | Qiskit level 2 |", "|---|---|---|"]
    for key, label in (("accuracy", "final accuracy, noisy"), ("noiseless_accuracy", "final accuracy, noiseless"),
                       ("margin", "final margin, noisy"), ("accuracy_early", f"accuracy at {EARLY}, noisy"),
                       ("noiseless_accuracy_early", f"accuracy at {EARLY}, noiseless"),
                       ("batch_usd", "whole training, batch $"), ("q2", "two-qubit gates"),
                       ("duration_us", "duration, us"), ("wall_s", "wall time per arm, s")):
        L.append(f"| {label} | {_st([x[f'psf_{key}'] for x in rows])} | {_st([x[f'qk_{key}'] for x in rows])} |")
    cl = next((x["classical"] for x in rows if x["classical"]), None)
    if cl:
        L += ["", "Classical reference (the same task for every seed): " +
              ", ".join(f"{m} {_f(v)}" for m, v in cl.items()) + "."]
    vs = sorted({x[k] for x in rows for k in ("psf_version", "qk_version", "psf_engine") if x[k]})
    L += ["", "Versions and engine: " + "; ".join(vs) + "."]
    return "\n".join(L) + "\n"


def trajectory(root, seeds):
    """Per evaluation point: mean PSF-Zero minus Qiskit, noiseless and noisy, and per-seed noiseless differences."""
    pts = {}
    for s in seeds:
        d = os.path.join(root, f"seed{s}")
        recs = [_load(os.path.join(d, f"arm-{a.replace(':', '_')}.json")) or
                _load(os.path.join(d, f"arm-{a.replace(':', '_')}.partial.json")) for a in (PSF, QK)]
        if not all(recs):
            continue
        ev = [{e["iteration"]: e for e in r.get("evals", [])} for r in recs]
        for it in sorted(set(ev[0]) & set(ev[1])):
            pts.setdefault(it, []).append((s, ev[0][it]["noiseless_accuracy"] - ev[1][it]["noiseless_accuracy"],
                                           ev[0][it]["accuracy"] - ev[1][it]["accuracy"],
                                           ev[0][it]["noiseless_accuracy"], ev[1][it]["noiseless_accuracy"]))
    L = ["", "## Trajectory (reported without prediction)", "",
         "| iteration | seeds | noiseless PSF-Zero / Qiskit (means) | difference noiseless | difference noisy | "
         "noiseless difference per seed |", "|---|---|---|---|---|---|"]
    for it in sorted(pts):
        v = pts[it]
        m = lambda i: sum(x[i] for x in v) / len(v)
        L.append(f"| {it} | {len(v)} | {m(3):.3f} / {m(4):.3f} | {m(1):+.3f} | {m(2):+.3f} | "
                 + ", ".join(f"{x[0]}: {x[1]:+.3f}" for x in v) + " |")
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
    if "--partial" in argv:  # a look at the trajectory while the run is going: writes nothing
        print(trajectory(root, seeds))
        return 0
    rows = collect(root, seeds)
    res = score(rows)
    text = report(rows, res, seeds) + trajectory(root, seeds)
    with open(js, "w", encoding="utf-8") as f:
        json.dump(dict(seeds=[first, last], alpha=ALPHA, early=EARLY, patterns=PATTERNS, pattern_seed=PATTERN_SEED,
                       verdicts=res, rows=rows), f, indent=1)
    with open(md, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
