"""Prediction and stand-in verification at a checkpoint, for the fruit match (2026-10-21).

The same computation as the end of `toqb.s2rc.run_s2rc` (prediction with the twin's P(1) from predict.traj
trajectories, R simulated jobs, the stand-in's job and exact P(1)), as a function that returns the fields instead of
writing them into the run record, so a run can take it at several budget points. The seeds are the plan's predict
seeds at every checkpoint (common random numbers across a run's checkpoints and across runs of the same task).
"""
from __future__ import annotations

import time

import numpy as np

from toqb import s2r2 as S2
from toqb.s2rc import _scores, predict_job


def predict_verify(R, theta, Xte, yte, pr, verify=True):
    """dict(prediction, prediction_shots_only, rehearsal) for the parameters theta (rehearsal only with verify)."""
    s = time.perf_counter()
    cs = [R.compile(theta, x) for x in Xte]
    z_twin = R.z("sim", cs, pr["traj"], pr["seed"])
    p1 = (1 - z_twin) / 2
    out = dict(prediction=predict_job(p1, yte, pr["shots"], pr["reps"], pr["level"], pr["seed"] + 1, traj=pr["traj"]),
               prediction_shots_only=predict_job(p1, yte, pr["shots"], pr["reps"], pr["level"], pr["seed"] + 1))
    out["prediction"]["twin_p1"] = [float(x) for x in p1]
    if verify:
        z_dev = R.z("dev", cs, pr["shots"], pr["seed"] + 2, shots=True)
        z_dev_exact = R.z("dev", cs, pr["traj"], pr["seed"] + 3)
        ce, acc = _scores(z_dev, yte)
        P = out["prediction"]
        from scipy.stats import binomtest
        n_correct = int(np.sum(np.sign(z_dev) == yte))
        out["rehearsal"] = dict(
            ce=ce, acc=acc, n_correct_strict=n_correct, n_points=int(len(yte)),
            h1_p=float(binomtest(n_correct, len(yte), 0.5, alternative="greater").pvalue),
            ce_inside=P["ce_interval"][0] <= ce <= P["ce_interval"][1],
            acc_inside=P["acc_interval"][0] <= acc <= P["acc_interval"][1], ce_gap=ce - P["ce_mean"],
            acc_gap=acc - P["acc_mean"], standin_ce_exact=S2._ce(z_dev_exact, yte),
            twin_vs_standin_p1_rmse=float(np.sqrt(np.mean(((1 - z_dev_exact) / 2 - p1) ** 2))),
            standin_p1=[float(x) for x in (1 - z_dev_exact) / 2])
    R.t["eval"] += time.perf_counter() - s
    return out
