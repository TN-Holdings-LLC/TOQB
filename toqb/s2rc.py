"""S2R, design C (the owner's decision of 2026-10-19): learn entirely on the GPU twin, predict, then verify once.

    python -m toqb.s2rc PLAN.json OUT.json SPEC        (from the TOQB root; TOQB_XP=cupy for the GPU)

1. **Train** on the twin only (the simulator's model of the device, `toqb.traj2`; no device is used): every loop the
   antithetic gradient of the training loss from `pairs` random +-1 directions at m +- h D on `sim_batch` training
   points (T = `sim_traj` trajectories, common random numbers), m <- m - lr g, for `loops` loops. Every `curve_every`
   loops the twin's CE on the first `curve_points` test points is recorded (the learning curve; not billed).
2. **Predict** what one device job will show: the twin's P(1) (readout included) of every test point from
   `predict.traj` trajectories; then `predict.reps` simulated device jobs, each drawing `shots` shots per test point
   from those P(1) and scoring them exactly as the device's answers will be scored (CE of p = (1 + z) / 2 clipped to
   [1e-4, 1 - 1e-4], accuracy with ties counted 0.5). The prediction is the distribution of those scores: its mean and
   its central `predict.level` interval, with the shots' noise and the twin's own Monte Carlo error (finite
   trajectories, bounded from above); the shots-only interval is recorded too. The twin's model error (twin != device)
   is not in the interval: it is what the verification measures.
3. **Verify (rehearsal)** on the stand-in (stage 0's device stand-in; simulation): one job of `shots` shots per test
   point, scored the same way; whether CE and accuracy fall inside the predicted intervals, and the gaps. The stand-in's
   exact <Z> (trajectory mean, `predict.traj`) is recorded too, to separate the twin's error from shot noise.

The device job itself (IBM hardware) is not run here; it needs the owner's go-ahead and a twin built from that day's
calibration. The record holds the final parameters, so the same model can be compiled and sent later.
"""
from __future__ import annotations

import json
import os
import time

import numpy as np

from toqb import s2r as S
from toqb import s2r2 as S2
from toqb import task_loop as TL


def _scores(z, y):
    acc = float(np.mean(np.where(z == 0, 0.5, (np.sign(z) == y).astype(float))))
    return S2._ce(z, y), acc


def predict_job(p1, y, shots, reps, level, seed, traj=None):
    """Distribution of (CE, accuracy) of one simulated device job: `shots` shots per point from P(1) = p1. With
    `traj` (the trajectories behind p1), each replicate first redraws every P(1) from N(p1, p1 (1 - p1) / traj),
    clipped to [0, 1]: the twin's own Monte Carlo error, bounded from above (a trajectory's P(1) lies in [0, 1]), is
    then part of the interval."""
    rng = np.random.default_rng(seed)
    P1 = np.broadcast_to(np.asarray(p1, dtype=float), (reps, len(p1)))
    if traj:
        P1 = np.clip(P1 + rng.standard_normal(P1.shape) * np.sqrt(P1 * (1 - P1) / traj), 0.0, 1.0)
    k = rng.binomial(shots, P1)
    zs = 1 - 2 * k / shots
    ce = np.array([S2._ce(z, y) for z in zs])
    acc = np.mean(np.where(zs == 0, 0.5, (np.sign(zs) == y[None, :]).astype(float)), axis=1)
    lo, hi = (1 - level) / 2 * 100, (1 + level) / 2 * 100
    return dict(ce_mean=float(ce.mean()), ce_interval=[float(np.percentile(ce, lo)), float(np.percentile(ce, hi))],
                acc_mean=float(acc.mean()), acc_interval=[float(np.percentile(acc, lo)), float(np.percentile(acc, hi))],
                ce_exact=S2._ce(1 - 2 * np.asarray(p1), y), reps=reps, level=level, shots=shots)


def run_s2rc(plan, spec):
    task, p, pr = plan["task"], plan["train"], plan["predict"]
    R = S2.Runner(plan, spec)
    rec = dict(kind="s2rc", arm=spec, seed=p["seed"], plan=plan["name"], started=S._cest(), train=p, predict=pr,
               version=R.arm.version(), standin=R.standin.params, engine=R.eng.xp.__name__, dtype=str(R.eng.dtype))
    Xtr, ytr, Xte, yte = S2.teacher_data2(task)
    n, L = task["n"], task["layers"]
    d = TL.n_params(n, L)
    rng = np.random.default_rng(p["seed"])
    m = rng.uniform(-p["init"], p["init"], d)
    K, b, Ts, h, lr = p["pairs"], p["sim_batch"], p["sim_traj"], p["h"], p["lr"]
    cp = min(p["curve_points"], len(Xte))
    curve, gnorm = [], []
    t0 = time.perf_counter()

    def twin_ce(k):
        s = time.perf_counter()
        z = R.z("sim", [R.compile(m, x) for x in Xte[:cp]], p["curve_traj"], p["seed"] * 7 + k)
        R.t["eval"] += time.perf_counter() - s
        ce, acc = _scores(z, yte[:cp])
        curve.append(dict(loop=k, twin_ce=ce, twin_acc=acc, wall_s=time.perf_counter() - t0))
    try:
        twin_ce(0)
        for k in range(1, p["loops"] + 1):
            idx = rng.choice(len(Xtr), b, replace=False)
            D = rng.choice([-1.0, 1.0], (K, d))
            cands = np.vstack([m[None, :] + h * D, m[None, :] - h * D])
            s = time.perf_counter()
            cs = [R.compile(th, Xtr[i]) for th in cands for i in idx]
            zs = R.z("sim", cs, Ts, p["seed"] * 1000003 + k, crn=True).reshape(2 * K, b)
            R.t["sim"] += time.perf_counter() - s
            ls = ((1 - zs * ytr[idx][None, :]) / 2).mean(axis=1)
            g = (((ls[:K] - ls[K:]) / (2 * h))[:, None] * D).mean(axis=0)
            m = m - lr * g
            gnorm.append(float(np.linalg.norm(g)))
            if k % p["curve_every"] == 0 or k == p["loops"]:
                twin_ce(k)
        rec.update(loops=p["loops"], curve=curve, gnorm=gnorm, final_mean=[float(x) for x in m],
                   train_wall_s=time.perf_counter() - t0)
        # predict
        cs = [R.compile(m, x) for x in Xte]
        s = time.perf_counter()
        z_twin = R.z("sim", cs, pr["traj"], pr["seed"])
        p1 = (1 - z_twin) / 2
        rec["prediction"] = predict_job(p1, yte, pr["shots"], pr["reps"], pr["level"], pr["seed"] + 1, traj=pr["traj"])
        rec["prediction_shots_only"] = predict_job(p1, yte, pr["shots"], pr["reps"], pr["level"], pr["seed"] + 1)
        rec["prediction"]["twin_p1"] = [float(x) for x in p1]
        rec["chance"] = dict(acc=0.5, ce=float(np.log(2)))
        # verify on the stand-in (rehearsal)
        z_dev = R.z("dev", cs, pr["shots"], pr["seed"] + 2, shots=True)
        z_dev_exact = R.z("dev", cs, pr["traj"], pr["seed"] + 3)
        R.t["eval"] += time.perf_counter() - s
        ce, acc = _scores(z_dev, yte)
        P = rec["prediction"]
        rec["rehearsal"] = dict(
            ce=ce, acc=acc, ce_inside=P["ce_interval"][0] <= ce <= P["ce_interval"][1],
            acc_inside=P["acc_interval"][0] <= acc <= P["acc_interval"][1], ce_gap=ce - P["ce_mean"],
            acc_gap=acc - P["acc_mean"], standin_ce_exact=S2._ce(z_dev_exact, yte),
            twin_vs_standin_p1_rmse=float(np.sqrt(np.mean(((1 - z_dev_exact) / 2 - p1) ** 2))),
            standin_p1=[float(x) for x in (1 - z_dev_exact) / 2])
    except Exception as exc:  # noqa: BLE001 - recorded
        rec["error"] = f"{type(exc).__name__}: {exc}"
    rec.update(wall_s=time.perf_counter() - t0, times=R.t, structures=R.n_struct, compiled=R.arm.compiled,
               structural_fail=R.arm.structural_fail, on_failed_ops=R.arm.on_failed_ops,
               durations_us=sorted({round(v[0] * 1e6, 4) for v in R.arm._dur.values()}),
               q2=sorted({v[1] for v in R.arm._dur.values()}), ended=S._cest())
    rec["valid"] = "error" not in rec and not R.arm.structural_fail and not R.arm.on_failed_ops
    return rec


def main(argv):
    """python -m toqb.s2rc PLAN.json OUT.json SPEC"""
    import sys
    if len(argv) != 3:
        print(main.__doc__)
        return 1
    plan_file, out, spec = argv
    if os.path.exists(out):
        print(f"{out} exists: a run never overwrites another", file=sys.stderr)
        return 2
    plan = json.load(open(plan_file, encoding="utf-8"))
    rec = run_s2rc(plan, spec)
    with open(out + ".tmp", "w", encoding="utf-8") as f:
        json.dump(rec, f)
    os.replace(out + ".tmp", out)
    short = {k: rec.get(k) for k in ("kind", "arm", "seed", "valid", "loops", "wall_s", "error")}
    if "rehearsal" in rec:
        P, Rh = rec["prediction"], rec["rehearsal"]
        short.update(pred_ce=round(P["ce_mean"], 4), pred_ce_int=[round(x, 4) for x in P["ce_interval"]],
                     standin_ce=round(Rh["ce"], 4), inside=Rh["ce_inside"], pred_acc=round(P["acc_mean"], 3),
                     standin_acc=round(Rh["acc"], 3), p1_rmse=round(Rh["twin_vs_standin_p1_rmse"], 4))
    print(json.dumps(short), flush=True)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
