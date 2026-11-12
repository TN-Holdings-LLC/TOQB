"""Test helper (workplace, 2026-11-12; not part of the job): noiseless raw_counts.json for an Ohm try-build, so that
gpu/ohm_score.py can be run end to end. User circuits: per-qubit bits sampled independently from the exact <Z> (the
scorer reads per-qubit marginals only); floors and mirrors: all zeros (noiseless); sentinel: a perfect echo."""
import json, os, sys
import numpy as np
from qiskit import qpy
from qiskit_aer import AerSimulator
out, ans_file, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
rng = np.random.default_rng(seed)
job = os.path.join(out, "job")
man = json.load(open(os.path.join(job, "manifest.json")))
circs = qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))
ans = json.load(open(ans_file))["z"]
b = json.load(open(os.path.join(out, "build.json")))
chain = b["chain"]["labels"]
shots = man["shots"]
rows = []
for k, p in enumerate(man["pubs"]):
    cell = man["cells"][p["cell"]]["name"]
    c = circs[k]
    n = c.num_clbits
    if cell.startswith("p2d_") and not cell.endswith(("_floor", "_mirror")):
        tag = cell[4:]
        labels = json.load(open(os.path.join(out, "runs", cell + ".json")))["labels"]   # clbit k = labels[k] (sorted)
        z = np.array([ans[tag][str(q)] for q in labels])
        p1 = (1 - z) / 2
        bits = (rng.random((shots, n)) < p1).astype(int)
        cnt = {}
        for row in bits:
            key = "".join(str(x) for x in row[::-1])
            cnt[key] = cnt.get(key, 0) + 1
    elif cell.startswith("p2d_"):
        cnt = {"0" * n: shots}
    else:   # the ring sentinel: a perfect echo (site signal 1: every bit returns flipped from its input)
        from psf_os.scan import input_bits
        rec = json.load(open(os.path.join(out, "runs", cell + ".json")))
        inp = rec["points"][p["point"]]["input"]
        bits = [1 - x for x in input_bits(inp, n)]
        cnt = {"".join(str(x) for x in bits[::-1]): shots}
    rows.append(dict(counts=cnt))
json.dump(dict(rows=rows), open(os.path.join(job, "raw_counts.json"), "w"))
print("rows", len(rows))
