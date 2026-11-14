"""Fixed before the run (prereg/xxcone_2026-11-14.md): the gap g = r(N = 33) - r(N = 81) on the same qubits, by block.

The N = 33 chain must be the first 33 qubits of the N = 81 chain, in order (checked here; otherwise STOP). Blocks are
positions in the N = 33 chain: far 0-10 (farthest from where the N = 81 chain continues), mid 11-21, near 22-32.
r = sum z e / sum e^2 over the block's qubits, from each job's scores.json (gpu/hub_score.py).

usage: python notes/xxcone_2026-11-14/cone.py RUN33 RUN81   (folders with build.json and scores.json)
"""
import json
import os
import sys

import numpy as np

BLOCKS = {"far": range(0, 11), "mid": range(11, 22), "near": range(22, 33)}
STEPS = (2, 4, 8, 12, 16)


def main(d33, d81):
    lab = {33: json.load(open(os.path.join(d33, "build.json")))["chains"]["33"]["labels"],
           81: json.load(open(os.path.join(d81, "build.json")))["chains"]["81"]["labels"]}
    if lab[81][:33] != lab[33]:
        raise SystemExit("STOP: the N = 33 chain is not the first 33 qubits of the N = 81 chain")
    sc = {33: json.load(open(os.path.join(d33, "scores.json")))["circuits"],
          81: json.load(open(os.path.join(d81, "scores.json")))["circuits"]}
    out = {}
    for th, name in (("0785", "pi4"), ("1571", "pi2")):
        for s in STEPS:
            for b, idx in BLOCKS.items():
                rr = []
                for n in (33, 81):
                    c = sc[n][f"N{n}_th{th}_s{s:02d}"]
                    z, e = np.array(c["z"])[list(idx)], np.array(c["exact"])[list(idx)]
                    rr.append(float(np.dot(z, e) / np.dot(e, e)))
                out[f"{name}_s{s:02d}_{b}"] = dict(r33=rr[0], r81=rr[1], gap=rr[0] - rr[1])
    g = lambda th, s, b: out[f"{th}_s{s:02d}_{b}"]["gap"]
    for th in ("pi4", "pi2"):
        print(th, " ".join(f"s{s:02d}: far {g(th, s, 'far'):+.3f} mid {g(th, s, 'mid'):+.3f} near {g(th, s, 'near'):+.3f} |"
                           for s in STEPS))
    p1 = all(abs(g("pi4", s, "far")) <= 0.03 for s in STEPS)
    p2 = all(g("pi4", s, "near") - g("pi4", s, "far") >= 0.05 for s in (4, 8))
    p3 = all(abs(g("pi2", s, "far")) <= 0.03 for s in (2, 4, 8)) and g("pi2", 16, "far") >= 0.03
    for k, v, t in ((1, p1, "pi/4 far block: |gap| <= 0.03 at every depth"),
                    (2, p2, "pi/4 at 16 and 32 layers: near gap - far gap >= 0.05"),
                    (3, p3, "pi/2 far block: |gap| <= 0.03 up to 32 layers, gap >= 0.03 at 64 layers")):
        print(f"prediction {k} ({t}): {'held' if v else 'FAILED'}")
    json.dump(dict(blocks=out, p1=p1, p2=p2, p3=p3), open("cone_result.json", "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
