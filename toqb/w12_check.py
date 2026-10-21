"""W12, the cause check of 2026-10-21: why E4 did not win early (workplace design, home code; nothing is trained).

    python -m toqb.w12_check noiseless OUT.jsonl RUNS_DIR [RUNS_DIR ...]     (CPU: T1 and T3, exact <Z0>)
    python -m toqb.w12_check twin OUT.jsonl RUNS_DIR [RUNS_DIR ...]          (GPU pod: T2, the twin, 1,024 trajectories)
    python -m toqb.w12_check table OUT.md NOISELESS.jsonl TWIN.jsonl RUNS_DIR [RUNS_DIR ...]

For every recorded point of every run (Z: theta = 0; C0 and E4: each checkpoint's theta and the final parameters):
- T1: the 64 training points' Brier mean(((f - y) / 2)^2) and accuracy, noiseless (exact <Z0>);
- T2: the same Brier on the twin (the run's own plan, arm and stand-in snapshot), 1,024 trajectories, seed
  predict.seed + 5 (fixed by W12, used by no run); the twin's per-point <Z0> on the training points is kept too
  (z_train), for a readout calibration fitted on training points only;
- T3: the 500 test points' CE (toqb.s2r2._ce) and accuracy, noiseless;
- T4: E4's claimed training change, the cumulative sum of brier_change_per_sweep.
The table adds the stand-in's test CE (the record's exact P(1)) and the realised change on the twin (T2 at the point
minus T2 at theta = 0), and E4's realised / claimed ratio. Outputs are never overwritten.
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

from toqb import s2r2 as S2
from toqb import task_loop as TL

TRAJ = 1024


def _role(rec):
    if rec["kind"] == "s2re4":
        return "Z" if int(rec.get("sweeps", 0) or 0) == 0 else ("E4v" if rec.get("variant") == "e4v" else "E4")
    return "C0" if float(rec["train"].get("init", 1.0)) == 0.0 else "C"


def points(rec):
    """(label, cost, theta, standin_p1) for every recorded point of a run, in order of cost."""
    d = TL.n_params(rec["task"]["n"], rec["task"]["layers"])
    if _role(rec) == "Z":
        return [("theta = 0", 0, np.zeros(d), rec["rehearsal"]["standin_p1"])]
    out = []
    for c in rec.get("checkpoints", []):
        lab = f"loop {c['loop']}" if "loop" in c else f"sweep {c['sweep']}"
        out.append((lab, int(c["train_traj_circuits"]), np.array(c["theta"]), c["rehearsal"]["standin_p1"]))
    lab = f"loop {rec['loops']}" if rec["kind"] == "s2rc" else f"sweep {rec['sweeps']}"
    cost = rec.get("train_traj_circuits")
    if cost is None:  # s2rc records without checkpoints (the test match)
        t = rec["train"]
        cost = t["loops"] * 2 * t["pairs"] * t["sim_batch"] * t["sim_traj"]
    out.append((lab, int(cost), np.array(rec["final_mean"]), rec["rehearsal"]["standin_p1"]))
    return sorted(out, key=lambda p: p[1])


def records(dirs):
    for d in dirs:
        for f in sorted(glob.glob(os.path.join(d, "*.json"))):
            rec = json.load(open(f, encoding="utf-8"))
            if rec.get("valid") and "rehearsal" in rec:
                yield os.path.basename(f), rec


def _key(rec):
    t = rec["task"]
    return (int(t["teacher_seed"]), float(t["teacher_angle"]), int(t["layers"]))


def _brier(f, y):
    return float(np.mean(((np.asarray(f) - y) / 2) ** 2))


def noiseless(out, dirs):
    data = {}
    with open(out, "x", encoding="utf-8") as fh:
        for name, rec in records(dirs):
            k = _key(rec)
            if k not in data:
                data[k] = S2.teacher_data2(rec["task"])
            Xtr, ytr, Xte, yte = data[k]
            n, L, enc = rec["task"]["n"], rec["task"]["layers"], rec["task"]["enc"]
            for lab, cost, th, _ in points(rec):
                ftr = np.array([TL.exact_z0(TL.angle_list(th, x, n, L, enc), n, L) for x in Xtr])
                fte = np.array([TL.exact_z0(TL.angle_list(th, x, n, L, enc), n, L) for x in Xte])
                row = dict(file=name, point=lab, cost=cost, t1_brier=_brier(ftr, ytr),
                           t1_acc=float(np.mean(np.sign(ftr) == ytr)), t3_ce=S2._ce(fte, yte),
                           t3_acc=float(np.mean(np.sign(fte) == yte)))
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                print(name, lab, {k2: round(v, 4) for k2, v in row.items() if isinstance(v, float)}, flush=True)


def twin(out, dirs):
    with open(out, "x", encoding="utf-8") as fh:
        for name, rec in records(dirs):
            plan = dict(name=rec["plan"], device=rec["device"], task=rec["task"], train=rec["train"],
                        predict=rec["predict"], standin=rec["standin"])
            R = S2.Runner(plan, rec["arm"])
            Xtr, ytr, _, _ = S2.teacher_data2(rec["task"])
            seed = int(rec["predict"]["seed"]) + 5
            for lab, cost, th, _ in points(rec):
                z = R.z("sim", [R.compile(th, x) for x in Xtr], TRAJ, seed)
                row = dict(file=name, point=lab, cost=cost, t2_brier=_brier(z, ytr), traj=TRAJ, seed=seed,
                           z_train=[round(float(v), 6) for v in z])
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                print(name, lab, round(row["t2_brier"], 4), flush=True)


def table(out, nl_file, tw_file, dirs):
    nl = {(r["file"], r["point"]): r for r in map(json.loads, open(nl_file, encoding="utf-8"))}
    tw = {(r["file"], r["point"]): r for r in map(json.loads, open(tw_file, encoding="utf-8"))} if tw_file != "-" else {}
    recs = list(records(dirs))
    z0 = {}
    for name, rec in recs:
        if _role(rec) == "Z" and (name, "theta = 0") in tw:
            z0[_key(rec)] = tw[(name, "theta = 0")]["t2_brier"]
    rows, ratios = [], []
    for name, rec in sorted(recs, key=lambda nr: (_key(nr[1]), _role(nr[1]), nr[0])):
        role = _role(rec)
        y = np.array(rec["test_labels"])
        claimed = np.cumsum(rec.get("brier_change_per_sweep", [])) if role in ("E4", "E4v") else []
        for lab, cost, _, sp1 in points(rec):
            a = nl.get((name, lab), {})
            b = tw.get((name, lab), {})
            st = S2._ce(1 - 2 * np.asarray(sp1), y)
            sw = int(lab.split()[1]) if lab.startswith("sweep") else 0
            t4 = float(claimed[sw - 1]) if role in ("E4", "E4v") and 0 < sw <= len(claimed) else None
            real = (b["t2_brier"] - z0[_key(rec)]) if b and _key(rec) in z0 else None
            ratio = (real / t4) if (t4 not in (None, 0.0) and real is not None) else None
            if ratio is not None:
                ratios.append(ratio)
            ts, ta, L = _key(rec)
            f = lambda v, nd=4: "-" if v is None else f"{v:.{nd}f}"
            rows.append(f"| {ts} | {ta} | {L} | {role} {rec.get('seed')} | {lab} | {cost:,} | {f(a.get('t1_brier'))} / "
                        f"{f(a.get('t1_acc'), 3)} | {f(b.get('t2_brier'))} | {f(t4)} | {f(real)} | {f(ratio, 2)} | "
                        f"{f(a.get('t3_ce'))} / {f(a.get('t3_acc'), 3)} | {st:.4f} |")
    head = ["# W12 cause check (2026-10-21)", "",
            "T1 noiseless training Brier / accuracy (64 points); T2 the twin's training Brier (1,024 trajectories, seed "
            "predict.seed + 5); T4 E4's claimed cumulative training change; realised = T2 at the point minus T2 at "
            "theta = 0 (the task's Z run); T3 noiseless test CE / accuracy (500 points); stand-in CE from the record's "
            "exact P(1).", "",
            f"E4 realised / claimed over all E4 points with both: {len(ratios)} points, median "
            f"{np.median(ratios):.2f}, mean {np.mean(ratios):.2f}" if ratios else "E4 realised / claimed: no points "
            "with both T2 and T4", "",
            "| teacher | angle | L | arm seed | point | cost | T1 Brier / acc | T2 Brier | T4 claimed | T2 realised | "
            "realised / claimed | T3 CE / acc | stand-in CE |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    with open(out, "x", encoding="utf-8") as fh:
        fh.write("\n".join(head + rows) + "\n")
    print(f"written {out}: {len(rows)} rows")


def main(argv):
    if len(argv) >= 3 and argv[0] == "noiseless":
        noiseless(argv[1], argv[2:])
    elif len(argv) >= 3 and argv[0] == "twin":
        twin(argv[1], argv[2:])
    elif len(argv) >= 5 and argv[0] == "table":
        table(argv[1], argv[2], argv[3], argv[4:])
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
