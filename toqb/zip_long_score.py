"""Score of the long training with checkpoints, the zipper against item 31 (report only, one rule fixed before the
run in prereg/drafts-2026-10-23/zip_long_note.md):

    python -m toqb.zip_long_score RUNS_DIR UNDAMP_DIR OUT.md [--json OUT.json] [--alpha 0.01] [--prev PREV_RUNS_DIR]

RUNS_DIR: toqb.s2rc_ckpt records of gpu/zip_long.sh (L 16, teachers 11-13, seed 301, 16,000 loops, checkpoints 500,
1,000, 2,000, 4,000, 8,000 and the final); UNDAMP_DIR: toqb.undamp_run outputs at every point.

Per run and point: the trained model's own noiseless CE and accuracy on the test points and on the 64 training points
(exact, no noise); the twin's (lam, delta) on the training inputs; the stand-in CE without shots, raw and undamped;
the stand-in CE with the run's shots; the twin's CE on 100 test points from the training curve.

The rule (the only test): at 16,000 loops, per teacher, d_i = noiseless CE_i(item 31) - noiseless CE_i(zipper) on the
500 test points (positive favours the zipper); two-sided Wilcoxon signed-rank (toqb.match_score), Holm over the 3
teachers, alpha 0.01, WIN if the adjusted p < alpha and mean d > 0. The zipper's gain "persists" if it WINs in at
least 2 of 3 teachers. The same comparison at the other points is reported without a claim.

With --prev (yesterday's depth sweep runs, results/zip-depth-2026-10-22/runs): the parameters at 2,000 loops are
compared with those runs' final parameters (same plans up to the loop count; expected equal bit for bit).
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys

import numpy as np

from toqb import s2r2 as S2
from toqb import undamp as U
from toqb.match_score import Stop, ce_points, holm, signed_rank_z, verdict
from toqb.s2rc import _scores

ARMS = {"psfai:template": "item31", "psfai:template_zip": "zipper"}


def _ideal(theta, X, y, task):
    z = U.ideal_z(np.asarray(theta), X, task)
    ce, acc = _scores(z, np.asarray(y))
    return z, ce, acc


def load(runs_dir, und_dir):
    runs = {}
    for f in sorted(glob.glob(os.path.join(runs_dir, "*.json"))):
        name = os.path.basename(f)
        rec = json.load(open(f, encoding="utf-8"))
        if not rec.get("valid"):
            raise Stop(f"{name}: not a valid run ({rec.get('error')})")
        arm = ARMS.get(rec["arm"])
        if arm is None:
            raise Stop(f"{name}: unknown arm {rec['arm']}")
        und = json.load(open(os.path.join(und_dir, name), encoding="utf-8"))
        upts = {p["point"]: p for p in und["points"]}
        task = rec["task"]
        Xtr, ytr, Xte, yte = S2.teacher_data2(task)
        y = np.asarray(yte)
        pts = [(c["loop"], c["theta"], c["rehearsal"]) for c in rec["checkpoints"]]
        pts.append((rec["loops"], rec["final_mean"], rec["rehearsal"]))
        curve = {c["loop"]: c["twin_ce"] for c in rec["curve"]}
        rows = []
        for loop, theta, rh in pts:
            u = upts.get(f"loop {loop}")
            if u is None:
                raise Stop(f"{name}: no undamp output at loop {loop}")
            zte, ce_te, acc_te = _ideal(theta, Xte, yte, task)
            _, ce_tr, acc_tr = _ideal(theta, Xtr, ytr, task)
            p1 = np.asarray(rh["standin_p1"])
            pu = (1 - U.apply(1 - 2 * p1, u["lam"], u["delta"])) / 2
            rows.append(dict(loop=loop, theta=np.asarray(theta), noiseless_ce_pts=ce_points((1 - zte) / 2, y),
                             noiseless_ce=ce_te, noiseless_acc=acc_te, noiseless_train_ce=ce_tr,
                             noiseless_train_acc=acc_tr, lam=u["lam"], delta=u["delta"], fit_rms=u["fit_rms"],
                             standin_ce_raw_exact=float(ce_points(p1, y).mean()),
                             standin_ce_und_exact=float(ce_points(pu, y).mean()),
                             standin_ce_shots=rh["ce"], reproduced=u["raw"]["reproduced"],
                             twin_curve_ce=curve.get(loop)))
        key = (int(task["layers"]), int(task["teacher_seed"]))
        runs.setdefault(key, {})[arm] = dict(file=name, rows=rows, y=y)
    return runs


def score(runs, alpha=0.01, prev_dir=None):
    res = dict(alpha=alpha, points=[], runs=[], reproduction=[])
    keys = sorted(runs)
    for key in keys:
        for arm in ("item31", "zipper"):
            if arm not in runs[key]:
                raise Stop(f"cell {key}: no {arm} run")
            for r in runs[key][arm]["rows"]:
                res["runs"].append({k: v for k, v in r.items() if k not in ("theta", "noiseless_ce_pts")}
                                   | dict(L=key[0], teacher=key[1], arm=arm))
    loops = sorted({r["loop"] for k in keys for r in runs[k]["item31"]["rows"]})
    final = max(loops)
    for loop in loops:
        rows = []
        for key in keys:
            a = next(r for r in runs[key]["item31"]["rows"] if r["loop"] == loop)
            b = next(r for r in runs[key]["zipper"]["rows"] if r["loop"] == loop)
            d = a["noiseless_ce_pts"] - b["noiseless_ce_pts"]
            d = np.where(np.abs(d) < 1e-12, 0.0, d)
            z, p = signed_rank_z(d)
            rows.append(dict(teacher=key[1], mean_d=float(d.mean()), z=z, p=p,
                             item31=a["noiseless_ce"], zipper=b["noiseless_ce"]))
        for r, adj in zip(rows, holm([r["p"] for r in rows])):
            r["p_holm"], r["verdict"] = adj, verdict(adj, r["mean_d"], alpha)
        wins = sum(r["verdict"] == "WIN" for r in rows)
        res["points"].append(dict(loop=loop, teachers=rows, wins=wins, rule=loop == final,
                                  persists=(wins >= 2 and len(rows) == 3) if loop == final else None))
    if prev_dir:
        for key in keys:
            for arm, spec in (("item31", "psfai_template"), ("zipper", "psfai_template_zip")):
                f = os.path.join(prev_dir, f"L{key[0]}_t{key[1]}_s301-{spec}.json")
                if not os.path.exists(f):
                    res["reproduction"].append(dict(L=key[0], teacher=key[1], arm=arm, equal=None))
                    continue
                prev = np.asarray(json.load(open(f, encoding="utf-8"))["final_mean"])
                r2k = next((r for r in runs[key][arm]["rows"] if r["loop"] == 2000), None)
                eq = r2k is not None and np.array_equal(prev, r2k["theta"])
                diff = None if r2k is None else float(np.max(np.abs(prev - r2k["theta"])))
                res["reproduction"].append(dict(L=key[0], teacher=key[1], arm=arm, equal=bool(eq), max_abs_diff=diff))
    return res


def markdown(res):
    L = ["# Long training with checkpoints, zipper against item 31: score (report only)", "",
         f"Rule fixed before the run (zip_long_note.md): at the final point, noiseless test CE per point, Wilcoxon, "
         f"Holm over 3 teachers, alpha {res['alpha']}; the gain persists if the zipper WINs in at least 2 of 3. "
         "Other points: reported, no claim.", "",
         "## Noiseless test CE, item 31 / zipper, per point", "",
         "| loops | teacher | item 31 | zipper | mean gain of the zipper | Holm p | verdict |", "|---|---|---|---|---|---|---|"]
    for pt in res["points"]:
        for r in pt["teachers"]:
            L.append(f"| {pt['loop']}{' (rule)' if pt['rule'] else ''} | {r['teacher']} | {r['item31']:.4f} | "
                     f"{r['zipper']:.4f} | {r['mean_d']:+.4f} | {r['p_holm']:.2e} | {r['verdict']} |")
    fin = [p for p in res["points"] if p["rule"]][0]
    L += ["", f"**The rule, at {fin['loop']} loops:** the zipper WINs in {fin['wins']} of {len(fin['teachers'])} "
          f"teachers: the gain {'PERSISTS' if fin['persists'] else 'does not persist'}.", "",
          "## Per run and point", "",
          "| teacher | arm | loops | noiseless CE test / train | noiseless acc test / train | lam / delta | stand-in CE "
          "no shots raw / undamped | with shots | twin curve CE |", "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(res["runs"], key=lambda r: (r["teacher"], r["arm"], r["loop"])):
        tc = "-" if r["twin_curve_ce"] is None else f"{r['twin_curve_ce']:.4f}"
        L.append(f"| {r['teacher']} | {r['arm']} | {r['loop']} | {r['noiseless_ce']:.4f} / {r['noiseless_train_ce']:.4f}"
                 f" | {r['noiseless_acc']:.3f} / {r['noiseless_train_acc']:.3f} | {r['lam']:.3f} / {r['delta']:+.3f} | "
                 f"{r['standin_ce_raw_exact']:.4f} / {r['standin_ce_und_exact']:.4f} | {r['standin_ce_shots']:.4f} | {tc} |")
    if res["reproduction"]:
        L += ["", "## The 2,000-loop point against yesterday's depth sweep (same plan up to the loop count)", "",
              "| teacher | arm | equal bit for bit | max abs difference |", "|---|---|---|---|"]
        for r in res["reproduction"]:
            L.append(f"| {r['teacher']} | {r['arm']} | {r['equal']} | {r.get('max_abs_diff')} |")
    return "\n".join(L) + "\n"


def main(argv):
    try:
        argv = list(argv)
        js, alpha, prev = None, 0.01, None
        for flag in ("--json", "--alpha", "--prev"):
            if flag in argv:
                i = argv.index(flag)
                val = argv[i + 1]
                del argv[i:i + 2]
                if flag == "--json":
                    js = val
                elif flag == "--alpha":
                    alpha = float(val)
                else:
                    prev = val
        if len(argv) != 3:
            print(__doc__)
            return 1
        runs, und, out = argv
        for f in (out, js):
            if f and os.path.exists(f):
                raise Stop(f"{f} exists: an output is never overwritten")
        res = score(load(runs, und), alpha, prev)
        open(out, "w", encoding="utf-8").write(markdown(res))
        if js:
            def clean(o):
                if isinstance(o, dict):
                    return {k: clean(v) for k, v in o.items()}
                if isinstance(o, list):
                    return [clean(v) for v in o]
                if isinstance(o, (np.floating, np.integer)):
                    return o.item()
                if isinstance(o, np.bool_):
                    return bool(o)
                return o
            json.dump(clean(res), open(js, "w", encoding="utf-8"), indent=1)
        print(f"written {out}")
        return 0
    except (Stop, U.Stop) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
