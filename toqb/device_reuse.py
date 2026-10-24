"""Flow C (prereg/drafts-2026-10-24/flow_c_note.md): a trained model sent to the device without training again.

    python -m toqb.device_reuse FETCH_DIR RECORD.json OUT_DIR [--points 90] [--traj N: procedure checks only]

RECORD: a toqb.s2rc_ckpt record (the far-teacher runs). Writes OUT_DIR/<name>.json and <name>.qpy in the form
`toqb.s2rc_device assemble` reads (a device run: "verify" false, the fetched Target's SHA-256, the exported circuits):

- the model is the record's final parameters, unchanged; the task and the prediction settings are the record's;
- the test points are the first P of the record's test set (its labels checked against the record's);
- the circuits are compiled by the record's arm for the fetched Target (the day's calibration): the zipper by formula
  (a24, TOQB's default front end), Qiskit by its level-2 search on that Target;
- prediction: the twin built from the fetched Target (the day's calibration), as `toqb.s2rc` predicts; beside it,
  `twin_snapshot_p1`: the twin of the 2026-10-13 snapshot (the twin used for training), on circuits compiled for the
  snapshot, so the two twins' scale errors can be compared after the job.

Nothing here connects to IBM. Labels are used only to check the subset and for the prediction's scores.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import time

import numpy as np

from toqb import s2r as S
from toqb import s2r2 as S2
from toqb.s2rc import predict_job


def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main(argv):
    argv = list(argv)
    P = 90
    if "--points" in argv:
        i = argv.index("--points"); P = int(argv[i + 1]); del argv[i:i + 2]
    traj = None  # procedure checks only: fewer twin trajectories; the device run keeps the record's
    if "--traj" in argv:
        i = argv.index("--traj"); traj = int(argv[i + 1]); del argv[i:i + 2]
    if len(argv) != 3:
        print(__doc__)
        return 1
    fetch, rec_file, out = argv
    tfile = os.path.abspath(os.path.join(fetch, "target.pkl"))
    fj = json.load(open(os.path.join(fetch, "fetch.json"), encoding="utf-8"))
    if sha256_file(tfile) != fj["target_sha256"]:
        print("STOP: target.pkl differs from fetch.json's hash", file=sys.stderr)
        return 2
    src = json.load(open(rec_file, encoding="utf-8"))
    if not src.get("valid"):
        print(f"STOP: {rec_file} is not a valid run", file=sys.stderr)
        return 2
    name = os.path.basename(rec_file)[:-5]
    os.makedirs(out, exist_ok=True)
    jf, qf = os.path.join(out, name + ".json"), os.path.join(out, name + ".qpy")
    for f in (jf, qf):
        if os.path.exists(f):
            print(f"STOP: {f} exists: a run never overwrites another", file=sys.stderr)
            return 2
    task, pr = src["task"], dict(src["predict"])
    if traj is not None:
        pr["traj"] = traj
    _, _, Xte, yte = S2.teacher_data2(task)
    Xte, yte = Xte[:P], np.asarray(yte)[:P]
    if list(map(int, yte)) != src["test_labels"][:P]:
        print("STOP: the test labels differ from the record's", file=sys.stderr)
        return 2
    theta = np.asarray(src["final_mean"])
    t0 = time.perf_counter()
    plan = dict(name=f"flow C: {name}, first {P} test points, the day's Target", device="file:" + tfile, verify=False,
                task=task, predict=pr, standin=src["standin"])
    R = S2.Runner(plan, src["arm"])
    cs = [R.compile(theta, x) for x in Xte]
    p1 = (1 - R.z("sim", cs, pr["traj"], pr["seed"])) / 2
    snap = copy.deepcopy(plan)
    snap["device"] = "snapshot:marrakesh"
    R0 = S2.Runner(snap, src["arm"])
    p1_snap = (1 - R0.z("sim", [R0.compile(theta, x) for x in Xte], pr["traj"], pr["seed"])) / 2
    rec = dict(kind="s2rc", arm=src["arm"], seed=src["seed"], plan=plan["name"], task=task, predict=pr,
               standin=src["standin"], verify=False, device=plan["device"], target_sha256=fj["target_sha256"],
               version=R.arm.version(), source=dict(record=os.path.basename(rec_file), sha256=sha256_file(rec_file),
                                                     loops=src["loops"], points=P),
               final_mean=[float(v) for v in theta], loops=0, started=S._cest(),
               traj_override=traj)
    rec["prediction"] = predict_job(p1, yte, pr["shots"], pr["reps"], pr["level"], pr["seed"] + 1, traj=pr["traj"])
    rec["prediction_shots_only"] = predict_job(p1, yte, pr["shots"], pr["reps"], pr["level"], pr["seed"] + 1)
    rec["prediction"]["twin_p1"] = [float(x) for x in p1]
    rec["twin_snapshot_p1"] = [float(x) for x in p1_snap]
    rec["test_labels"] = [int(v) for v in yte]
    from qiskit import qpy
    with open(qf, "wb") as f:
        qpy.dump(list(cs), f)
    rec["export"] = dict(qpy=os.path.basename(qf), circuits=len(cs), sha256=sha256_file(qf))
    rec.update(wall_s=time.perf_counter() - t0, structural_fail=R.arm.structural_fail, on_failed_ops=R.arm.on_failed_ops,
               durations_us=sorted({round(v[0] * 1e6, 4) for v in R.arm._dur.values()}),
               q2=sorted({v[1] for v in R.arm._dur.values()}), ended=S._cest())
    rec["valid"] = not R.arm.structural_fail and not R.arm.on_failed_ops
    json.dump(rec, open(jf, "w", encoding="utf-8"))
    print(f"{name}: {len(cs)} circuits, q2 {rec['q2']}, durations {rec['durations_us']} us, predicted acc "
          f"{rec['prediction']['acc_mean']:.3f}, valid {rec['valid']}")
    return 0 if rec["valid"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
