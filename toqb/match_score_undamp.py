"""Score of the undamped-readout match (W14 draft, 2026-10-21): design C's training (C0) on both compiler arms, each
answered raw and undamped (toqb.undamp), on fresh teachers and the W9 ladder.

    python -m toqb.match_score_undamp RUNS_DIR UNDAMP_DIR OUT.md [--json OUT.json] [--alpha 0.01]

RUNS_DIR holds the C0 run records (toqb.s2rc_ckpt; arms psfai:template and qiskit:2:target:template); UNDAMP_DIR the
matching toqb.undamp_run outputs (same file names). Per point, as W8: the stand-in's exact P(1) per test point gives
the per-point CE, raw (p = 1 - P(1)) or undamped (z_u = clip((1 - 2 P(1) - delta) / lam, -1, 1), p = (1 + z_u) / 2),
with toqb.s2r2's clip. Comparisons X against Y per task: Wilcoxon signed-rank on d = CE(Y) - CE(X), Holm over the
group's tasks, WIN / LOSS / TIE at alpha; per group (angle, L): Stouffer with Holm over groups (W11's rule).

Comparisons (W14 draft; the owner fixes which is the headline before any record is read):
  A. PSF undamped against PSF raw (does the readout help PSF?)
  B. PSF undamped against Qiskit raw (the new pipeline against the opponent as it stands)
  C. PSF undamped against Qiskit undamped (the same readout on both)
  D. Qiskit undamped against Qiskit raw (reported)
Also reported: accuracy (McNemar), the undamped prediction layer (stand-in undamped CE inside the undamped interval),
and (lam, delta) per run.
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys

import numpy as np

from toqb import undamp as U
from toqb.match_score import Stop, ce_points, correct_points, holm, mcnemar, signed_rank_z, verdict

ARMS = {"psfai:template": "PSF", "qiskit:2:target:template": "Qiskit"}
COMPARISONS = (("A", "PSF undamped", "PSF raw"), ("B", "PSF undamped", "Qiskit raw"),
               ("C", "PSF undamped", "Qiskit undamped"), ("D", "Qiskit undamped", "Qiskit raw"))


def load(runs_dir, und_dir):
    tasks = {}
    for f in sorted(glob.glob(os.path.join(runs_dir, "*.json"))):
        name = os.path.basename(f)
        rec = json.load(open(f, encoding="utf-8"))
        if not rec.get("valid") or "rehearsal" not in rec:
            raise Stop(f"{name}: not a valid run with a stand-in verification ({rec.get('error')})")
        if rec.get("kind") != "s2rc" or float(rec["train"].get("init", 1.0)) != 0.0:
            raise Stop(f"{name}: not a C0 run")
        arm = ARMS.get(rec["arm"])
        if arm is None:
            raise Stop(f"{name}: unknown arm {rec['arm']}")
        uf = os.path.join(und_dir, name)
        if not os.path.exists(uf):
            raise Stop(f"{name}: no undamp output in {und_dir}")
        und = json.load(open(uf, encoding="utf-8"))
        last = und["points"][-1]
        if not last["raw"]["reproduced"]:
            raise Stop(f"{name}: the undamp step did not reproduce the stand-in's shots")
        t = rec["task"]
        key = (int(t["teacher_seed"]), float(t["teacher_angle"]), int(t["layers"]))
        y = np.array(rec["test_labels"])
        p1 = np.asarray(rec["rehearsal"]["standin_p1"], float)
        zu = U.apply(1 - 2 * p1, last["lam"], last["delta"])
        slot = tasks.setdefault(key, {"y": y})
        if not np.array_equal(slot["y"], y):
            raise Stop(f"task {key}: arms scored on different test labels")
        for ro, pp in (("raw", p1), ("undamped", (1 - zu) / 2)):
            lab = f"{arm} {ro}"
            if lab in slot:
                raise Stop(f"task {key}: two {lab} runs")
            slot[lab] = dict(file=name, ce=ce_points(pp, y), ok=correct_points(pp, y),
                             lam=last["lam"], delta=last["delta"],
                             inside=last["undamped"]["inside"] if ro == "undamped" else last["raw"]["inside"])
    return tasks


def score(tasks, alpha=0.01):
    keys = sorted(tasks)
    groups = sorted({(k[1], k[2]) for k in keys})
    res = dict(alpha=alpha, comparisons={}, arms={})
    for key in keys:
        for lab, v in tasks[key].items():
            if lab == "y":
                continue
            res["arms"].setdefault(lab, []).append(dict(task=list(key), ce=float(v["ce"].mean()),
                                                        acc=float(v["ok"].mean()), lam=v["lam"], delta=v["delta"],
                                                        inside=v["inside"]))
    for cid, x, yl in COMPARISONS:
        rows = []
        for key in keys:
            s = tasks[key]
            if x not in s or yl not in s:
                continue
            d = s[yl]["ce"] - s[x]["ce"]
            d = np.where(np.abs(d) < 1e-12, 0.0, d)  # equal answers up to rounding count as ties (dropped)
            z, p = signed_rank_z(d)
            b, c, pm = mcnemar(s[x]["ok"], s[yl]["ok"])
            se = float(np.std(d, ddof=1) / math.sqrt(len(d)))
            rows.append(dict(task=list(key), mean_d=float(d.mean()), ci99=[float(d.mean() - 2.576 * se),
                             float(d.mean() + 2.576 * se)], z=z, p=p, acc_diff=float(s[x]["ok"].mean() - s[yl]["ok"].mean()),
                             mcnemar=[b, c], p_acc=pm))
        gres = []
        for g in groups:
            rs = [r for r in rows if (r["task"][1], r["task"][2]) == g]
            if not rs:
                continue
            adj = holm([r["p"] for r in rs])
            for r, a in zip(rs, adj):
                r["p_holm"], r["verdict"] = a, verdict(a, r["mean_d"], alpha)
            Z = float(sum(r["z"] for r in rs) / math.sqrt(len(rs)))
            from scipy.stats import norm
            gres.append(dict(group=list(g), Z=Z, p=float(2 * norm.sf(abs(Z))), tasks=len(rs),
                             task_verdicts=[r["verdict"] for r in rs]))
        adjg = holm([g["p"] for g in gres])
        for g, a in zip(gres, adjg):
            w, l = g["task_verdicts"].count("WIN"), g["task_verdicts"].count("LOSS")
            g["p_holm"] = a
            g["verdict"] = ("MIXED" if w and l else "WIN" if a < alpha and g["Z"] > 0 and not l
                            else "LOSS" if a < alpha and g["Z"] < 0 and not w else "TIE")
        res["comparisons"][cid] = dict(x=x, y=yl, tasks=rows, groups=gres)
    return res


def markdown(res):
    L = ["# The undamped-readout match: score", "",
         f"Rules: W14 draft (2026-10-21), alpha {res['alpha']}; W8's per-point statistics; groups (angle, L), Holm over "
         "groups. Truth tier: stand-in (simulation).", "", "## Per arm and readout (means over tasks)", "",
         "| arm, readout | tasks | CE | accuracy | lam / delta | undamped prediction inside |", "|---|---|---|---|---|---|"]
    for lab, v in sorted(res["arms"].items()):
        ins = sum(1 for r in v if r["inside"]) if "undamped" in lab else "-"
        L.append(f"| {lab} | {len(v)} | {np.mean([r['ce'] for r in v]):.4f} | {np.mean([r['acc'] for r in v]):.3f} | "
                 f"{np.mean([r['lam'] for r in v]):.3f} / {np.mean([r['delta'] for r in v]):+.3f} | {ins} |")
    for cid, c in res["comparisons"].items():
        L += ["", f"## {cid}. {c['x']} against {c['y']}", "", "| group (angle, L) | Stouffer Z | Holm p | verdict | tasks |",
              "|---|---|---|---|---|"]
        for g in c["groups"]:
            L.append(f"| {g['group'][0]}, L{g['group'][1]} | {g['Z']:+.2f} | {g['p_holm']:.2e} | {g['verdict']} | "
                     f"{', '.join(g['task_verdicts'])} |")
        L += ["", "| teacher | angle | L | mean CE gain (99 % CI) | Holm p | verdict | acc diff | McNemar b / c |",
              "|---|---|---|---|---|---|---|---|"]
        for r in c["tasks"]:
            L.append(f"| {r['task'][0]} | {r['task'][1]} | {r['task'][2]} | {r['mean_d']:+.4f} ({r['ci99'][0]:+.4f}, "
                     f"{r['ci99'][1]:+.4f}) | {r.get('p_holm', float('nan')):.2e} | {r.get('verdict', '-')} | "
                     f"{r['acc_diff']:+.3f} | {r['mcnemar'][0]} / {r['mcnemar'][1]} |")
    return "\n".join(L) + "\n"


def main(argv):
    try:
        js = None
        alpha = 0.01
        argv = list(argv)
        if "--json" in argv:
            i = argv.index("--json"); js = argv[i + 1]; del argv[i:i + 2]
        if "--alpha" in argv:
            i = argv.index("--alpha"); alpha = float(argv[i + 1]); del argv[i:i + 2]
        if len(argv) != 3:
            print(__doc__)
            return 1
        runs, und, out = argv
        for f in (out, js):
            if f and os.path.exists(f):
                raise Stop(f"{f} exists: an output is never overwritten")
        res = score(load(runs, und), alpha)
        open(out, "w", encoding="utf-8").write(markdown(res))
        if js:
            json.dump(res, open(js, "w", encoding="utf-8"), indent=1)
        print(f"written {out}")
        return 0
    except (Stop, U.Stop) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
