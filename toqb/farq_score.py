"""Score of the zipper-against-Qiskit far-teacher test (rules fixed before the run in
prereg/drafts-2026-10-23/far_qiskit_note.md):

    python -m toqb.farq_score Q_RUNS Q_THETA0 Z_RUNS Z_THETA0 OUT.md [--json OUT.json] [--alpha 0.01]

Q_*: the Qiskit arm's toqb.s2rc_ckpt records and toqb.theta0_eval outputs (gpu/far_qiskit.sh); Z_*: the zipper's, from
the far-teacher test (results/far-teacher-2026-10-23; the same plans, L 16, teachers 17, 18, 19 at angle 1.0, 2,000
loops with a checkpoint at 500). Item 31's records there are not read.

Rule A (at 500 and at 2,000 loops): accuracy without correction, shot-free (the stand-in's exact P(1) on the label's
side); per teacher the zipper against Qiskit, exact McNemar on the 500 paired test points; Holm over the 6 comparisons,
alpha 0.01. At a point, an arm is the more accurate if it WINs in at least 2 of 3 teachers.
Rule B (the same points): the trained model itself, noiseless (its exact <Z> on the label's side: read without the
circuit's readout offset; owner, 2026-10-23); the same McNemar, Holm over 6, 2 of 3.
Reported: accuracy with the run's shots, the share of +1 answers, the stand-in and noiseless AUC, all at theta = 0, 500
and 2,000 loops; and a decision aid for a device run (owner, 2026-10-23: a device declaration only if the power at
300 points is at least 0.8 in 2 of 3 teachers at one loop count): the power of one exact McNemar at alpha 0.01
with 300 (and 500) test points drawn from the 500 and each arm's answer from 250 shots of the stand-in's P(1).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

from toqb import far_score as F
from toqb import undamp as U
from toqb.match_score import Stop, holm, mcnemar, verdict

Q_ARMS = {"qiskit:2:target:template": "qiskit"}
Z_ARMS = {"psfai:template_zip": "zipper", "psfai:template": None}
POINTS = F.POINTS
POWER_N = (300, 500)
POWER_REPS = 2000
POWER_SHOTS = 250
POWER_SEED = 20261024


def load(q_runs, q_t0, z_runs, z_t0):
    q = F.load(q_runs, q_t0, Q_ARMS)
    z = F.load(z_runs, z_t0, {k: v or "item31" for k, v in Z_ARMS.items()})
    if sorted(q) != sorted(z):
        raise Stop(f"teachers differ: Qiskit {sorted(q)}, zipper {sorted(z)}")
    for t in q:
        if not np.array_equal(q[t]["qiskit"]["y"], z[t]["zipper"]["y"]):
            raise Stop(f"teacher {t}: the test labels differ between the Qiskit and the zipper records")
    return {t: dict(qiskit=q[t]["qiskit"], zipper=z[t]["zipper"]) for t in sorted(q)}


def _shot_correct(rng, p1, y):
    ph = rng.binomial(POWER_SHOTS, p1) / POWER_SHOTS
    return np.where(y > 0, ph < 0.5, ph > 0.5)


def power(p1_z, p1_q, y, n, alpha, seed):
    """Share of simulated device runs (n of the test points, 250 shots each arm) in which the exact McNemar is below
    alpha with the stand-in's own direction (shot-free); the stand-in direction itself in `sign`."""
    p1_z, p1_q, y = np.asarray(p1_z, float), np.asarray(p1_q, float), np.asarray(y)
    sign = np.sign(F.correct_points(p1_z, y).mean() - F.correct_points(p1_q, y).mean())
    rng = np.random.default_rng(seed)
    hit = 0
    for _ in range(POWER_REPS):
        i = rng.choice(len(y), n, replace=False)
        b, c, p = mcnemar(_shot_correct(rng, p1_z[i], y[i]), _shot_correct(rng, p1_q[i], y[i]))
        hit += int(p < alpha and np.sign(b - c) == sign and sign != 0)
    return hit / POWER_REPS, int(sign)


def score(cells, alpha=0.01):
    teachers = sorted(cells)
    res = dict(alpha=alpha, A=[], B=[], runs=[], power=[])
    for t in teachers:
        for arm in ("zipper", "qiskit"):
            for loop, r in sorted(cells[t][arm]["rows"].items()):
                res["runs"].append({k: v for k, v in r.items() if k not in F.PER_POINT}
                                   | dict(teacher=t, arm=arm, loop=loop, q2=cells[t][arm]["q2"],
                                          durations_us=cells[t][arm]["durations_us"]))
    for rule, key, acc in (("A", "ok", "acc"), ("B", "ok_nl", "noiseless_acc")):
        rows = []
        for loop in POINTS:
            for t in teachers:
                z, q = cells[t]["zipper"]["rows"][loop], cells[t]["qiskit"]["rows"][loop]
                b, c, p = mcnemar(z[key], q[key])
                rows.append(dict(loop=loop, teacher=t, zipper=z[acc], qiskit=q[acc], diff=z[acc] - q[acc], b=b, c=c,
                                 p=p))
        for r, adj in zip(rows, holm([r["p"] for r in rows])):
            r["p_holm"], r["verdict"] = adj, verdict(adj, r["diff"], alpha)
        for loop in POINTS:
            sub = [r for r in rows if r["loop"] == loop]
            w, l_ = sum(r["verdict"] == "WIN" for r in sub), sum(r["verdict"] == "LOSS" for r in sub)
            res[rule].append(dict(loop=loop, wins=w, losses=l_, zipper=w >= 2, qiskit=l_ >= 2, rows=sub))
    for loop in POINTS:
        for t in teachers:
            z, q = cells[t]["zipper"]["rows"][loop], cells[t]["qiskit"]["rows"][loop]
            y = cells[t]["zipper"]["y"]
            row = dict(loop=loop, teacher=t)
            for n in POWER_N:
                row[f"power_{n}"], row["sign"] = power(z["p1"], q["p1"], y, n, alpha, POWER_SEED + 10 * t + loop)
            res["power"].append(row)
    return res


def markdown(res):
    L = ["# Far teachers, zipper against Qiskit: score (report only)", "",
         f"Rules fixed before the run (far_qiskit_note.md): A shot-free stand-in accuracy without correction; B the "
         f"trained model noiseless; McNemar, Holm over 6 per rule, alpha {res['alpha']}; 2 of 3 teachers.",
         "Truth tier: stand-in (A), the model itself (B).", ""]
    for rule, title in (("A", "stand-in accuracy, shot-free"), ("B", "noiseless accuracy of the trained model")):
        for a in res[rule]:
            L += [f"## {rule}. {title} at {a['loop']} loops: zipper / Qiskit", "",
                  "| teacher | zipper / Qiskit | McNemar b / c | Holm p | verdict (zipper) |", "|---|---|---|---|---|"]
            L += [f"| {r['teacher']} | {r['zipper']:.3f} / {r['qiskit']:.3f} | {r['b']} / {r['c']} | {r['p_holm']:.2e} "
                  f"| {r['verdict']} |" for r in a["rows"]]
            who = "the zipper" if a["zipper"] else "Qiskit" if a["qiskit"] else "neither"
            L += ["", f"**More accurate at {a['loop']} loops ({rule}): {who}** (zipper WIN {a['wins']}, LOSS "
                  f"{a['losses']} of 3).", ""]
    L += ["## Decision aid for a device run (report only)", "",
          f"Power of one exact McNemar at alpha {res['alpha']} in the stand-in's direction; test points drawn from the "
          f"500, {POWER_SHOTS} shots per point and arm, {POWER_REPS} repetitions. The device is not the stand-in.", "",
          "| loops | teacher | stand-in direction | power, 300 points | power, 500 points |", "|---|---|---|---|---|"]
    L += [f"| {r['loop']} | {r['teacher']} | {'zipper' if r['sign'] > 0 else 'Qiskit' if r['sign'] < 0 else 'none'} | "
          f"{r['power_300']:.2f} | {r['power_500']:.2f} |" for r in res["power"]]
    L += ["", "## Per run and point", "",
          "| teacher | arm | loops | acc no shots / with shots | +1 share | stand-in AUC | noiseless acc / AUC / CE | "
          "twin-stand-in P(1) rmse |", "|---|---|---|---|---|---|---|---|"]
    for r in sorted(res["runs"], key=lambda r: (r["teacher"], r["arm"], r["loop"])):
        rm = r.get("twin_standin_rmse")
        L.append(f"| {r['teacher']} | {r['arm']} | {r['loop']} | {r['acc']:.3f} / {r['acc_shots']:.3f} | "
                 f"{r['plus_share']:.2f} | {r['auc_standin']:.3f} | {r['noiseless_acc']:.3f} / {r['auc_noiseless']:.3f} / "
                 f"{r['noiseless_ce']:.4f} | {'-' if rm is None else f'{rm:.4f}'} |")
    L += ["", "Circuits (per arm, from the records): " + "; ".join(
        sorted({f"{r['arm']}: q2 {r['q2']}, durations {r['durations_us']}" for r in res["runs"] if r["teacher"] ==
                min(x["teacher"] for x in res["runs"]) and r["loop"] == 0}))]
    return "\n".join(L) + "\n"


def main(argv):
    try:
        argv = list(argv)
        js, alpha = None, 0.01
        if "--json" in argv:
            i = argv.index("--json"); js = argv[i + 1]; del argv[i:i + 2]
        if "--alpha" in argv:
            i = argv.index("--alpha"); alpha = float(argv[i + 1]); del argv[i:i + 2]
        if len(argv) != 5:
            print(__doc__)
            return 1
        *dirs, out = argv
        for f in (out, js):
            if f and os.path.exists(f):
                raise Stop(f"{f} exists: an output is never overwritten")
        res = score(load(*dirs), alpha)
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
