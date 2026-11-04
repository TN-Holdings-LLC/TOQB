"""Append one finished P6-form job's readings to the ledger (a new file; the old one is kept): floor kind from the
theta_x = 0 cells (mean over their t, SE combined), mirror kind from the mirror2d cells (d = floor - mirror) when the
job has them. Physical qubit labels from the record's mapping (job 1: ising2d records; job 2: repair2d records, A's
copy and B's copy each read with their own job line, recorded under one job name).

usage: PYTHONPATH=<psf-os> python ledger_from_job.py JOB_DIR RUNS_DIR LEDGER_IN|none LEDGER_OUT JOB_NAME WHEN
WHEN: "YYYY-MM-DD HH:MM:SS" (CET) or auto (the CET time in JOB_DIR/submission.json's "submitted" field)
"""
import json
import os
import re
import sys

import numpy as np

from psf_os import ising2d as I
from psf_os import job as J
from psf_os import ledger as Lg
from psf_os import repair2d as Rp
from psf_os.kim import z_values

jd, runs, lin, lout, name, when = sys.argv[1:7]
if when == "auto":
    sub = json.load(open(os.path.join(jd, "submission.json"))).get("submitted", "")
    m = re.search(r"\((\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) CET\)", sub)
    if not m:
        raise SystemExit(f"STOP: no CET time in submission.json ({sub!r}); give WHEN by hand")
    when = m.group(1)
print(f"{name}: when {when} CET")
led = Lg.load(lin) if lin != "none" else Lg.empty()
n = len(I.QUBITS)
floor, mirror, maps = {}, {}, {}
for cell, (rec, cc) in J.read(jd, runs).items():
    kind = rec.get("psfos_job", {}).get("kind")
    if kind not in ("ising2d", "mirror2d", "repair2d"):
        continue
    for p in rec["points"]:
        z, se = z_values(cc[(p["input"], "z")], n)
        if kind == "ising2d" and float(rec["psfos_job"].get("theta_x", 0.53)) == 0.0:
            floor.setdefault("A", []).append((z, se))
            maps["A"] = rec["mapping"]
        elif kind == "mirror2d":
            mirror.setdefault("A", []).append((z, se))
        elif kind == "repair2d" and float(rec["psfos_job"]["theta_x"]) == 0.0:
            floor.setdefault(p["arm"], []).append((z, se))
            maps[p["arm"]] = rec[f"mapping_{p['arm']}"]


def avg(v):
    z = np.mean([a for a, _ in v], axis=0)
    return z, np.sqrt(np.sum([np.square(s) for _, s in v], axis=0)) / len(v)


for arm, v in sorted(floor.items()):
    z0, s0 = avg(v)
    zm, sm = avg(mirror[arm]) if arm in mirror else (None, None)
    phys = [maps[arm][str(q)] for q in I.QUBITS]
    rd = Rp.readings(phys, z0, s0, zm, sm)
    # one job name for both copies: two copies in one job are one job for rule a (two different jobs)
    led = Rp.record(led, json.load(open(f"{jd}/manifest.json"))["fetch"]["backend"], name, when, rd)
    for kind, (r, line) in rd.items():
        print(f"{name} {arm} {kind}: line {line:.3f}, DEAD {[x[0] for x in r if x[1] == 'DEAD']}")
Lg.save(led, lout)
