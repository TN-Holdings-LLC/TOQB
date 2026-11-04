"""Dry runs only: synthetic raw_counts.json for a built job (product states; not data). ising2d / repair2d cells at
theta_x 0.53 use the P6 CPU answers, theta_x 0 floors and mirrors use <Z> = 0.98; every physical qubit in BAD reads
0.4 lower. Sentinel cells get all-zero strings.

usage: PYTHONPATH=<psf-os> python dry_counts.py JOB_DIR RUNS_DIR P6_ANSWERS.json BAD,BAD,... SEED
"""
import json
import os
import sys

import numpy as np

from psf_os import ising2d as I

jd, runs, ansf, bad, seed = sys.argv[1:6]
bad = {int(x) for x in bad.split(",") if x}
ans = json.load(open(ansf))["answers"]
rng = np.random.default_rng(int(seed))
man = json.load(open(os.path.join(jd, "manifest.json")))
rows = []
for p in man["pubs"]:
    rec = json.load(open(os.path.join(runs, man["cells"][p["cell"]]["name"] + ".json")))
    pt = rec["points"][p["point"]]
    kind = rec.get("psfos_job", {}).get("kind")
    if kind in ("ising2d", "mirror2d", "repair2d"):
        tx = float(rec["psfos_job"].get("theta_x", 0.53))
        z = np.array(ans[str(pt["t"])] if kind != "mirror2d" and tx > 0 else [0.98] * len(I.QUBITS), float)
        mp = rec.get(f"mapping_{pt.get('arm')}") or rec["mapping"]
        for k, q in enumerate(I.QUBITS):
            if mp[str(q)] in bad:
                z[k] -= 0.4
        b = (rng.random((rec["shots"], len(z))) < (1 - z) / 2).astype(int)
    else:
        b = np.zeros((rec["shots"], 40), int)
    keys, cnt = np.unique(b[:, ::-1], axis=0, return_counts=True)
    rows.append(dict(counts={"".join(map(str, k)): int(c) for k, c in zip(keys, cnt)}))
json.dump(dict(rows=rows), open(os.path.join(jd, "raw_counts.json"), "w"))
print(f"{len(rows)} synthetic rows, bad {sorted(bad)}")
