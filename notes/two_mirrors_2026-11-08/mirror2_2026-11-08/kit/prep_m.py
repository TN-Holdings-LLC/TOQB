"""Cut the Ising A mirror circuits for theta 0.4, 0.6, 0.8 at t 1, 3, 6 (place 3) out of the fez job (read only)."""
import json, sys
from qiskit import qpy
R, out = sys.argv[1], sys.argv[2]
d = f"{R}/results/os3d-physA-2026-11-07/j2_4x2x2"
want = [f"p2d_g3d3_th{th}_t{t}_mirror" for th in ("04", "06", "08") for t in (1, 3, 6)]
man = json.load(open(f"{d}/job/manifest.json"))
names = [man["cells"][p["cell"]]["name"] for p in man["pubs"]]
circs = qpy.load(open(f"{d}/job/circuits.qpy", "rb"))
with open(f"{out}/isingA_m9.qpy", "wb") as f:
    qpy.dump([circs[names.index(n)] for n in want], f)
json.dump(want, open(f"{out}/isingA_m9_names.json", "w"))
print(len(want))
