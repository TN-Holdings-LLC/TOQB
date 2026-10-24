"""Where does the readout offset come from? (flow B, item 4; report only, no rule; 2026-10-24)

    python -m toqb.offset_ablate RUNS_DIR OUT.json [--variants full,no_zz,no_over,no_t12,plain] [--points 0,2000] [--traj 1024]

RUNS_DIR: toqb.s2rc_ckpt records (the far-teacher runs: item 31 and the zipper, teachers 17-19 at angle 1.0). For
each run, at theta = 0 and at the listed points (2000 = the final parameters, 500 = the checkpoint), on each
stand-in variant:

- full: the stand-in of the plan (t12 0.3, over 0.01, zz 10 kHz);
- no_zz / no_over / no_t12: that one addition switched off (zz_hz 0, over 0, t12 0);
- plain: all three off, i.e. the snapshot's own noise in the stand-in's engine;

(lam, delta, fit rms) of the stand-in's <Z> against the noiseless model on the 64 training inputs (no labels), and the
share of +1 answers and the shot-free accuracy on the 500 test points. The twin's (lam, delta) on the training inputs
is recorded beside them. 1,024 trajectories, seed of the plan's predict.seed + 11. Labels are used only for the
accuracy reported. The arm is the run's own; with the a24 switch (2026-10-24) the circuits are the same
(results/a24-identity-2026-10-24).
"""
from __future__ import annotations

import copy
import glob
import json
import os
import sys

import numpy as np

from toqb import s2r2 as S2
from toqb import task_loop as TL
from toqb import undamp as U

VARIANTS = {"full": {}, "no_zz": {"zz_hz": 0.0}, "no_over": {"over": 0.0}, "no_t12": {"t12": 0.0},
            "plain": {"zz_hz": 0.0, "over": 0.0, "t12": 0.0}}
TRAJ = 1024


def main(argv):
    argv = list(argv)
    if len(argv) < 2:
        print(__doc__)
        return 1
    runs, out = argv[0], argv[1]
    variants = list(VARIANTS)
    points = [0, 2000]
    if "--variants" in argv:
        variants = argv[argv.index("--variants") + 1].split(",")
    if "--points" in argv:
        points = [int(v) for v in argv[argv.index("--points") + 1].split(",")]
    global TRAJ
    if "--traj" in argv:  # for a smoke test only; the report uses 1,024
        TRAJ = int(argv[argv.index("--traj") + 1])
    if os.path.exists(out):
        print(f"STOP: {out} exists: an output is never overwritten", file=sys.stderr)
        return 2
    data, rows = {}, []
    for f in sorted(glob.glob(os.path.join(runs, "*.json"))):
        rec = json.load(open(f, encoding="utf-8"))
        task = rec["task"]
        key = json.dumps(task, sort_keys=True)
        if key not in data:
            data[key] = S2.teacher_data2(task)
        Xtr, _, Xte, yte = data[key]
        yte = np.asarray(yte)
        thetas = {0: np.zeros(TL.n_params(task["n"], task["layers"]))}
        for c in rec.get("checkpoints", []):
            thetas[int(c["loop"])] = np.asarray(c["theta"])
        thetas[int(rec["loops"])] = np.asarray(rec["final_mean"])
        plan = json.load(open(os.path.join(os.path.dirname(os.path.abspath(runs)), "plans",
                                           os.path.basename(f).split("-")[0] + ".json"), encoding="utf-8"))
        seed = plan["predict"]["seed"] + 11
        for v in variants:
            p = copy.deepcopy(plan)
            p["standin"].update(VARIANTS[v])
            R = S2.Runner(p, rec["arm"])
            for pt in points:
                th = thetas[pt]
                zi_tr = U.ideal_z(th, Xtr, task)
                ztr = R.z("dev", [R.compile(th, x) for x in Xtr], TRAJ, seed)
                lam, delta, rms = U.fit(ztr, zi_tr)
                zte = R.z("dev", [R.compile(th, x) for x in Xte], TRAJ, seed + 1)
                row = dict(file=os.path.basename(f), arm=rec["arm"], teacher=int(task["teacher_seed"]), variant=v,
                           loop=pt, lam=lam, delta=delta, rms=rms, plus_share=float(np.mean(zte > 0)),
                           acc=float(np.mean(np.sign(zte) == yte)))
                if v == variants[0]:
                    tl, td, tr = U.fit(R.z("sim", [R.compile(th, x) for x in Xtr], TRAJ, seed), zi_tr)
                    row.update(twin_lam=tl, twin_delta=td, twin_rms=tr)
                rows.append(row)
                print(json.dumps(row), flush=True)
    json.dump(dict(variants={v: VARIANTS[v] for v in variants}, traj=TRAJ, rows=rows), open(out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
