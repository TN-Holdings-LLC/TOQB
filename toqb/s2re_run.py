"""Design E on the twin (exploratory, 2026-10-20): the same task, arms, prediction and stand-in verification as
`toqb.s2rc` (design C), with C's training loop replaced by design E's formula (`toqb.s2re`): the twin's <Z0> and its
exact parameter-shift tangent at theta0 for every training point, then theta* = theta0 + pinv(G) (y tau - f0).
No random directions, no learning rate, no loop over steps; the only randomness is the twin's own trajectories.

    python -m toqb.s2re_run PLAN.json OUT.json SPEC        (from the TOQB root; TOQB_XP=cupy for the GPU)

The plan is a design C plan; its "train" block needs "feat_traj" (trajectories per tangent evaluation) and may give
"theta0": "zero" (default). The record has kind "s2re" and the same prediction and rehearsal fields as s2rc's, so
`gpu/` summaries and `toqb.predscore` read it unchanged. `toqb.s2rc` itself is not changed (design C's code stays as
rehearsed).
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np

from toqb import s2r as S
from toqb import s2r2 as S2
from toqb import s2re as E
from toqb import task_loop as TL
from toqb.s2rc import _SkipVerify, _scores, predict_job


def run_s2re(plan, spec, keep=None):
    task, p, pr = plan["task"], plan["train"], plan["predict"]
    R = S2.Runner(plan, spec)
    rec = dict(kind="s2re", arm=spec, seed=p.get("seed"), plan=plan["name"], started=S._cest(), train=p, predict=pr,
               version=R.arm.version(), standin=R.standin.params, engine=R.eng.xp.__name__, dtype=str(R.eng.dtype),
               device=plan["device"], task=task, verify=plan.get("verify", True))
    Xtr, ytr, Xte, yte = S2.teacher_data2(task)
    n, L = task["n"], task["layers"]
    d = TL.n_params(n, L)
    theta0 = np.zeros(d)
    t0 = time.perf_counter()
    s = t0
    try:
        # training by formula: the twin's tangent at theta0, one point at a time (all 2d+1 circuits of a point share a
        # structure; common random numbers, so the +-pi/2 differences carry little trajectory noise)
        shifts = [theta0]
        for k in range(d):
            e = np.zeros(d)
            e[k] = math.pi / 2
            shifts += [theta0 + e, theta0 - e]
        f0 = np.empty(len(Xtr))
        G = np.empty((len(Xtr), d))
        for i, x in enumerate(Xtr):
            s = time.perf_counter()
            cs = [R.compile(th, x) for th in shifts]
            zs = R.z("sim", cs, p["feat_traj"], int(p.get("seed", 0)) * 1000003 + i, crn=True)
            R.t["sim"] += time.perf_counter() - s
            f0[i] = zs[0]
            G[i] = (zs[1::2] - zs[2::2]) / 2
        m, tau = E.closed_form(f0, G, ytr, theta0)
        rec.update(loops=0, tau=tau, tangent_evaluations=len(Xtr) * len(shifts), final_mean=[float(v) for v in m],
                   train_wall_s=time.perf_counter() - t0, curve=[], gnorm=[])
        # predict
        cs = [R.compile(m, x) for x in Xte]
        s = time.perf_counter()
        z_twin = R.z("sim", cs, pr["traj"], pr["seed"])
        p1 = (1 - z_twin) / 2
        rec["prediction"] = predict_job(p1, yte, pr["shots"], pr["reps"], pr["level"], pr["seed"] + 1, traj=pr["traj"])
        rec["prediction_shots_only"] = predict_job(p1, yte, pr["shots"], pr["reps"], pr["level"], pr["seed"] + 1)
        rec["prediction"]["twin_p1"] = [float(x) for x in p1]
        rec["chance"] = dict(acc=0.5, ce=float(np.log(2)))
        rec["test_labels"] = [int(v) for v in yte]
        if keep is not None:
            keep["circuits"] = cs
        if not plan.get("verify", True):
            raise _SkipVerify
        # verify on the stand-in (rehearsal)
        z_dev = R.z("dev", cs, pr["shots"], pr["seed"] + 2, shots=True)
        z_dev_exact = R.z("dev", cs, pr["traj"], pr["seed"] + 3)
        R.t["eval"] += time.perf_counter() - s
        ce, acc = _scores(z_dev, yte)
        P = rec["prediction"]
        # H1's count: a point is correct when the measured <Z> has the label's sign (label +1 <-> <Z> > 0 <->
        # P(1) < 0.5); <Z> = 0 exactly (P(1) = 0.5) counts as wrong. One-sided exact binomial test against 0.5.
        from scipy.stats import binomtest
        n_correct = int(np.sum(np.sign(z_dev) == yte))
        rec["rehearsal"] = dict(
            ce=ce, acc=acc, n_correct_strict=n_correct, n_points=int(len(yte)),
            h1_p=float(binomtest(n_correct, len(yte), 0.5, alternative="greater").pvalue), ce_inside=P["ce_interval"][0] <= ce <= P["ce_interval"][1],
            acc_inside=P["acc_interval"][0] <= acc <= P["acc_interval"][1], ce_gap=ce - P["ce_mean"],
            acc_gap=acc - P["acc_mean"], standin_ce_exact=S2._ce(z_dev_exact, yte),
            twin_vs_standin_p1_rmse=float(np.sqrt(np.mean(((1 - z_dev_exact) / 2 - p1) ** 2))),
            standin_p1=[float(x) for x in (1 - z_dev_exact) / 2])
    except _SkipVerify:
        R.t["eval"] += time.perf_counter() - s
    except Exception as exc:  # noqa: BLE001 - recorded
        rec["error"] = f"{type(exc).__name__}: {exc}"
    rec.update(wall_s=time.perf_counter() - t0, times=R.t, structures=R.n_struct, compiled=R.arm.compiled,
               structural_fail=R.arm.structural_fail, on_failed_ops=R.arm.on_failed_ops,
               durations_us=sorted({round(v[0] * 1e6, 4) for v in R.arm._dur.values()}),
               q2=sorted({v[1] for v in R.arm._dur.values()}), ended=S._cest())
    rec["valid"] = "error" not in rec and not R.arm.structural_fail and not R.arm.on_failed_ops
    return rec




def main(argv):
    """python -m toqb.s2re_run PLAN.json OUT.json SPEC"""
    if len(argv) != 3:
        print(main.__doc__)
        return 1
    plan_file, out, spec = argv
    if os.path.exists(out):
        print(f"{out} exists: a run never overwrites another", file=sys.stderr)
        return 2
    rec = run_s2re(json.load(open(plan_file, encoding="utf-8")), spec)
    with open(out + ".tmp", "w", encoding="utf-8") as f:
        json.dump(rec, f)
    os.replace(out + ".tmp", out)
    short = {k: rec.get(k) for k in ("kind", "arm", "valid", "train_wall_s", "wall_s", "error")}
    if "rehearsal" in rec:
        P, Rh = rec["prediction"], rec["rehearsal"]
        short.update(pred_ce=round(P["ce_mean"], 4), pred_ce_int=[round(x, 4) for x in P["ce_interval"]],
                     standin_ce=round(Rh["ce"], 4), inside=Rh["ce_inside"], pred_acc=round(P["acc_mean"], 3),
                     standin_acc=round(Rh["acc"], 3), h1_p=Rh["h1_p"], p1_rmse=round(Rh["twin_vs_standin_p1_rmse"], 4))
    print(json.dumps(short), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
