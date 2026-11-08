"""Cut the mirror and floor circuits (and keep the device's mirror/floor means) out of the two fez jobs (read only)."""
import json, os, sys
from qiskit import qpy
R, out = sys.argv[1], sys.argv[2]
sets = {
    "heisB_mf": (f"{R}/results/os3d-heisB-2026-11-08/fez", [f"p2d_h3d0_t{t}_mirror" for t in range(1, 5)] + ["p2d_h3d0_t1_floor"]),
    "isingA_mf": (f"{R}/results/os3d-physA-2026-11-07/j2_4x2x2", [f"p2d_g3d3_th06_t{t}_mirror" for t in range(1, 7)] + ["p2d_g3d3_th06_t1_floor"]),
}
for key, (d, want) in sets.items():
    man = json.load(open(f"{d}/job/manifest.json"))
    names = [man["cells"][p["cell"]]["name"] for p in man["pubs"]]
    circs = qpy.load(open(f"{d}/job/circuits.qpy", "rb"))
    with open(f"{out}/{key}.qpy", "wb") as f:
        qpy.dump([circs[names.index(n)] for n in want], f)
    json.dump(want, open(f"{out}/{key}_names.json", "w"))
    print(key, len(want))
