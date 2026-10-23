"""Does the twin's training gradient point where the noiseless model's does? (report only, 2026-10-23)

    python -m toqb.grad_agree RUN.json OUT.json [--dirs 64] [--traj 32] [--inputs 64]    (TOQB_XP=cupy on the GPU)

For a toqb.s2rc run record, at the training's start (theta = 0, design C's C0) and at its final parameters: the
training loss's derivative along J random directions D_j (Rademacher, seed fixed, the same for every run),
s_j = (loss(theta + h D_j) - loss(theta - h D_j)) / 2h with the run's h, loss = mean over the first `inputs` training
points of (1 - y z) / 2 (the loss design C trains on), in the run's twin (trajectories with common random numbers, as
the training) and in the exact noiseless model. With Rademacher directions these projections preserve inner products,
so cos(S_twin, S_ideal) estimates the cosine between the twin's and the noiseless gradient. The twin's projections are
computed twice with independent trajectory seeds: cos(S_twin1, S_twin2) shows how much trajectory noise alone lowers
the cosine. Also reported: the norms, and their ratio (the twin's gradient scale against the noiseless one).

The hypothesis it serves (home, 2026-10-22; the workplace's item 2 of 2026-10-23): on a circuit where the noise acts
as one uniform shrink (the zipper), the twin's gradient is the noiseless one scaled; on item 31's it is bent.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

from toqb import s2r2 as S2
from toqb import undamp as U

DIR_SEED = 20261023


def projections(R, theta, X, y, task, D, h, T, seed, chunk=16):
    """(twin projections, noiseless projections) of the loss gradient on the directions D."""
    J = len(D)
    st, si = np.empty(J), np.empty(J)
    for a in range(0, J, chunk):
        Dc = D[a:a + chunk]
        thetas = np.vstack([theta[None, :] + h * Dc, theta[None, :] - h * Dc])
        cs = [R.compile(th, x) for th in thetas for x in X]
        z = R.z("sim", cs, T, seed, crn=True).reshape(len(thetas), len(X))
        loss = ((1 - z * y[None, :]) / 2).mean(axis=1)
        k = len(Dc)
        st[a:a + k] = (loss[:k] - loss[k:]) / (2 * h)
        zi = np.array([U.ideal_z(th, X, task) for th in thetas])
        li = ((1 - zi * y[None, :]) / 2).mean(axis=1)
        si[a:a + k] = (li[:k] - li[k:]) / (2 * h)
    return st, si


def cos(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na > 0 and nb > 0 else float("nan")


def run(rec, J=64, T=32, n_inputs=64):
    task = rec["task"]
    plan = dict(name=rec["plan"], device=rec["device"], task=task, train=rec["train"], predict=rec["predict"],
                standin=rec["standin"])
    R = S2.Runner(plan, rec["arm"])
    Xtr, ytr, _, _ = S2.teacher_data2(task)
    X, y = Xtr[:n_inputs], np.asarray(ytr[:n_inputs], float)
    d = len(rec["final_mean"])
    D = np.random.default_rng(DIR_SEED).choice([-1.0, 1.0], (J, d))
    h = float(rec["train"]["h"])
    out = dict(kind="grad_agree", source=dict(plan=rec["plan"], arm=rec["arm"], seed=rec.get("seed")), task=task,
               dirs=J, traj=T, inputs=len(X), h=h, dir_seed=DIR_SEED, started=time.strftime("%Y-%m-%d %H:%M:%S"),
               points=[])
    base = int(rec["predict"]["seed"]) + 11
    for lab, theta in (("start", np.zeros(d)), (f"loop {rec.get('loops')}", np.asarray(rec["final_mean"]))):
        t0 = time.perf_counter()
        s1, si = projections(R, theta, X, y, task, D, h, T, base)
        s2, _ = projections(R, theta, X, y, task, D, h, T, base + 1)
        st = (s1 + s2) / 2
        pt = dict(point=lab, cos_twin_ideal=cos(st, si), cos_twin1_ideal=cos(s1, si), cos_twin2_ideal=cos(s2, si),
                  cos_twin1_twin2=cos(s1, s2), norm_twin=float(np.linalg.norm(st)), norm_ideal=float(np.linalg.norm(si)),
                  scale=float(np.linalg.norm(st) / np.linalg.norm(si)) if np.linalg.norm(si) > 0 else float("nan"),
                  wall_s=time.perf_counter() - t0)
        out["points"].append(pt)
        print(f"{lab}: cos(twin, noiseless) {pt['cos_twin_ideal']:.3f} | cos(twin, twin) {pt['cos_twin1_twin2']:.3f} | "
              f"scale {pt['scale']:.3f} | {pt['wall_s']:.0f} s", flush=True)
    return out


def main(argv):
    argv = list(argv)
    opts = dict(J=64, T=32, n_inputs=64)
    for flag, key in (("--dirs", "J"), ("--traj", "T"), ("--inputs", "n_inputs")):
        if flag in argv:
            i = argv.index(flag)
            opts[key] = int(argv[i + 1])
            del argv[i:i + 2]
    if len(argv) != 2:
        print(__doc__)
        return 1
    src, dst = argv
    if os.path.exists(dst):
        print(f"STOP: {dst} exists: an output is never overwritten", file=sys.stderr)
        return 2
    res = run(json.load(open(src, encoding="utf-8")), **opts)
    json.dump(res, open(dst, "w", encoding="utf-8"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
