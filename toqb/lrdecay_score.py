"""Score of flow B3 (rule fixed before the run in prereg/drafts-2026-10-24/flow_b_note.md): does a decaying step
stop long training from drifting?

    python -m toqb.lrdecay_score RUNS_DIR OUT.md [--json OUT.json] [--alpha 0.01]

RUNS_DIR: toqb.s2rc_ckpt records of gpu/flow_b.sh (part b3): per teacher one run with the constant step (file name
ending -const.json) and one with the decaying step (-decay.json), the same plan otherwise.

Rule: at the final loop, per teacher, the trained model's noiseless accuracy (sign of the exact <Z> on the label's
side), decaying against constant: exact McNemar on the paired test points; Holm over the teachers; alpha 0.01. The
decaying step is the better if it WINs in at least 2 of 3 teachers.
Reported: the same at every checkpoint; per schedule the change from its best checkpoint (by the same noiseless
accuracy) to the final loop; stand-in accuracy shot-free and with the run's shots; the share of +1 answers.
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

from toqb import s2r2 as S2
from toqb import undamp as U
from toqb.match_score import Stop, correct_points, holm, mcnemar, verdict

_DATA = {}


def load(runs_dir):
    cells = {}
    for f in sorted(glob.glob(os.path.join(runs_dir, "*.json"))):
        name = os.path.basename(f)
        sched = "decay" if name.endswith("-decay.json") else "const" if name.endswith("-const.json") else None
        if sched is None:
            raise Stop(f"{name}: neither -const nor -decay")
        rec = json.load(open(f, encoding="utf-8"))
        if not rec.get("valid"):
            raise Stop(f"{name}: not a valid run ({rec.get('error')})")
        task = rec["task"]
        key = json.dumps(task, sort_keys=True)
        if key not in _DATA:
            _DATA[key] = S2.teacher_data2(task)
        _, _, Xte, yte = _DATA[key]
        y = np.asarray(rec["test_labels"])
        if not np.array_equal(y, np.asarray(yte)):
            raise Stop(f"{name}: test labels differ")
        pts = {c["loop"]: (np.asarray(c["theta"]), c["rehearsal"]) for c in rec["checkpoints"]}
        pts[rec["loops"]] = (np.asarray(rec["final_mean"]), rec["rehearsal"])
        rows = {}
        for loop, (th, rh) in pts.items():
            zi = U.ideal_z(th, Xte, task)
            p1 = np.asarray(rh["standin_p1"])
            rows[loop] = dict(ok_nl=np.sign(zi) == y, noiseless_acc=float(np.mean(np.sign(zi) == y)),
                              acc=float(correct_points(p1, y).mean()), acc_shots=rh["acc"],
                              plus_share=float(np.mean(p1 < 0.5)))
        cells.setdefault(int(task["teacher_seed"]), {})[sched] = dict(file=name, rows=rows, loops=rec["loops"])
    return cells


def score(cells, alpha=0.01):
    teachers = sorted(cells)
    for t in teachers:
        if set(cells[t]) != {"const", "decay"}:
            raise Stop(f"teacher {t}: needs one -const and one -decay run")
    final = cells[teachers[0]]["const"]["loops"]
    loops = sorted(cells[teachers[0]]["const"]["rows"])
    rows = []
    for loop in loops:
        for t in teachers:
            d, c = cells[t]["decay"]["rows"][loop], cells[t]["const"]["rows"][loop]
            b, cc, p = mcnemar(d["ok_nl"], c["ok_nl"])
            rows.append(dict(loop=loop, teacher=t, decay=d["noiseless_acc"], const=c["noiseless_acc"],
                             diff=d["noiseless_acc"] - c["noiseless_acc"], b=b, c=cc, p=p))
    rule = [r for r in rows if r["loop"] == final]
    for r, adj in zip(rule, holm([r["p"] for r in rule])):
        r["p_holm"], r["verdict"] = adj, verdict(adj, r["diff"], alpha)
    wins = sum(r["verdict"] == "WIN" for r in rule)
    losses = sum(r["verdict"] == "LOSS" for r in rule)
    drift = []
    for t in teachers:
        for s in ("const", "decay"):
            rr = cells[t][s]["rows"]
            best = max(rr, key=lambda k: rr[k]["noiseless_acc"])
            drift.append(dict(teacher=t, schedule=s, best_loop=best, best=rr[best]["noiseless_acc"],
                              final=rr[final]["noiseless_acc"], change=rr[final]["noiseless_acc"] - rr[best]["noiseless_acc"]))
    runs = [{k: v for k, v in r.items() if k != "ok_nl"} | dict(teacher=t, schedule=s, loop=L)
            for t in teachers for s in ("const", "decay") for L, r in sorted(cells[t][s]["rows"].items())]
    return dict(alpha=alpha, final=final, rule=rule, wins=wins, losses=losses, holds=wins >= 2,
                reverse=losses >= 2, all=rows, drift=drift, runs=runs)


def markdown(res):
    L = ["# Flow B3: decaying against constant step (report only)", "",
         f"Rule fixed before the run (flow_b_note.md): at {res['final']} loops, the trained model's noiseless accuracy, "
         f"exact McNemar, Holm over the teachers, alpha {res['alpha']}; 2 of 3.", "",
         "| teacher | decaying / constant | McNemar b / c | Holm p | verdict (decaying) |", "|---|---|---|---|---|"]
    L += [f"| {r['teacher']} | {r['decay']:.3f} / {r['const']:.3f} | {r['b']} / {r['c']} | {r['p_holm']:.2e} | "
          f"{r['verdict']} |" for r in res["rule"]]
    who = "YES" if res["holds"] else ("no; the constant step is the better" if res["reverse"] else "no")
    L += ["", f"**The decaying step is the better at {res['final']} loops: {who}** (WIN {res['wins']}, LOSS "
          f"{res['losses']} of {len(res['rule'])}).", "", "## Every checkpoint (reported)", "",
          "| loops | teacher | decaying / constant | b / c | p (unadjusted) |", "|---|---|---|---|---|"]
    L += [f"| {r['loop']} | {r['teacher']} | {r['decay']:.3f} / {r['const']:.3f} | {r['b']} / {r['c']} | {r['p']:.2e} |"
          for r in res["all"]]
    L += ["", "## Drift: from the best checkpoint to the end (reported)", "",
          "| teacher | schedule | best at | best | final | change |", "|---|---|---|---|---|---|"]
    L += [f"| {d['teacher']} | {d['schedule']} | {d['best_loop']} | {d['best']:.3f} | {d['final']:.3f} | "
          f"{d['change']:+.3f} |" for d in res["drift"]]
    L += ["", "## Per run and point", "", "| teacher | schedule | loops | noiseless acc | stand-in acc no shots / shots "
          "| +1 share |", "|---|---|---|---|---|---|"]
    L += [f"| {r['teacher']} | {r['schedule']} | {r['loop']} | {r['noiseless_acc']:.3f} | {r['acc']:.3f} / "
          f"{r['acc_shots']:.3f} | {r['plus_share']:.2f} |" for r in res["runs"]]
    return "\n".join(L) + "\n"


def main(argv):
    try:
        argv = list(argv)
        js, alpha = None, 0.01
        if "--json" in argv:
            i = argv.index("--json"); js = argv[i + 1]; del argv[i:i + 2]
        if "--alpha" in argv:
            i = argv.index("--alpha"); alpha = float(argv[i + 1]); del argv[i:i + 2]
        if len(argv) != 2:
            print(__doc__)
            return 1
        runs, out = argv
        for f in (out, js):
            if f and os.path.exists(f):
                raise Stop(f"{f} exists: an output is never overwritten")
        res = score(load(runs), alpha)
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
