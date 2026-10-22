"""Score of the depth sweep, the zipper against item 31 (report only, declared in
prereg/drafts-2026-10-22/zip_depth_note.md before the run):

    python -m toqb.zip_depth_score RUNS_DIR UNDAMP_DIR OUT.md [--json OUT.json] [--alpha 0.01]

RUNS_DIR holds the toqb.s2rc records of gpu/zip_depth.sh (arms psfai:template = item 31 and psfai:template_zip =
zipper; L 8, 12, 16, 20; teachers 11, 12, 13; seed 301); UNDAMP_DIR the matching toqb.undamp_run --final-only outputs.

Per run: lam, delta (the twin on the 64 training inputs); the stand-in CE raw with shots (the record's), and, without
shots, from the stand-in's exact P(1) per test point: raw and undamped CE and accuracy; the trained model's own
noiseless CE and accuracy on the test points (exact, no noise).

The rule fixed before the run (the workplace's, owner 2026-10-22): per depth L and teacher, d_i = CE_i(item 31) -
CE_i(zipper) on the undamped stand-in's exact P(1) (positive favours the zipper); two-sided Wilcoxon signed-rank
(toqb.match_score), Holm over the depth's 3 teachers; WIN if the adjusted p < alpha and mean d > 0. The depth is
"widened" if, in at least 2 of the 3 teachers, the zipper WINs and its noiseless test CE is also lower than item 31's.

Reported, not tested: per arm and depth, the mean undamped CE (chance is ln 2 = 0.693) and lam; and the cost of the
undamped readout on a device: shots for the same shot noise as 250 raw shots, 250 / lam^2, and the QPU seconds of
500 test points at that count (toqb.s2rc_device.qpu_seconds) against 250 shots.
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
from toqb.match_score import Stop, ce_points, correct_points, holm, signed_rank_z, verdict
from toqb.s2rc import _scores

ARMS = {"psfai:template": "item31", "psfai:template_zip": "zipper"}
LN2 = math.log(2.0)


def load(runs_dir, und_dir):
    cells = {}
    for f in sorted(glob.glob(os.path.join(runs_dir, "*.json"))):
        name = os.path.basename(f)
        rec = json.load(open(f, encoding="utf-8"))
        if not rec.get("valid") or "rehearsal" not in rec:
            raise Stop(f"{name}: not a valid run with a stand-in verification ({rec.get('error')})")
        arm = ARMS.get(rec["arm"])
        if arm is None:
            raise Stop(f"{name}: unknown arm {rec['arm']}")
        uf = os.path.join(und_dir, name)
        if not os.path.exists(uf):
            raise Stop(f"{name}: no undamp output in {und_dir}")
        last = json.load(open(uf, encoding="utf-8"))["points"][-1]
        t = rec["task"]
        key = (int(t["layers"]), int(t["teacher_seed"]))
        y = np.array(rec["test_labels"])
        p1 = np.asarray(rec["rehearsal"]["standin_p1"], float)
        zu = U.apply(1 - 2 * p1, last["lam"], last["delta"])
        pu = (1 - zu) / 2
        _, _, Xte, yte = S2.teacher_data2(t)
        if not np.array_equal(np.asarray(yte), y):
            raise Stop(f"{name}: the test labels differ from the teacher's")
        zi = U.ideal_z(np.array(rec["final_mean"]), Xte, t)
        ce0, acc0 = _scores(zi, np.asarray(yte))
        slot = cells.setdefault(key, {"y": y})
        if not np.array_equal(slot["y"], y):
            raise Stop(f"cell {key}: arms scored on different test labels")
        if arm in slot:
            raise Stop(f"cell {key}: two {arm} runs")
        slot[arm] = dict(file=name, lam=float(last["lam"]), delta=float(last["delta"]),
                         reproduced=bool(last["raw"]["reproduced"]), ce_shots=float(rec["rehearsal"]["ce"]),
                         ce_raw=ce_points(p1, y), ok_raw=correct_points(p1, y),
                         ce_und=ce_points(pu, y), ok_und=correct_points(pu, y),
                         ce_noiseless=float(ce0), acc_noiseless=float(acc0))
    return cells


def score(cells, alpha=0.01):
    from toqb.s2rc_device import qpu_seconds
    depths = sorted({k[0] for k in cells})
    res = dict(alpha=alpha, depths=[], runs=[], cost=[])
    for key in sorted(cells):
        for arm in ("item31", "zipper"):
            v = cells[key].get(arm)
            if v is None:
                raise Stop(f"cell {key}: no {arm} run")
            res["runs"].append(dict(L=key[0], teacher=key[1], arm=arm, file=v["file"], lam=v["lam"], delta=v["delta"],
                                    reproduced=v["reproduced"], ce_shots=v["ce_shots"],
                                    ce_raw=float(v["ce_raw"].mean()), acc_raw=float(v["ok_raw"].mean()),
                                    ce_und=float(v["ce_und"].mean()), acc_und=float(v["ok_und"].mean()),
                                    ce_noiseless=v["ce_noiseless"], acc_noiseless=v["acc_noiseless"]))
    for L in depths:
        rows = []
        for key in sorted(k for k in cells if k[0] == L):
            a, b = cells[key]["item31"], cells[key]["zipper"]
            d = a["ce_und"] - b["ce_und"]
            d = np.where(np.abs(d) < 1e-12, 0.0, d)
            z, p = signed_rank_z(d)
            rows.append(dict(teacher=key[1], mean_d=float(d.mean()), z=z, p=p,
                             noiseless_item31=a["ce_noiseless"], noiseless_zipper=b["ce_noiseless"],
                             noiseless_same_order=b["ce_noiseless"] < a["ce_noiseless"]))
        for r, adj in zip(rows, holm([r["p"] for r in rows])):
            r["p_holm"], r["verdict"] = adj, verdict(adj, r["mean_d"], alpha)
            r["counts"] = r["verdict"] == "WIN" and r["noiseless_same_order"]
        n_ok = sum(r["counts"] for r in rows)
        res["depths"].append(dict(L=L, teachers=rows, counted=n_ok, widened=n_ok >= 2 and len(rows) == 3))
        for arm in ("item31", "zipper"):
            rs = [r for r in res["runs"] if r["L"] == L and r["arm"] == arm]
            lam = float(np.mean([r["lam"] for r in rs]))
            shots = int(math.ceil(250 / lam ** 2)) if lam > 0 else None
            res["cost"].append(dict(L=L, arm=arm, lam=lam, ce_und=float(np.mean([r["ce_und"] for r in rs])),
                                    ce_raw=float(np.mean([r["ce_raw"] for r in rs])),
                                    ce_noiseless=float(np.mean([r["ce_noiseless"] for r in rs])),
                                    at_chance=float(np.mean([r["ce_und"] for r in rs])) >= LN2 - 0.01,
                                    shots_equiv=shots, qpu_s_500=(qpu_seconds(500, shots) if shots else None),
                                    qpu_s_500_raw=qpu_seconds(500, 250)))
    return res


def markdown(res):
    L = ["# Depth sweep, zipper against item 31: score (report only)", "",
         f"Rule fixed before the run (zip_depth_note.md): per depth, Wilcoxon on the undamped stand-in's exact P(1), "
         f"Holm over 3 teachers, alpha {res['alpha']}; widened if the zipper WINs with a lower noiseless CE in at least "
         "2 of 3 teachers. Truth tier: stand-in (simulation).", "",
         "## Per depth", "", "| L | teacher | mean CE gain of the zipper | Holm p | verdict | noiseless CE item 31 / zipper "
         "| counted |", "|---|---|---|---|---|---|---|"]
    for dp in res["depths"]:
        for r in dp["teachers"]:
            L.append(f"| {dp['L']} | {r['teacher']} | {r['mean_d']:+.4f} | {r['p_holm']:.2e} | {r['verdict']} | "
                     f"{r['noiseless_item31']:.4f} / {r['noiseless_zipper']:.4f} | {'yes' if r['counts'] else 'no'} |")
    L += ["", "| L | teachers counted | widened |", "|---|---|---|"]
    for dp in res["depths"]:
        L.append(f"| {dp['L']} | {dp['counted']} of {len(dp['teachers'])} | {'YES' if dp['widened'] else 'no'} |")
    L += ["", "## Per arm and depth (means over teachers; chance CE = 0.693)", "",
          "| L | arm | lam | CE raw (exact) | CE undamped (exact) | at chance | noiseless CE | shots for 250-shot noise "
          "| QPU s, 500 points: undamped / raw |", "|---|---|---|---|---|---|---|---|---|"]
    for c in res["cost"]:
        L.append(f"| {c['L']} | {c['arm']} | {c['lam']:.3f} | {c['ce_raw']:.4f} | {c['ce_und']:.4f} | "
                 f"{'yes' if c['at_chance'] else 'no'} | {c['ce_noiseless']:.4f} | {c['shots_equiv']} | "
                 f"{c['qpu_s_500']:.0f} / {c['qpu_s_500_raw']:.0f} |")
    L += ["", "## Per run", "", "| L | teacher | arm | lam / delta | CE with shots | CE raw / undamped (exact) | "
          "acc raw / undamped | noiseless CE / acc | shots reproduced |", "|---|---|---|---|---|---|---|---|---|"]
    for r in res["runs"]:
        L.append(f"| {r['L']} | {r['teacher']} | {r['arm']} | {r['lam']:.3f} / {r['delta']:+.3f} | {r['ce_shots']:.4f} | "
                 f"{r['ce_raw']:.4f} / {r['ce_und']:.4f} | {r['acc_raw']:.3f} / {r['acc_und']:.3f} | "
                 f"{r['ce_noiseless']:.4f} / {r['acc_noiseless']:.3f} | {r['reproduced']} |")
    return "\n".join(L) + "\n"


def main(argv):
    try:
        js, alpha = None, 0.01
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
