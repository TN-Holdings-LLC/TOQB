"""Score a utility job (gpu/utility_build.py) against its answers; written before any run (home, 2026-11-10).

Per observable (17 values of theta_h): the device value is the mean parity of the measured bits (the circuit reads its
X / Y sites through the basis change), SE = sqrt((1 - z^2) / shots).
  READS if MSE <= mean square of the exact values / 2 (over the 17 points);
  per point AGREES if |z - e| <= 0.05; counted.
Beside, never judged: retention z / e where |e| >= 0.1; the floor's and the mirror's parity (exactly +1 without
noise); the sentinel; CZ per circuit. IBM's published (mitigated) values are not used.
usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/utility_score.py OUT ANSWERS.json   (writes OUT/scores.json)
"""
import json
import math
import os
import sys

import numpy as np


def parity(counts):
    tot = sum(counts.values())
    return sum(v * (1 - 2 * (k.replace(" ", "").count("1") % 2)) for k, v in counts.items()) / tot, tot


def main(out, ans_file):
    from psf_os import job as J
    from psf_os import sentinel
    rep = json.load(open(os.path.join(out, "report.json")))
    answers = json.load(open(ans_file))
    jd, runs = os.path.join(out, "job"), os.path.join(out, "runs")
    cells = J.read(jd, runs)
    res = dict(device=rep["device"], sentinel=sentinel.verdict(jd, runs)["status"], observables={})
    for name, r in rep["observables"].items():
        if r["embedding"] is None:
            res["observables"][name] = dict(verdict="NOT BUILT")
            continue
        rec, cc = cells[f"u_{name}"]
        pts = []
        for p in rec["points"]:
            z, S = parity(cc[(p["input"], p["setting"])])
            k = int(p["input"][1:])
            e = answers[f"{name}_k{k:02d}"]
            pts.append(dict(k=k, z=z, se=math.sqrt(max(1 - z * z, 0) / S), exact=e, agrees=abs(z - e) <= 0.05,
                            retention=z / e if abs(e) >= 0.1 else None))
        z = np.array([p["z"] for p in pts])
        e = np.array([p["exact"] for p in pts])
        mse, msq = float(np.mean((z - e) ** 2)), float(np.mean(e ** 2))
        fl = parity(next(iter(cells[f"u_{name}_floor"][1].values())))[0]
        mi = parity(next(iter(cells[f"u_{name}_mirror"][1].values())))[0]
        res["observables"][name] = dict(embedding=r["embedding"], cz=r["cz_per_circuit"], mse=mse, mean_square_exact=msq,
                                        reads="READS" if mse <= msq / 2 else "DOES NOT READ",
                                        agrees=sum(p["agrees"] for p in pts), points=pts, floor=fl, mirror=mi)
    json.dump(res, open(os.path.join(out, "scores.json"), "w"), indent=1)
    print(f"{res['device']}  sentinel {res['sentinel']}")
    for name, r in res["observables"].items():
        if r.get("verdict") == "NOT BUILT":
            print(f"{name}: NOT BUILT")
            continue
        print(f"{name}: embedding {r['embedding']} CZ {r['cz']}  {r['reads']} (MSE {r['mse']:.4f} / mean square "
              f"{r['mean_square_exact']:.4f})  AGREES {r['agrees']}/17  floor {r['floor']:+.3f} mirror {r['mirror']:+.3f}")
        print("   z: " + " ".join(f"{p['z']:+.2f}" for p in r["points"]))
        print("   e: " + " ".join(f"{p['exact']:+.2f}" for p in r["points"]))
    return res


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
