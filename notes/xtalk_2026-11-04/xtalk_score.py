"""Score the crosstalk job (draft; not declared): reads the finished job (psf_os.job.read), the sealed answers
(xtalk_answers.py) and runs psf_os.crosstalk2d.analyse (bootstrap 200, seed 0). Writes the estimates, SEs and the
proposed verdicts; the sentinel is judged first by the usual M6 reader and is not repeated here.

usage: PYTHONPATH=<psf-os> python notes/xtalk_2026-11-04/xtalk_score.py JOB_DIR RUNS_DIR ANSWERS.json OUT.json
"""
import json
import os
import sys

from psf_os import crosstalk2d as X
from psf_os import job as J

job_dir, runs, ans_f, out_f = sys.argv[1:5]
if os.path.exists(out_f):
    raise SystemExit(f"STOP: {out_f} exists")
ans = json.load(open(ans_f))
cells, qubits, edges, flipped = {}, None, None, None
for name, (rec, cc) in J.read(job_dir, runs).items():
    kind = rec.get("psfos_job", {}).get("kind")
    if kind not in ("xtalk_split", "xtalk_mirror", "xtalk_readout"):
        continue
    if qubits is None:
        qubits, edges = rec["qubits"], [tuple(e) for e in rec["edges"]]
    if rec["qubits"] != qubits:
        raise SystemExit(f"STOP: {name} is on another lattice")
    for p in rec["points"]:
        counts = cc[(p["input"], "z")]
        if kind == "xtalk_split":
            cells[(p["arm"], float(rec["psfos_job"]["theta"]), p["t"])] = counts
        elif kind == "xtalk_mirror":
            cells[("m" + p["arm"], p["t"])] = counts
        else:
            cells[("pat", p["pattern"])] = counts
            flipped = rec["flipped"]
if ans["qubits"] != qubits:
    raise SystemExit("STOP: the answers are for another lattice")
exact = {}
for th, byt in ans["answers"].items():
    exact[float(th)] = {int(t): dict(z=v["z"], pairs={tuple(int(x) for x in k.split(",")): tuple(tr)
                                                       for k, tr in v["pairs"].items()}) for t, v in byt.items()}
r = X.analyse(cells, exact, qubits, edges, flipped, theta_q1=0.4, nboot=200, seed=0)
json.dump(dict(job=os.path.basename(os.path.normpath(job_dir)), **r), open(out_f, "w"), indent=1)
for k, v in r["verdicts"].items():
    print(k, v)
