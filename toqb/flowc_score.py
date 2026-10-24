"""Flow C's report (prereg/drafts-2026-10-24/flow_c_note.md; no rule): the device against two twins.

    python -m toqb.flowc_score JOB_DIR RUNS_DIR OUT.md [--json OUT.json]

JOB_DIR: `toqb.s2rc_device` job folder after `result` (manifest.json, raw_counts.json); RUNS_DIR: the
`toqb.device_reuse` records it was assembled from (their SHA-256 must be the manifest's). Per cell (arm and teacher)
and per arm over its cells: the device's z = 1 - 2 P(1) per point against each twin's (the day's calibration; the
2026-10-13 snapshot): least-squares scale and offset (z_device ~ a z_twin + b), correlation, residual rms; the share
of +1 answers on the device and per twin; accuracy with the shots against the day twin's 99 % interval.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np

from toqb.s2rc_device import p1_of_counts  # the device day's reading of clbit 0


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()




def reg(zd, zt):
    a, b = np.polyfit(zt, zd, 1)
    r = float(np.corrcoef(zt, zd)[0, 1])
    rms = float(np.sqrt(np.mean((zd - (a * zt + b)) ** 2)))
    return dict(scale=float(a), offset=float(b), corr=r, rms=rms)


def main(argv):
    argv = list(argv)
    js = None
    if "--json" in argv:
        i = argv.index("--json"); js = argv[i + 1]; del argv[i:i + 2]
    if len(argv) != 3:
        print(__doc__)
        return 1
    job, runs, out = argv
    for f in (out, js):
        if f and os.path.exists(f):
            print(f"STOP: {f} exists: an output is never overwritten", file=sys.stderr)
            return 2
    man = json.load(open(os.path.join(job, "manifest.json"), encoding="utf-8"))
    raw = json.load(open(os.path.join(job, "raw_counts.json"), encoding="utf-8"))
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    ph = {}
    for i, pub in enumerate(man["pubs"]):
        ph.setdefault(pub["cell"], {})[pub["point"]] = p1_of_counts(rows[i])
    res = dict(job_id=raw.get("job_id"), backend=man["fetch"].get("backend"),
               calibration=man["fetch"].get("calibration_time"), shots=man["shots"], cells=[], arms={})
    pool = {}
    for c in man["cells"]:
        rf = os.path.join(runs, c["name"] + ".json")
        if sha(rf) != c["run_sha256"]:
            print(f"STOP: {rf} differs from the manifest", file=sys.stderr)
            return 2
        rec = json.load(open(rf, encoding="utf-8"))
        P = c["points"]
        zd = 1 - 2 * np.array([ph[c["cell"]][i] for i in range(P)])
        zday = 1 - 2 * np.array(c["twin_p1"])
        zsnap = 1 - 2 * np.array(rec["twin_snapshot_p1"])
        y = np.array(c["labels"])
        acc = float(np.mean(np.where(zd == 0, 0.5, (np.sign(zd) == y).astype(float))))
        iv = c["prediction"]["acc_interval"]
        cell = dict(name=c["name"], arm=c["arm"], teacher=int(rec["task"]["teacher_seed"]), points=P,
                    day=reg(zd, zday), snapshot=reg(zd, zsnap), plus_device=float(np.mean(zd > 0)),
                    plus_day=float(np.mean(zday > 0)), plus_snapshot=float(np.mean(zsnap > 0)), acc=acc,
                    acc_pred_day=c["prediction"]["acc_mean"], acc_inside_day=iv[0] <= acc <= iv[1])
        res["cells"].append(cell)
        a = pool.setdefault(c["arm"], dict(zd=[], zday=[], zsnap=[]))
        a["zd"] += list(zd); a["zday"] += list(zday); a["zsnap"] += list(zsnap)
    for arm, a in pool.items():
        zd, zday, zsnap = (np.array(a[k]) for k in ("zd", "zday", "zsnap"))
        res["arms"][arm] = dict(points=len(zd), day=reg(zd, zday), snapshot=reg(zd, zsnap),
                                plus_device=float(np.mean(zd > 0)))
    L = ["# Flow C: the device against two twins (report only, no rule)", "",
         f"Job {res['job_id']} on {res['backend']}, calibration {res['calibration']}, {res['shots']} shots per point.", "",
         "## Per arm (all points)", "",
         "| arm | points | scale vs day twin / vs snapshot twin | offset day / snapshot | corr day / snapshot | +1 on device |",
         "|---|---|---|---|---|---|"]
    for arm, a in res["arms"].items():
        L.append(f"| {arm} | {a['points']} | {a['day']['scale']:.2f} / {a['snapshot']['scale']:.2f} | "
                 f"{a['day']['offset']:+.3f} / {a['snapshot']['offset']:+.3f} | {a['day']['corr']:.3f} / "
                 f"{a['snapshot']['corr']:.3f} | {a['plus_device']:.2f} |")
    L += ["", "## Per cell", "", "| cell | scale day / snapshot | corr day / snapshot | +1 device / day / snapshot | "
          "accuracy (day twin's prediction, inside) |", "|---|---|---|---|---|"]
    for c in res["cells"]:
        L.append(f"| {c['name']} | {c['day']['scale']:.2f} / {c['snapshot']['scale']:.2f} | {c['day']['corr']:.3f} / "
                 f"{c['snapshot']['corr']:.3f} | {c['plus_device']:.2f} / {c['plus_day']:.2f} / {c['plus_snapshot']:.2f} | "
                 f"{c['acc']:.3f} ({c['acc_pred_day']:.3f}, {'yes' if c['acc_inside_day'] else 'no'}) |")
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    if js:
        json.dump(res, open(js, "w", encoding="utf-8"), indent=1)
    print(f"written {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
