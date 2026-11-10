"""3 (prep): the 4 x 3 x 2 user circuits of both places, fold and line, t 1-4 (compiled, from the job's runs, read
only) into one qpy for the trajectory simulator, with the answers and the device scores."""
import json, shutil, sys
from qiskit import qpy
R, out = sys.argv[1], sys.argv[2]
names, circs = [], []
for c in (0, 1):
    for lay in ("f", "l"):
        for t in (1, 2, 3, 4):
            n = f"p2d_q32{lay}{c}_t{t}"
            (q,) = qpy.load(open(f"{R}/ibm_fez/runs/{n}.qpy", "rb"))
            names.append(n); circs.append(q)
with open(f"{out}/q32.qpy", "wb") as f:
    qpy.dump(circs, f)
json.dump(names, open(f"{out}/q32_names.json", "w"))
shutil.copy(f"{R}/answers/isingL_fez.json", f"{out}/q32_answers.json")
shutil.copy(f"{R}/ibm_fez/scores.json", f"{out}/q32_scores.json")
print(len(names))
