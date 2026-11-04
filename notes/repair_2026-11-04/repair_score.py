"""Score the self-repair test (draft; not declared): job 2's P6 problem on A's and B's copies against the sealed P6
answers, MSE per copy, the bootstrap SE of A - B (shots, 200 resamples, seed 0) and the between-run spread from job 1
(the same circuits on A's copy, if job 1 ran on the same copy): spread = |MSE_A(job 1) - MSE_A(job 2)| / sqrt(2).
Verdict on the ratio B / A (0.8 / 1.25) with the difference beyond 2 x max(shot SE, spread) (owner, 2026-11-04).
Reported: the price (chain log) and the flag lifetime (job 2's floor on A's copy at the excluded qubits).

usage: PYTHONPATH=<psf-os> python repair_score.py JOB1_DIR JOB1_RUNS JOB2_DIR JOB2_RUNS CHAIN.json P6_ANSWERS.json OUT.json
"""
import json
import os
import sys

import numpy as np

from psf_os import ising2d as I
from psf_os import job as J
from psf_os import ledger as Lg
from psf_os import repair2d as Rp
from psf_os.kim import z_values

j1, r1, j2, r2, chainf, ansf, outf = sys.argv[1:8]
if os.path.exists(outf):
    raise SystemExit(f"STOP: {outf} exists")
n = len(I.QUBITS)
ans = {int(t): v for t, v in json.load(open(ansf))["answers"].items()}
log = json.load(open(chainf))
cells, floorA, copy2 = {}, [], log["A"]["mapping"]
for name, (rec, cc) in J.read(j2, r2).items():
    if rec.get("psfos_job", {}).get("kind") != "repair2d":
        continue
    for p in rec["points"]:
        c = cc[(p["input"], "z")]
        if float(rec["psfos_job"]["theta_x"]) > 0:
            cells[(p["arm"], p["t"])] = c
        elif p["arm"] == "A":
            floorA.append(z_values(c, n))
exact = {t: ans[t] for t in sorted({t for _, t in cells})}
z1, copy1 = {}, None
for name, (rec, cc) in J.read(j1, r1).items():
    if rec.get("psfos_job", {}).get("kind") == "ising2d" and float(rec["psfos_job"].get("theta_x", 0.53)) > 0:
        copy1 = {int(k): v for k, v in rec["mapping"].items()}
        z1 = {p["t"]: z_values(cc[(p["input"], "z")], n)[0] for p in rec["points"]}
same = copy1 == {int(k): v for k, v in copy2.items()}
zA2 = {t: z_values(cells[("A", t)], n)[0] for t in exact}
spread = abs(Rp.mse({t: z1[t] for t in exact if t in z1}, exact) - Rp.mse(zA2, exact)) / np.sqrt(2) if same else None
s = Rp.score(cells, exact, n, nboot=200, seed=0, spread=spread)
z0 = np.mean([z for z, _ in floorA], axis=0)
se0 = np.sqrt(np.sum([np.square(e) for _, e in floorA], axis=0)) / len(floorA)
phys = [copy2[str(q)] if isinstance(next(iter(copy2)), str) else copy2[q] for q in I.QUBITS]
rd, line = Lg.read_floor(phys, z0, se0)
life = {q: v for q, v, *_ in rd if q in {int(x) for x in log["excluded"]}}
out = dict(score=s, spread_from_job1=spread, job1_same_copy_as_A=same, price=log["price"], status=log["status"],
           lifetime_job2_floor_on_A=life, job2_floor_line_A=line)
json.dump(out, open(outf, "w"), indent=1, default=str)
print(json.dumps({k: out[k] for k in ("status", "price", "lifetime_job2_floor_on_A")}, default=str))
print(f"MSE A {s['mse_A']:.5f}, B {s['mse_B']:.5f}, ratio {s['ratio']:.2f}; shot SE {s['se_diff']:.5f}, spread "
      f"{spread if spread is None else round(spread, 5)}; verdict {s['verdict']}")
