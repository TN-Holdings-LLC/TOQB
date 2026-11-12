"""Task C (home, 2026-11-12; owner 10:49 JST "C進めて"): Trotter error of the device's Hubbard circuit beside the
device's own error. The device circuit (notes/hubbard_2026-11-11/hub_cost.py: U 4, J 1, dt 0.25, first order) is
compared with the same circuit at dt / 2, dt / 4, dt / 8 up to the same times J t = 0.5, 1.0, 1.5; the continuum value
is taken by Richardson extrapolation of the two finest (first-order error ~ dt): z0 = 2 z(dt/8) - z(dt/4), with
|z(dt/8) - z0| as its error. Per time: MSE over the 2L qubits of (circuit - continuum).
usage: python trotter.py L [--chi 1024]   (writes trotter_L{L}.json)
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "hubbard_2026-11-11"))
import hub_cost as HC  # noqa: E402

L = int(sys.argv[1])
CHI = int(sys.argv[sys.argv.index("--chi") + 1]) if "--chi" in sys.argv else 1024
TIMES = (0.5, 1.0, 1.5)
FACTORS = (1, 2, 4, 8)
out = {"L": L, "U": HC.U, "z": {}}
for jt in TIMES:
    for f in FACTORS:
        HC.DT = 0.25 / f
        steps = int(round(jt / HC.DT))
        t0 = time.time()
        z, bond, err = HC.run_quimb(HC.blocks(HC.circuit(L, steps)), CHI)
        out["z"][f"{jt}_{f}"] = np.asarray(z).tolist()
        print(f"L {L} Jt {jt} dt 0.25/{f} ({steps} steps): bond {bond}, error estimate {err:.1e}, {time.time() - t0:.0f} s",
              flush=True)
    zs = {f: np.array(out["z"][f"{jt}_{f}"]) for f in FACTORS}
    z0 = 2 * zs[8] - zs[4]
    for f in FACTORS:
        print(f"   dt 0.25/{f}: MSE against the continuum {np.mean((zs[f] - z0) ** 2):.2e}", flush=True)
    print(f"   extrapolation error (dt/8 against continuum) {np.mean((zs[8] - z0) ** 2):.1e}", flush=True)
HC.DT = 0.25
json.dump(out, open(os.path.join(HERE, f"trotter_L{L}.json"), "w"))
