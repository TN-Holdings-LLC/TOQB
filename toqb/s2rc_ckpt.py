"""Design C's training with checkpoints, for the fruit match (2026-10-21).

    python -m toqb.s2rc_ckpt PLAN.json OUT.json SPEC        (from the TOQB root; TOQB_XP=cupy for the GPU)

A copy of `toqb.s2rc.run_s2rc`'s training loop (the same draws, seeds and update, line for line), with one addition:
after the loops listed in the plan's train.checkpoints, it predicts and verifies on the stand-in with
`toqb.fruit_common.predict_verify` and keeps the result in rec["checkpoints"], with the training cost spent so far
(loops x 2 pairs x sim_batch x sim_traj trajectory-circuits). The checkpoints draw no training random numbers and use
their own seeds, so the training is unchanged by them; `tests/test_fruit.py` requires this copy's final parameters
and scores to equal s2rc's on the same plan. `toqb.s2rc` itself is not changed (design C's code stays as rehearsed).
The record has kind "s2rc" (the scorer's C0 role) and every field s2rc writes.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

from toqb import s2r as S
from toqb import s2r2 as S2
from toqb import task_loop as TL
from toqb.fruit_common import predict_verify
from toqb.s2rc import _scores


def run_s2rc_ckpt(plan, spec):
    task, p, pr = plan["task"], plan["train"], plan["predict"]
    R = S2.Runner(plan, spec)
    rec = dict(kind="s2rc", arm=spec, seed=p["seed"], plan=plan["name"], started=S._cest(), train=p, predict=pr,
               version=R.arm.version(), standin=R.standin.params, engine=R.eng.xp.__name__, dtype=str(R.eng.dtype),
               device=plan["device"], task=task, verify=plan.get("verify", True), runner="toqb.s2rc_ckpt")
    Xtr, ytr, Xte, yte = S2.teacher_data2(task)
    n, L = task["n"], task["layers"]
    d = TL.n_params(n, L)
    rng = np.random.default_rng(p["seed"])
    m = rng.uniform(-p["init"], p["init"], d)
    K, b, Ts, h, lr = p["pairs"], p["sim_batch"], p["sim_traj"], p["h"], p["lr"]
    cp = min(p["curve_points"], len(Xte))
    ckpts = sorted(int(c) for c in p.get("checkpoints", []) if 0 < int(c) < p["loops"])
    per_loop = 2 * K * b * Ts
    curve, gnorm, checkpoints = [], [], []
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
            if k in ckpts:
                c = predict_verify(R, m, Xte, yte, pr, verify=plan.get("verify", True))
                c.update(loop=k, train_traj_circuits=k * per_loop, theta=[float(x) for x in m],
                         wall_s=time.perf_counter() - t0)
                checkpoints.append(c)
                rh = c.get("rehearsal", {})
                print(f"checkpoint {k} loops: stand-in CE {rh.get('ce', float('nan')):.4f} acc {rh.get('acc', float('nan')):.3f}"
                      f" inside {rh.get('ce_inside')}", flush=True)
            if k % p.get("progress_every", 50) == 0 or k == p["loops"]:
                el = time.perf_counter() - t0
                print(f"progress {k}/{p['loops']} loops, {el:.0f} s, about {el / k * (p['loops'] - k):.0f} s left"
                      + (f", twin CE {curve[-1]['twin_ce']:.4f} at loop {curve[-1]['loop']}" if curve else ""),
                      flush=True)
        rec.update(loops=p["loops"], curve=curve, gnorm=gnorm, final_mean=[float(x) for x in m],
                   train_wall_s=time.perf_counter() - t0, train_traj_circuits=p["loops"] * per_loop,
                   checkpoints=checkpoints)
        out = predict_verify(R, m, Xte, yte, pr, verify=plan.get("verify", True))
        rec.update(out)
        rec["chance"] = dict(acc=0.5, ce=float(np.log(2)))
        rec["test_labels"] = [int(v) for v in yte]
    except Exception as exc:  # noqa: BLE001 - recorded
        rec["error"] = f"{type(exc).__name__}: {exc}"
    rec.update(wall_s=time.perf_counter() - t0, times=R.t, structures=R.n_struct, compiled=R.arm.compiled,
               structural_fail=R.arm.structural_fail, on_failed_ops=R.arm.on_failed_ops,
               durations_us=sorted({round(v[0] * 1e6, 4) for v in R.arm._dur.values()}),
               q2=sorted({v[1] for v in R.arm._dur.values()}), ended=S._cest())
    rec["valid"] = "error" not in rec and not R.arm.structural_fail and not R.arm.on_failed_ops
    return rec


def main(argv):
    """python -m toqb.s2rc_ckpt PLAN.json OUT.json SPEC"""
    if len(argv) != 3:
        print(main.__doc__)
        return 1
    plan_file, out, spec = argv
    if os.path.exists(out):
        print(f"{out} exists: a run never overwrites another", file=sys.stderr)
        return 2
    rec = run_s2rc_ckpt(json.load(open(plan_file, encoding="utf-8")), spec)
    with open(out + ".tmp", "w", encoding="utf-8") as f:
        json.dump(rec, f)
    os.replace(out + ".tmp", out)
    short = {k: rec.get(k) for k in ("kind", "arm", "seed", "valid", "loops", "wall_s", "error")}
    short["checkpoints"] = [(c["loop"], round(c.get("rehearsal", {}).get("ce", float("nan")), 4)) for c in rec.get("checkpoints", [])]
    if "rehearsal" in rec:
        P, Rh = rec["prediction"], rec["rehearsal"]
        short.update(pred_ce=round(P["ce_mean"], 4), standin_ce=round(Rh["ce"], 4), inside=Rh["ce_inside"],
                     standin_acc=round(Rh["acc"], 3))
    print(json.dumps(short), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
