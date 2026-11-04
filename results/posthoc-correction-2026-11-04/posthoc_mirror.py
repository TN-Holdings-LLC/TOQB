"""Post-hoc reference on fez: floor (readout) and mirror (gate) rescaling, both from our own measurements."""
import json, sys
import numpy as np
sys.path.insert(0, "gpu")
from psf_os import ising2d as I
import p6_score as P

d = "results/p6-device-2026-11-04"
sc = I.score(f"{d}/V/job", f"{d}/V/runs"); fl = sc["0"]
def F(t):
    f1, f5, f9 = (np.array(fl[k]) for k in (1, 5, 9))
    return f1 + (f5 - f1) * (t - 1) / 4 if t <= 5 else f5 + (f9 - f5) * (t - 5) / 4
mir = json.load(open("results/os2d-2026-11-04/scores.json"))["mirror_by_t"]
lnG = {t: 0.5 * np.log(np.clip(np.array(mir[str(t)]) / np.clip(F(2 * t), 0.05, None), 1e-3, 1.0)) for t in (3, 5)}
a_q = (lnG[3] / 3 + lnG[5] / 5) / 2
a_g = np.median(a_q)
print("gate decay per step: median", round(float(np.exp(a_g)), 4), "range", np.round(np.exp(np.percentile(a_q, [5, 95])), 3))
z0 = np.mean([fl[t] for t in (1, 5, 9)], axis=0); med = np.median(z0); mad = np.median(abs(z0 - med))
keep = z0 >= med - max(5 * 1.4826 * mad, 0.05)
for tx in ("0.53", "0.3", "0.8"):
    ans = P.answers(float(tx)); raw = {t: np.array(sc[tx][t]) for t in range(1, 10)}
    meths = {"raw": raw, "floor": {t: raw[t] / F(t) for t in raw},
             "floor+gate(q)": {t: raw[t] / (F(t) * np.exp(a_q * t)) for t in raw},
             "floor+gate(med)": {t: raw[t] / (F(t) * np.exp(a_g * t)) for t in raw}}
    base = None
    for name, m in meths.items():
        for k, lab in ((None, ""), (keep, "+R")):
            j = P.judge({t: list(m[t]) for t in m}, ans, k); base = base or j["mse"]
            print(f" tx {tx:4} {name+lab:18} MSE {j['mse']:.4f} ratio {j['mse']/base:.2f} diff "
                  f"{[round(j['rows'][t]['diff'], 3) for t in (1, 3, 5, 7, 9)]} {j['agrees']}")
