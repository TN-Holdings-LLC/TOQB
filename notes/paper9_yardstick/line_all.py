"""Every recorded device result with an exact answer, on one yardstick (desk, no device; written 2026-11-14 after the
results): does "r >= 1 - 1/sqrt 2 = 0.293" tell whether the result READS (MSE <= half the mean square answer)?

r = sum z e / sum e^2 over the circuit's measured values (z) and exact values (e). With a pure shrink z = r e the two
agree exactly; a miss means the error that is not a shrink (rest = MSE / mean square - (1 - r)^2) decided the verdict.
Families: the hub_score records (XX chains, Hubbard, the dt test), the twin test's user circuits, the daily record,
the 11-04 practice tests, and the dual-unitary curves (one verdict per curve: r from the correlation points).
usage: python notes/paper9_yardstick/line_all.py   (from the repository root; writes line_all.json)
"""
import glob
import json
import math
import os

import numpy as np

LINE = 1 - 1 / math.sqrt(2)
rows = []


def add(family, record, item, r, mse, msq, reads):
    rest = mse / msq - (1 - r) ** 2
    rows.append(dict(family=family, record=record, item=item, r=r, ratio=mse / msq, rest=rest,
                     reads=reads, line=r >= LINE, match=(r >= LINE) == reads))


# hub_score records: per circuit z, exact, mse, mean_square, reads
for f in sorted(glob.glob("results/*/*/scores*.json")):
    if "twin" in f:
        continue
    j = json.load(open(f))
    if not isinstance(j, dict) or "circuits" not in j or not isinstance(j["circuits"], dict):
        continue
    for t, c in j["circuits"].items():
        if not isinstance(c, dict) or not {"z", "exact", "mse", "mean_square", "reads"} <= set(c):
            continue
        z, e = np.array(c["z"]), np.array(c["exact"])
        if np.dot(e, e) == 0:
            continue
        fam = "XX chain" if t.startswith("N") and "_th" in t else "Hubbard"
        add(fam, f.split("/")[1] + ("/" + os.path.basename(f) if "continuum" in f else ""), f"{f.split('/')[2]}:{t}",
            float(np.dot(z, e) / np.dot(e, e)), c["mse"], c["mean_square"], c["reads"] == "READS")

# twin test, user circuits
for f in glob.glob("results/twin-2026-11-13/*/twin_scores.json"):
    for t, p in json.load(open(f))["pairs"].items():
        u = p["user"]
        add("XX chain" if t.startswith("N") else "Hubbard", "twin-2026-11-13", t, u["r"], u["mse"], u["mean_square"],
            u["reads"] == "READS")

# daily record and practice tests (per problem: z, exact by qubit or slope)
for f in sorted(glob.glob("results/daily/2026-*/*/run/scores.json")):
    for pid, p in json.load(open(f))["problems"].items():
        add("daily (P4 chain)", "daily/" + f.split("/")[2] + "/" + f.split("/")[3], pid, p["slope"], p["mse"],
            p["mean_square_answer"], p["reads"] == "READS")
for f in sorted(glob.glob("results/practice*-2026-11-04/run/scores.json")):
    for pid, p in json.load(open(f))["problems"].items():
        if not {"z", "exact"} <= set(p):
            continue
        z, e = np.array(list(p["z"].values()) if isinstance(p["z"], dict) else p["z"]), \
            np.array(list(p["exact"].values()) if isinstance(p["exact"], dict) else p["exact"])
        mse, msq = float(np.mean((z - e) ** 2)), float(np.mean(e ** 2))
        if msq == 0:
            continue
        add("practice (2D)", f.split("/")[1], pid, float(np.dot(z, e) / np.dot(e, e)), mse, msq, mse <= msq / 2)

# dual-unitary curves: one verdict per curve
for f in sorted(glob.glob("results/du*-2026-11-*/*/run/scores.json")):
    j = json.load(open(f))
    pts = j["points"].values()
    on, ex = np.array([p["on"] for p in pts]), np.array([p["exact"] for p in pts])
    add("dual-unitary (curve)", f.split("/")[1] + "/" + f.split("/")[2], "curve", float(np.dot(on, ex) / np.dot(ex, ex)),
        j["mse"], j["mean_square_exact"], j["reads"] == "READS")

json.dump(rows, open("notes/paper9_yardstick/line_all.json", "w"), indent=1)
print(f"{len(rows)} results; the line matches the verdict in {sum(r['match'] for r in rows)}")
for fam in sorted({r["family"] for r in rows}):
    rr = [r for r in rows if r["family"] == fam]
    print(f"  {fam:22s} {sum(r['match'] for r in rr):3d} of {len(rr):3d}   reads {sum(r['reads'] for r in rr)}")
print("misses (family, record, item, r, MSE/msq, rest, verdict):")
for r in rows:
    if not r["match"]:
        print(f"  {r['family']:20s} {r['record']:34s} {r['item']:28s} r {r['r']:.3f} ratio {r['ratio']:.3f} rest {r['rest']:+.3f} "
              f"{'READS' if r['reads'] else 'DOES NOT READ'}")
