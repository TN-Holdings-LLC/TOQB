"""D inputs: kingston places 1 and 2, old and line, t 3 and 4, user and mirror circuits (compiled, from the job's
runs, read only), with the answers and the device's scores."""
import json, sys, shutil
from qiskit import qpy
R, out = sys.argv[1], sys.argv[2]
names, circs = [], []
for c in (1, 2):
    for h in ("d", "l"):
        for t in (3, 4):
            for suf in ("", "_mirror"):
                n = f"p2d_h3{h}{c}_t{t}{suf}"
                (q,) = qpy.load(open(f"{R}/kingston/runs/{n}.qpy", "rb"))
                names.append(n); circs.append(q)
with open(f"{out}/kng.qpy", "wb") as f:
    qpy.dump(circs, f)
json.dump(names, open(f"{out}/kng_names.json", "w"))
shutil.copy(f"{R}/kingston/scores.json", f"{out}/kng_scores.json")
import glob
ans = sorted(glob.glob(f"{R}/answers/*.json"))
print("answers files", ans)
shutil.copy(ans[0], f"{out}/kng_answers.json")
print(len(names))
