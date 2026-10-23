"""Score of the data and gradient test (report only, rules fixed in prereg/drafts-2026-10-23/data_grad_note.md):

    python -m toqb.data_grad_score RUNS_DIR GRAD_DIR OUT.md [--json OUT.json] [--alpha 0.01]

RUNS_DIR: the 12 toqb.s2rc records of gpu/data_grad.sh (L 16; teachers 14, 15, 16; arms item 31 and zipper;
64 training points, with the 256-point task's test set, and 256); GRAD_DIR: the toqb.grad_agree outputs.

Main measure (owner, 2026-10-23): accuracy without any correction. Per test point, correct means the stand-in's exact
P(1) on the label's side (toqb.match_score.correct_points, no shots); the accuracy with the run's shots is reported.

Rules (exact McNemar on the paired test points, Holm over the 3 teachers, alpha 0.01; WIN = more points correct):
  A. per arm, 256 training points against 64: the data was the wall for that arm if 256 WINs in >= 2 of 3 teachers.
  B. at 256 training points, the zipper against item 31: the zipper's gain survives more data if it WINs in >= 2 of 3.
Reported without a claim: B at 64 points; CE (raw, exact and with shots); the noiseless test and train CE; the
gradient cosines (twin against noiseless, and twin against twin) at the start and at the end.
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

from toqb import s2r2 as S2
from toqb import undamp as U
from toqb.match_score import Stop, ce_points, correct_points, holm, mcnemar, verdict
from toqb.s2rc import _scores

ARMS = {"psfai:template": "item31", "psfai:template_zip": "zipper"}


def load(runs_dir, grad_dir):
    cells = {}
    for f in sorted(glob.glob(os.path.join(runs_dir, "*.json"))):
        name = os.path.basename(f)
        rec = json.load(open(f, encoding="utf-8"))
        if not rec.get("valid"):
            raise Stop(f"{name}: not a valid run ({rec.get('error')})")
        arm = ARMS.get(rec["arm"])
        if arm is None:
            raise Stop(f"{name}: unknown arm {rec['arm']}")
        task = rec["task"]
        Xtr, ytr, Xte, yte = S2.teacher_data2(task)
        y = np.asarray(rec["test_labels"])
        if not np.array_equal(y, np.asarray(yte)):
            raise Stop(f"{name}: test labels differ from the teacher's")
        p1 = np.asarray(rec["rehearsal"]["standin_p1"])
        th = np.asarray(rec["final_mean"])
        ce0, acc0 = _scores(U.ideal_z(th, Xte, task), y)
        ce0tr, acc0tr = _scores(U.ideal_z(th, Xtr, task), np.asarray(ytr))
        gf = os.path.join(grad_dir, name)
        grad = json.load(open(gf, encoding="utf-8"))["points"] if os.path.exists(gf) else None
        key = (int(task["teacher_seed"]), int(task["n_train"]))
        cells.setdefault(key, {})[arm] = dict(
            file=name, y=y, Xte=Xte, ok=correct_points(p1, y), ce_pts=ce_points(p1, y),
            acc=float(correct_points(p1, y).mean()), ce=float(ce_points(p1, y).mean()),
            acc_shots=rec["rehearsal"]["acc"], ce_shots=rec["rehearsal"]["ce"],
            noiseless_ce=float(ce0), noiseless_acc=float(acc0), noiseless_train_ce=float(ce0tr),
            noiseless_train_acc=float(acc0tr), grad=grad)
    return cells


def _compare(pairs, alpha):
    rows = []
    for t, x, yv in pairs:
        if not np.array_equal(x["Xte"], yv["Xte"]):
            raise Stop(f"teacher {t}: the two runs are not on the same test points")
        b, c, p = mcnemar(x["ok"], yv["ok"])
        rows.append(dict(teacher=t, acc_x=x["acc"], acc_y=yv["acc"], diff=x["acc"] - yv["acc"], b=b, c=c, p=p))
    for r, adj in zip(rows, holm([r["p"] for r in rows])):
        r["p_holm"], r["verdict"] = adj, verdict(adj, r["diff"], alpha)
    return rows


def score(cells, alpha=0.01):
    teachers = sorted({k[0] for k in cells})
    res = dict(alpha=alpha, A={}, B={}, runs=[])
    for (t, ntr), v in sorted(cells.items()):
        for arm, c in v.items():
            res["runs"].append(dict(teacher=t, n_train=ntr, arm=arm, acc=c["acc"], ce=c["ce"], acc_shots=c["acc_shots"],
                                    ce_shots=c["ce_shots"], noiseless_ce=c["noiseless_ce"],
                                    noiseless_train_ce=c["noiseless_train_ce"], noiseless_acc=c["noiseless_acc"],
                                    grad=c["grad"]))
    for arm in ("item31", "zipper"):
        rows = _compare([(t, cells[(t, 256)][arm], cells[(t, 64)][arm]) for t in teachers], alpha)
        w = sum(r["verdict"] == "WIN" for r in rows)
        res["A"][arm] = dict(rows=rows, wins=w, wall=w >= 2 and len(rows) == 3)
    for ntr in (256, 64):
        rows = _compare([(t, cells[(t, ntr)]["zipper"], cells[(t, ntr)]["item31"]) for t in teachers], alpha)
        w = sum(r["verdict"] == "WIN" for r in rows)
        res["B"][ntr] = dict(rows=rows, wins=w, rule=ntr == 256,
                             survives=(w >= 2 and len(rows) == 3) if ntr == 256 else None)
    return res


def markdown(res):
    L = ["# Data and gradient test: score (report only)", "",
         f"Rules fixed before the run (data_grad_note.md): accuracy without correction (stand-in exact P(1), no shots), "
         f"exact McNemar on paired test points, Holm over 3 teachers, alpha {res['alpha']}. Truth tier: stand-in.", ""]
    for arm, a in res["A"].items():
        L += [f"## A. {arm}: 256 training points against 64", "", "| teacher | acc 256 / 64 | McNemar b / c | Holm p | verdict |",
              "|---|---|---|---|---|"]
        for r in a["rows"]:
            L.append(f"| {r['teacher']} | {r['acc_x']:.3f} / {r['acc_y']:.3f} | {r['b']} / {r['c']} | {r['p_holm']:.2e} | "
                     f"{r['verdict']} |")
        L += ["", f"**{arm}: the data was the wall: {'YES' if a['wall'] else 'no'}** ({a['wins']} of 3).", ""]
    for ntr, b in res["B"].items():
        L += [f"## B. Zipper against item 31 at {ntr} training points{' (the rule)' if b['rule'] else ' (reported)'}", "",
              "| teacher | acc zipper / item 31 | McNemar b / c | Holm p | verdict |", "|---|---|---|---|---|"]
        for r in b["rows"]:
            L.append(f"| {r['teacher']} | {r['acc_x']:.3f} / {r['acc_y']:.3f} | {r['b']} / {r['c']} | {r['p_holm']:.2e} | "
                     f"{r['verdict']} |")
        if b["rule"]:
            L += ["", f"**The zipper's gain survives more data: {'YES' if b['survives'] else 'no'}** ({b['wins']} of 3)."]
        L.append("")
    L += ["## Per run", "", "| teacher | train points | arm | acc (no shots) / with shots | CE (no shots) / with shots | "
          "noiseless CE test / train | grad cos twin-noiseless start / end | twin-twin start / end | grad scale start / end |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(res["runs"], key=lambda r: (r["teacher"], r["n_train"], r["arm"])):
        g = r["grad"]
        if g:
            gc = f"{g[0]['cos_twin_ideal']:.3f} / {g[-1]['cos_twin_ideal']:.3f}"
            gt = f"{g[0]['cos_twin1_twin2']:.3f} / {g[-1]['cos_twin1_twin2']:.3f}"
            gs = f"{g[0]['scale']:.3f} / {g[-1]['scale']:.3f}"
        else:
            gc = gt = gs = "-"
        L.append(f"| {r['teacher']} | {r['n_train']} | {r['arm']} | {r['acc']:.3f} / {r['acc_shots']:.3f} | "
                 f"{r['ce']:.4f} / {r['ce_shots']:.4f} | {r['noiseless_ce']:.4f} / {r['noiseless_train_ce']:.4f} | "
                 f"{gc} | {gt} | {gs} |")
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
        runs, grad, out = argv
        for f in (out, js):
            if f and os.path.exists(f):
                raise Stop(f"{f} exists: an output is never overwritten")
        res = score(load(runs, grad), alpha)
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
