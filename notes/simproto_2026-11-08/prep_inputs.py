"""Cut the circuits to compare out of the two fez device jobs (read only) into small inputs for the POD.
usage: python prep_inputs.py TOQB_CHECKOUT OUT_DIR"""
import io, json, os, sys, shutil
from qiskit import qpy
R, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
sets = {
    "heisB": (f"{R}/results/os3d-heisB-2026-11-08/fez", [f"p2d_h3d0_t{t}" for t in range(1, 5)],
              f"{R}/results/os3d-heisB-2026-11-08/answers/heis_answers_fez.json"),
    "isingA": (f"{R}/results/os3d-physA-2026-11-07/j2_4x2x2",
               [f"p2d_g3d3_th{th}_t{t}" for th in ("04", "06", "08") for t in range(1, 7)],
               f"{R}/results/os3d-physA-2026-11-07/answers/answers_4x2x2.json"),
}
for key, (d, want, ans) in sets.items():
    man = json.load(open(f"{d}/job/manifest.json"))
    names = [man["cells"][p["cell"]]["name"] for p in man["pubs"]]
    circs = qpy.load(open(f"{d}/job/circuits.qpy", "rb"))
    pick = [(n, circs[names.index(n)]) for n in want]
    with open(f"{out}/{key}.qpy", "wb") as f:
        qpy.dump([c for _, c in pick], f)
    json.dump([n for n, _ in pick], open(f"{out}/{key}_names.json", "w"))
    shutil.copy(f"{d}/scores.json", f"{out}/{key}_device_scores.json")
    shutil.copy(ans, f"{out}/{key}_answers.json")
    print(key, len(pick), "circuits", [c.size() for _, c in pick])
shutil.copy(f"{R}/notes/os3d_sim_2026-11-07/sim3d.py", f"{out}/../sim3d.py")
