"""Flow L summary (2026-10-28): reads the raw rows of main/ and amend1_L24/ (and flow J's n = 20, L = 16 rows) and
writes depth_data.csv and summary.txt in this folder.   usage: python analyze.py"""
import csv
import json
import os

import numpy as np

H = os.path.dirname(os.path.abspath(__file__))


def rows(path):
    return [json.loads(l) for l in open(os.path.join(H, path))]


real = {8: rows("main/real_L8.jsonl"), 16: rows("../flow-j-2026-10-27/n20.jsonl"), 24: rows("amend1_L24/real_L24.jsonl")}
cliff = {}
for r in rows("main/clifford.jsonl") + rows("amend1_L24/clifford_L24.jsonl"):
    cliff.setdefault(r["L"], []).append(r)
cliff = dict(sorted(cliff.items()))
src = {8: "main/real_L8.jsonl", 16: "flow-j-2026-10-27/n20.jsonl (model 0 re-run equal: main/check.jsonl)",
       24: "amend1_L24/real_L24.jsonl"}

with open(os.path.join(H, "depth_data.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["measure", "L", "model_or_seed", "lam", "se", "corr", "q2", "us", "sim_seconds", "source"])
    for L, rs in real.items():
        for r in rs:
            w.writerow(["real", L, r.get("mseed", 0), r["lam"], "", r["corr"], r["q2"], r["us"], r["s"], src[L]])
    for L, rs in cliff.items():
        for r in rs:
            w.writerow(["clifford", L, r["seed"], r["lam_c"], r["se"], "", r["q2"], r["us"], r["s"],
                        "amend1_L24/clifford_L24.jsonl" if L == 24 else "main/clifford.jsonl"])


def ms(v):
    v = np.asarray(v, float)
    return v.mean(), v.std(ddof=1) / np.sqrt(len(v))


out = ["Flow L summary (n = 20, fold:rule, ibm_kingston 2026-10-24 twin, P = 24, T = 256; four models / seeds each)", ""]
out.append("Bridge (declared rule: AGREE if |mean C - mean real| <= 2 sqrt(SE_C^2 + SE_r^2), SE = sd of four / 2)")
out.append(f"{'L':>4} {'real':>8} {'SE':>7} {'lam_C':>8} {'SE':>7} {'diff':>7} {'2 SE':>7} {'ratio':>6}  verdict")
mean_r, mean_c = {}, {}
for L in cliff:
    mc, sc = ms([r["lam_c"] for r in cliff[L]])
    mean_c[L] = mc
    if L in real:
        mr, sr = ms([r["lam"] for r in real[L]])
        mean_r[L] = mr
        d, t = mr - mc, 2 * np.hypot(sr, sc)
        out.append(f"{L:>4} {mr:8.4f} {sr:7.4f} {mc:8.4f} {sc:7.4f} {d:7.4f} {t:7.4f} {mc / mr:6.3f}  "
                   f"{'AGREE' if abs(d) <= t else 'DIFFER'}")
    else:
        out.append(f"{L:>4} {'-':>8} {'-':>7} {mc:8.4f} {sc:7.4f}   (lam_C / SE = {mc / sc:.1f})")
out += ["", "Per-layer factor (mean(L2) / mean(L1))^(1 / (L2 - L1))"]
for name, m in (("lam_C", mean_c), ("real", mean_r)):
    Ls = [L for L in m if m[L] > 0]
    out.append(name + ": " + ", ".join(f"L {a}-{b}: {(m[b] / m[a]) ** (1 / (b - a)):.4f}" for a, b in zip(Ls, Ls[1:])))
out += ["", "Shots relative to lam = 1 (1 / mean^2): " + ", ".join(
    f"L {L}: C {1 / mean_c[L] ** 2:.1f}" + (f" / real {1 / mean_r[L] ** 2:.2f}" if L in mean_r else "")
    for L in mean_c if mean_c[L] > 0.03)]
open(os.path.join(H, "summary.txt"), "w").write("\n".join(out) + "\n")
print("\n".join(out))
