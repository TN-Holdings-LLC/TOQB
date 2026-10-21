"""Apply the undamped readout (toqb.undamp) to a finished run, at every recorded point (2026-10-21).

    python -m toqb.undamp_run RUN.json OUT.json [--traj 1024] [--final-only]     (TOQB_XP=cupy for the GPU)

For a run record of toqb.s2rc, toqb.s2rc_ckpt, toqb.s2re4_run or toqb.s2re_run (any arm), at the final parameters and
at every checkpoint:
1. (lam, delta) from the run's own twin on its 64 training inputs (`--traj` trajectories, seed predict.seed + 5),
   against the exact noiseless model; no labels, no stand-in.
2. The undamped prediction: the record's twin P(1) of the test points through the same simulated jobs as the raw
   prediction (same seed), each job's <Z> undamped before scoring.
3. The undamped stand-in score: the stand-in's job is drawn again with the run's own seed (predict.seed + 2), so the
   shots are the ones the raw score used (checked: the raw CE recomputed must equal the record's; a mismatch is
   reported, not hidden), then scored with the undamped readout; the undamped CE of the stand-in's exact P(1) too.
4. Whether the undamped stand-in CE falls inside the undamped prediction's interval (the prediction layer).
Nothing in the run is changed; the output is a separate record (kind "undamp"). Outputs are never overwritten.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

from toqb import s2r as S
from toqb import s2r2 as S2
from toqb import undamp as U
from toqb.s2rc import _scores


def points(rec):
    d = len(rec["final_mean"]) if rec.get("final_mean") else None
    out = []
    for c in rec.get("checkpoints", []):
        lab = f"loop {c['loop']}" if "loop" in c else f"sweep {c['sweep']}"
        out.append((lab, np.array(c["theta"]), c["prediction"], c["rehearsal"]))
    if rec.get("final_mean") is not None:
        lab = f"loop {rec.get('loops')}" if rec["kind"] == "s2rc" else f"sweep {rec.get('sweeps')}"
        out.append((lab, np.array(rec["final_mean"]), rec["prediction"], rec["rehearsal"]))
    return out, d


def run(rec, traj=1024, final_only=False):
    task, pr = rec["task"], rec["predict"]
    plan = dict(name=rec["plan"], device=rec["device"], task=task, train=rec["train"], predict=pr,
                standin=rec["standin"])
    R = S2.Runner(plan, rec["arm"])
    Xtr, ytr, Xte, yte = S2.teacher_data2(task)
    pts, d = points(rec)
    if not pts:  # theta = 0 runs (Z) keep no final_mean
        from toqb import task_loop as TL
        pts = [("theta = 0", np.zeros(TL.n_params(task["n"], task["layers"])), rec["prediction"], rec["rehearsal"])]
    if final_only:
        pts = pts[-1:]
    out = dict(kind="undamp", source=dict(plan=rec["plan"], arm=rec["arm"], kind=rec["kind"], seed=rec.get("seed")),
               task=task, traj=traj, seed=int(pr["seed"]) + 5, started=S._cest(), points=[])
    for lab, th, P, Rh in pts:
        t0 = time.perf_counter()
        lam, delta, rms = U.estimate(R, th, Xtr, task, traj, int(pr["seed"]) + 5)
        Pu = U.predict_job_undamped(P["twin_p1"], yte, pr["shots"], pr["reps"], pr["level"], pr["seed"] + 1, lam, delta,
                                    traj=pr["traj"])
        cs = [R.compile(th, x) for x in Xte]
        z_dev = R.z("dev", cs, pr["shots"], pr["seed"] + 2, shots=True)
        ce_raw, acc_raw = _scores(z_dev, yte)
        ce_u, acc_u = U.score(z_dev, yte, lam, delta)
        sp1 = np.asarray(Rh["standin_p1"])
        ce_u_exact = S2._ce(U.apply(1 - 2 * sp1, lam, delta), yte)
        out["points"].append(dict(
            point=lab, lam=lam, delta=delta, fit_rms=rms,
            raw=dict(ce=ce_raw, acc=acc_raw, ce_recorded=Rh["ce"], reproduced=bool(abs(ce_raw - Rh["ce"]) < 1e-9),
                     pred_ce=P["ce_mean"], pred_ce_interval=P["ce_interval"], inside=Rh.get("ce_inside")),
            undamped=dict(ce=ce_u, acc=acc_u, ce_exact=ce_u_exact, pred_ce=Pu["ce_mean"],
                          pred_ce_interval=Pu["ce_interval"], pred_acc=Pu["acc_mean"],
                          inside=bool(Pu["ce_interval"][0] <= ce_u <= Pu["ce_interval"][1])),
            wall_s=time.perf_counter() - t0))
        q = out["points"][-1]
        print(f"{lab}: lam {lam:.3f} delta {delta:+.3f} | stand-in CE {ce_raw:.4f} -> {ce_u:.4f}, acc {acc_raw:.3f} -> "
              f"{acc_u:.3f} | undamped prediction {Pu['ce_mean']:.4f} [{Pu['ce_interval'][0]:.4f}, "
              f"{Pu['ce_interval'][1]:.4f}] inside {q['undamped']['inside']} | shots reproduced {q['raw']['reproduced']}",
              flush=True)
    out["ended"] = S._cest()
    return out


def main(argv):
    """python -m toqb.undamp_run RUN.json OUT.json [--traj 1024] [--final-only]"""
    argv = list(argv)
    traj = 1024
    if "--traj" in argv:
        i = argv.index("--traj")
        traj = int(argv[i + 1])
        del argv[i:i + 2]
    final_only = "--final-only" in argv
    argv = [a for a in argv if a != "--final-only"]
    if len(argv) != 2:
        print(main.__doc__)
        return 1
    src, dst = argv
    if os.path.exists(dst):
        print(f"{dst} exists: an output is never overwritten", file=sys.stderr)
        return 2
    try:
        res = run(json.load(open(src, encoding="utf-8")), traj=traj, final_only=final_only)
    except U.Stop as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2
    with open(dst + ".tmp", "w", encoding="utf-8") as f:
        json.dump(res, f)
    os.replace(dst + ".tmp", dst)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
