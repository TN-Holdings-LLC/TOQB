"""Score of the far-teacher test (rules fixed before the run in prereg/drafts-2026-10-23/far_teacher_note.md):

    python -m toqb.far_score RUNS_DIR THETA0_DIR OUT.md [--json OUT.json] [--alpha 0.01]

RUNS_DIR: the toqb.s2rc_ckpt records of gpu/far_teacher.sh (L 16, teachers 17, 18, 19 at angle 1.0, arms item 31 and
zipper, 2,000 loops with a checkpoint at 500); THETA0_DIR: the toqb.theta0_eval outputs (theta = 0, same plans).

Main measure (owner, 2026-10-23): accuracy without correction, shot-free: a test point is correct when the stand-in's
exact P(1) is on the label's side (toqb.match_score.correct_points).

Rule A (at 500 and at 2,000 loops): per teacher, the zipper against item 31, exact McNemar on the 500 paired test
points; Holm over the 6 comparisons (2 points x 3 teachers), alpha 0.01; WIN = more points correct. At a point, the
zipper is more accurate if it WINs in at least 2 of 3 teachers.
Rule B (the same points): what training added. Per test point, g = correct(trained) - correct(theta = 0) for each arm
(-1, 0 or 1), d = g(zipper) - g(item 31); two-sided Wilcoxon signed-rank on d (zeros dropped); Holm over the 6; WIN if
the adjusted p < alpha and mean d > 0. At a point, the zipper learned more if it WINs in at least 2 of 3 teachers.
Reported: accuracy with the run's shots; the stand-in AUC (offset- and scale-free) and the noiseless AUC, accuracy and
CE; the same at theta = 0.
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np
from scipy.stats import rankdata

from toqb import s2r2 as S2
from toqb import undamp as U
from toqb.match_score import Stop, correct_points, holm, mcnemar, signed_rank_z, verdict
from toqb.s2rc import _scores

ARMS = {"psfai:template": "item31", "psfai:template_zip": "zipper"}
POINTS = (500, 2000)
_DATA = {}


def auc(s, y):
    s, y = np.asarray(s, float), np.asarray(y)
    r = rankdata(s)
    pos = y > 0
    n1, n0 = int(pos.sum()), int((~pos).sum())
    return float((r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def load(runs_dir, t0_dir):
    cells = {}
    for f in sorted(glob.glob(os.path.join(runs_dir, "*.json"))):
        name = os.path.basename(f)
        rec = json.load(open(f, encoding="utf-8"))
        if not rec.get("valid"):
            raise Stop(f"{name}: not a valid run ({rec.get('error')})")
        arm = ARMS.get(rec["arm"])
        if arm is None:
            raise Stop(f"{name}: unknown arm {rec['arm']}")
        t0f = os.path.join(t0_dir, name)
        if not os.path.exists(t0f):
            raise Stop(f"{name}: no theta = 0 output")
        t0 = json.load(open(t0f, encoding="utf-8"))
        task = rec["task"]
        key = json.dumps(task, sort_keys=True)
        if key not in _DATA:  # one teacher's data serves both arms (it takes minutes at angle 1.0)
            _DATA[key] = S2.teacher_data2(task)
        _, _, Xte, yte = _DATA[key]
        y = np.asarray(rec["test_labels"])
        if not (np.array_equal(y, np.asarray(yte)) and t0["test_labels"] == rec["test_labels"]):
            raise Stop(f"{name}: test labels differ")
        pts = {c["loop"]: (np.asarray(c["theta"]), c["rehearsal"]) for c in rec["checkpoints"]}
        pts[rec["loops"]] = (np.asarray(rec["final_mean"]), rec["rehearsal"])
        pts[0] = (np.zeros(len(rec["final_mean"])), t0["rehearsal"])
        rows = {}
        for loop, (theta, rh) in pts.items():
            p1 = np.asarray(rh["standin_p1"])
            zi = U.ideal_z(theta, Xte, task)
            ce0, acc0 = _scores(zi, y)
            rows[loop] = dict(ok=correct_points(p1, y), acc=float(correct_points(p1, y).mean()), acc_shots=rh["acc"],
                              auc_standin=auc(1 - 2 * p1, y), auc_noiseless=auc(zi, y), noiseless_acc=float(acc0),
                              noiseless_ce=float(ce0), plus_share=float(np.mean(p1 < 0.5)))
        cells.setdefault(int(task["teacher_seed"]), {})[arm] = dict(file=name, rows=rows)
    return cells


def score(cells, alpha=0.01):
    teachers = sorted(cells)
    res = dict(alpha=alpha, A=[], B=[], runs=[])
    for t in teachers:
        for arm in ("item31", "zipper"):
            if arm not in cells[t]:
                raise Stop(f"teacher {t}: no {arm} run")
            for loop, r in sorted(cells[t][arm]["rows"].items()):
                res["runs"].append({k: v for k, v in r.items() if k != "ok"} | dict(teacher=t, arm=arm, loop=loop))
    a_rows, b_rows = [], []
    for loop in POINTS:
        for t in teachers:
            z, q = cells[t]["zipper"]["rows"], cells[t]["item31"]["rows"]
            b, c, p = mcnemar(z[loop]["ok"], q[loop]["ok"])
            a_rows.append(dict(loop=loop, teacher=t, zipper=z[loop]["acc"], item31=q[loop]["acc"],
                               diff=z[loop]["acc"] - q[loop]["acc"], b=b, c=c, p=p))
            d = (z[loop]["ok"].astype(int) - z[0]["ok"].astype(int)) - (q[loop]["ok"].astype(int) - q[0]["ok"].astype(int))
            zs, pw = signed_rank_z(d.astype(float))
            b_rows.append(dict(loop=loop, teacher=t, gain_zipper=z[loop]["acc"] - z[0]["acc"],
                               gain_item31=q[loop]["acc"] - q[0]["acc"], mean_d=float(d.mean()), z=zs, p=pw))
    for rows, key in ((a_rows, "diff"), (b_rows, "mean_d")):
        for r, adj in zip(rows, holm([r["p"] for r in rows])):
            r["p_holm"], r["verdict"] = adj, verdict(adj, r[key], alpha)
    for loop in POINTS:
        wa = sum(r["verdict"] == "WIN" for r in a_rows if r["loop"] == loop)
        wb = sum(r["verdict"] == "WIN" for r in b_rows if r["loop"] == loop)
        res["A"].append(dict(loop=loop, wins=wa, holds=wa >= 2 and len(teachers) == 3,
                             rows=[r for r in a_rows if r["loop"] == loop]))
        res["B"].append(dict(loop=loop, wins=wb, holds=wb >= 2 and len(teachers) == 3,
                             rows=[r for r in b_rows if r["loop"] == loop]))
    return res


def markdown(res):
    L = ["# Far-teacher test: score (report only)", "",
         f"Rules fixed before the run (far_teacher_note.md): shot-free accuracy without correction; A: zipper against item "
         f"31 (McNemar); B: what training added (Wilcoxon on per-point gains); Holm over 6 per rule, alpha {res['alpha']}.",
         "Truth tier: stand-in.", ""]
    for a in res["A"]:
        L += [f"## A. Accuracy at {a['loop']} loops: zipper / item 31", "",
              "| teacher | zipper / item 31 | McNemar b / c | Holm p | verdict |", "|---|---|---|---|---|"]
        L += [f"| {r['teacher']} | {r['zipper']:.3f} / {r['item31']:.3f} | {r['b']} / {r['c']} | {r['p_holm']:.2e} | "
              f"{r['verdict']} |" for r in a["rows"]]
        L += ["", f"**The zipper is more accurate at {a['loop']} loops: {'YES' if a['holds'] else 'no'}** ({a['wins']} of 3).", ""]
    for b in res["B"]:
        L += [f"## B. What training added, theta = 0 to {b['loop']} loops", "",
              "| teacher | gain zipper / item 31 | mean per-point difference | Holm p | verdict |", "|---|---|---|---|---|"]
        L += [f"| {r['teacher']} | {r['gain_zipper']:+.3f} / {r['gain_item31']:+.3f} | {r['mean_d']:+.4f} | "
              f"{r['p_holm']:.2e} | {r['verdict']} |" for r in b["rows"]]
        L += ["", f"**The zipper learned more by {b['loop']} loops: {'YES' if b['holds'] else 'no'}** ({b['wins']} of 3).", ""]
    L += ["## Per run and point", "",
          "| teacher | arm | loops | acc no shots / with shots | +1 share | stand-in AUC | noiseless acc / AUC / CE |",
          "|---|---|---|---|---|---|---|"]
    for r in sorted(res["runs"], key=lambda r: (r["teacher"], r["arm"], r["loop"])):
        L.append(f"| {r['teacher']} | {r['arm']} | {r['loop']} | {r['acc']:.3f} / {r['acc_shots']:.3f} | "
                 f"{r['plus_share']:.2f} | {r['auc_standin']:.3f} | {r['noiseless_acc']:.3f} / {r['auc_noiseless']:.3f} / "
                 f"{r['noiseless_ce']:.4f} |")
    return "\n".join(L) + "\n"


def main(argv):
    try:
        argv = list(argv)
        js, alpha = None, 0.01
        if "--json" in argv:
            i = argv.index("--json"); js = argv[i + 1]; del argv[i:i + 2]
        if "--alpha" in argv:
            i = argv.index("--alpha"); alpha = float(argv[i + 1]); del argv[i:i + 2]
        if len(argv) != 3:
            print(__doc__)
            return 1
        runs, t0, out = argv
        for f in (out, js):
            if f and os.path.exists(f):
                raise Stop(f"{f} exists: an output is never overwritten")
        res = score(load(runs, t0), alpha)
        open(out, "w", encoding="utf-8").write(markdown(res))
        if js:
            json.dump(res, open(js, "w", encoding="utf-8"), indent=1, default=float)
        print(f"written {out}")
        return 0
    except (Stop, U.Stop) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
