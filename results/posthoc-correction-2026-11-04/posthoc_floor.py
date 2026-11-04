"""Post-hoc reference: per-qubit floor division (readout of |0> + errors seen by |0>) on the P6 jobs."""
import json, sys
import numpy as np
sys.path.insert(0, "gpu")
from psf_os import ising2d as I
import p6_score as P

def floor_at(fl, t):  # linear in t between the measured floor depths 1, 5, 9
    f1, f5, f9 = (np.array(fl[k]) for k in (1, 5, 9))
    return f1 + (f5 - f1) * (t - 1) / 4 if t <= 5 else f5 + (f9 - f5) * (t - 5) / 4

for d in sys.argv[1:]:
    sc = I.score(f"{d}/V/job", f"{d}/V/runs"); fl = sc["0"]
    z0 = np.mean([fl[t] for t in (1, 5, 9)], axis=0); med = np.median(z0); mad = np.median(abs(z0 - med))
    keep = z0 >= med - max(5 * 1.4826 * mad, 0.05)
    print(d)
    for tx in ("0.53", "0.3", "0.8"):
        ans = P.answers(float(tx))
        raw = {t: np.array(sc[tx][t]) for t in range(1, 10)}
        perq = {t: raw[t] / floor_at(fl, t) for t in range(1, 10)}
        glob = {t: raw[t] / np.mean(floor_at(fl, t)) for t in range(1, 10)}
        out = []
        for name, m, k in (("raw", raw, None), ("raw+R", raw, keep), ("global floor", glob, None),
                           ("per-qubit floor", perq, None), ("per-qubit+R", perq, keep)):
            j = P.judge({t: list(m[t]) for t in m}, ans, k)
            out.append((name, j["mse"], [round(j["rows"][t]["diff"], 3) for t in (1, 3, 5, 7, 9)]))
        base = out[0][1]
        for name, mse, diffs in out:
            print(f"  tx {tx:4} {name:16} MSE {mse:.4f} ratio {mse/base:.2f} diff t1,3,5,7,9 {diffs}")
