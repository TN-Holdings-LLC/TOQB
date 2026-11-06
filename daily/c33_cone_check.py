"""Independent check of the C33 answers at t >= 10 (D05, D10, D15, D20, D27, D32; task T's proposal 5, task W): each
site's <X> from its own backward light cone of the user's circuit (gpu/daily_answers.py cones, at most 33 qubits, one
GPU), against the answers sealed on 11-05 and released (results/daily-pool-2026-11-05/released/<ID>.json), which were
computed from the whole 2^33 state. Two different computations of the same circuit; tolerance 1e-4 (single precision).

usage (pod): python daily/c33_cone_check.py RELEASED_DIR OUT.json [cupy|numpy]
"""
from __future__ import annotations

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "gpu"))
sys.path.insert(0, os.path.join(HERE, ".."))
import daily_answers as A  # noqa: E402

from daily import pool as P  # noqa: E402

IDS = ["D05", "D10", "D15", "D20", "D27", "D32"]  # cheapest first


def main(released, out, backend="cupy"):
    rep = {}
    for pid in IDS:
        t0 = time.time()
        rel = json.load(open(os.path.join(released, f"{pid}.json")))
        r = A.cones(P.problem_circuit(pid), backend, "single")
        done = [q for q, v in r["values"].items() if v is not None]
        d = max(abs(r["values"][q] - rel["values"][str(q)]) for q in done)
        rep[pid] = dict(t=P.entry(pid)[4], sites=len(r["values"]), compared=len(done), cone_max=max(r["cone"].values()),
                        max_diff=float(d), ok=bool(d <= 1e-4), seconds=round(time.time() - t0, 1))
        print(f"{pid} t {rep[pid]['t']}: {len(done)} of {len(r['values'])} sites, largest cone {rep[pid]['cone_max']}, "
              f"max |cone - whole state| {d:.2e}, {time.time() - t0:.0f} s", flush=True)
        json.dump(rep, open(out, "w"), indent=1)
    return rep


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *(sys.argv[3:4] or ["cupy"]))
