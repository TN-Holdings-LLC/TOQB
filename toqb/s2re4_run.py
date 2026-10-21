"""Design E4 on the twin (exploratory, 2026-10-21): the same task, arms, prediction and stand-in verification as
`toqb.s2rc` (design C), with C's training loop replaced by E4's exact per-parameter solve (`toqb.s2re`).

    python -m toqb.s2re4_run PLAN.json OUT.json SPEC        (from the TOQB root; TOQB_XP=cupy for the GPU)

Training, from theta = 0, parameters in fixed order, `sweeps` times over all of them:
- For parameter k, every training point's <Z0> is exactly a + b cos u + c sin u along u (one rotation). The twin
  estimates it from the three circuits theta, theta + pi/2 e_k, theta - pi/2 e_k of every training point, in two
  independent halves of `traj` trajectories (traj / 2 each; within a half, common random numbers across the circuits
  of a structure, so the shifts' differences carry little trajectory noise).
- The Brier sum along u is P cos u + Q sin u + R cos 2u + S sin 2u (+ const); its coefficients are formed with one
  factor from each half (`s2re.brier_coeffs_split`), so they are unbiased for the noiseless ones (the bias
  correction of noisy estimates, owner principle of 2026-10-21, item 5).
- u is the exact global minimum (`s2re.trig2_min`: the quartic in tan(u/2)); u = 0 is a candidate, so a step never
  raises the estimated loss. No random directions, no learning rate, no grid.

Cost: 3 x d x m circuits x traj trajectories per sweep. With "sweeps": "budget" the run takes the whole sweeps that fit
in "budget_traj_circuits" (design C's training: loops x 2 pairs x sim_batch x sim_traj; C's learning-curve
evaluations are monitoring, not training, and are excluded for both). "sweeps": 0 is the theta = 0 control (no
training; prediction and stand-in only).

With "checkpoints": true in the train block (the fruit match, 2026-10-21), the run also predicts and verifies on the
stand-in after every sweep but the last (`toqb.fruit_common.predict_verify`), into rec["checkpoints"] with the
training cost spent so far; the checkpoints draw no training random numbers, so the training is unchanged.

The record has kind "s2re4" and the same prediction and rehearsal fields as s2rc's and s2re's.
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
from toqb.fruit_common import predict_verify
from toqb.s2rc import _SkipVerify, _scores, predict_job


def sweeps_for(p, d, m):
    if p.get("sweeps", "budget") != "budget":
        return int(p["sweeps"])
    return int(p["budget_traj_circuits"] // (3 * d * m * p["traj"]))


def run_s2re4(plan, spec, keep=None):
    task, p, pr = plan["task"], plan["train"], plan["predict"]
    R = S2.Runner(plan, spec)
    rec = dict(kind="s2re4", arm=spec, seed=p.get("seed"), plan=plan["name"], started=S._cest(), train=p, predict=pr,
               version=R.arm.version(), standin=R.standin.params, engine=R.eng.xp.__name__, dtype=str(R.eng.dtype),
               device=plan["device"], task=task, verify=plan.get("verify", True))
    Xtr, ytr, Xte, yte = S2.teacher_data2(task)
    n, L = task["n"], task["layers"]
    d, mtr = TL.n_params(n, L), len(Xtr)
    th = np.zeros(d)
    sweeps = sweeps_for(p, d, mtr)
    half = int(p.get("traj", 32)) // 2
    base = int(p.get("seed", 0)) * 1000003
    t0 = time.perf_counter()
    s = t0
    hist, steps, checkpoints = [], [], []
    try:
        for sw in range(sweeps):
            for k in range(d):
                e = np.zeros(d)
                e[k] = math.pi / 2
                s = time.perf_counter()
                cs = [R.compile(t, x) for t in (th, th + e, th - e) for x in Xtr]
                R.t["compile_e4"] = R.t.get("compile_e4", 0.0) + time.perf_counter() - s
                s = time.perf_counter()
                hs = []
                for h in range(2):
                    zs = R.z("sim", cs, half, base + 7 * (sw * d + k) + 3 * h + 1, crn=True).reshape(3, mtr)
                    hs.append(E.sinusoid(zs[2], zs[0], zs[1]))
                R.t["sim"] += time.perf_counter() - s
                P, Q, Rr, Ss = E.brier_coeffs_split(hs[0], hs[1], ytr)
                u, dv = E.trig2_min(P, Q, Rr, Ss)
                th[k] += u
                steps.append(round(float(dv) / (4 * mtr), 6))
                if (k + 1) % 34 == 0 or k == d - 1:
                    el = time.perf_counter() - t0
                    done = sw * d + k + 1
                    print(f"progress sweep {sw + 1}/{sweeps} parameter {k + 1}/{d}, {el:.0f} s, about "
                          f"{el / done * (sweeps * d - done):.0f} s left, estimated Brier change this block "
                          f"{sum(steps[-34:]):.4f}", flush=True)
            hist.append(float(sum(steps[-d:])))
            if p.get("checkpoints") and sw + 1 < sweeps:
                c = predict_verify(R, th, Xte, yte, pr, verify=plan.get("verify", True))
                c.update(sweep=sw + 1, train_traj_circuits=(sw + 1) * 3 * d * mtr * 2 * half,
                         theta=[float(v) for v in th], wall_s=time.perf_counter() - t0)
                checkpoints.append(c)
                rh = c.get("rehearsal", {})
                print(f"checkpoint sweep {sw + 1}: stand-in CE {rh.get('ce', float('nan')):.4f} acc "
                      f"{rh.get('acc', float('nan')):.3f} inside {rh.get('ce_inside')}", flush=True)
        m = th
        rec.update(loops=0, sweeps=sweeps, half_traj=half, train_traj_circuits=sweeps * 3 * d * mtr * 2 * half,
                   brier_change_per_sweep=hist, checkpoints=checkpoints, final_mean=[float(v) for v in m],
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
            keep["theta"] = m
        if not plan.get("verify", True):
            raise _SkipVerify
        # verify on the stand-in (rehearsal); the same code as toqb.s2rc and toqb.s2re_run
        z_dev = R.z("dev", cs, pr["shots"], pr["seed"] + 2, shots=True)
        z_dev_exact = R.z("dev", cs, pr["traj"], pr["seed"] + 3)
        R.t["eval"] += time.perf_counter() - s
        ce, acc = _scores(z_dev, yte)
        P = rec["prediction"]
        from scipy.stats import binomtest
        n_correct = int(np.sum(np.sign(z_dev) == yte))
        rec["rehearsal"] = dict(
            ce=ce, acc=acc, n_correct_strict=n_correct, n_points=int(len(yte)),
            h1_p=float(binomtest(n_correct, len(yte), 0.5, alternative="greater").pvalue),
            ce_inside=P["ce_interval"][0] <= ce <= P["ce_interval"][1],
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
    """python -m toqb.s2re4_run PLAN.json OUT.json SPEC"""
    if len(argv) != 3:
        print(main.__doc__)
        return 1
    plan_file, out, spec = argv
    if os.path.exists(out):
        print(f"{out} exists: a run never overwrites another", file=sys.stderr)
        return 2
    rec = run_s2re4(json.load(open(plan_file, encoding="utf-8")), spec)
    with open(out + ".tmp", "w", encoding="utf-8") as f:
        json.dump(rec, f)
    os.replace(out + ".tmp", out)
    short = {k: rec.get(k) for k in ("kind", "arm", "valid", "sweeps", "train_wall_s", "wall_s", "error")}
    if "rehearsal" in rec:
        P, Rh = rec["prediction"], rec["rehearsal"]
        short.update(pred_ce=round(P["ce_mean"], 4), pred_ce_int=[round(x, 4) for x in P["ce_interval"]],
                     standin_ce=round(Rh["ce"], 4), inside=Rh["ce_inside"], pred_acc=round(P["acc_mean"], 3),
                     standin_acc=round(Rh["acc"], 3), h1_p=Rh["h1_p"], p1_rmse=round(Rh["twin_vs_standin_p1_rmse"], 4))
    print(json.dumps(short), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
