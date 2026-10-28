"""Flow M summary (2026-10-28): reads run/kising.jsonl and flow L's depth_data.csv; writes summary.txt and
depth_figure_lm.png/.pdf (classifier, Clifford, kicked Ising on one plot).   usage: python analyze.py"""
import csv
import json
import os

import numpy as np

H = os.path.dirname(os.path.abspath(__file__))
K = {}
for l in open(os.path.join(H, "run/kising.jsonl")):
    r = json.loads(l)
    K.setdefault(r["L"], []).append(r)
FL = {}
for r in csv.DictReader(open(os.path.join(H, "../flow-l-2026-10-28/depth_data.csv"))):
    FL.setdefault((r["measure"], int(r["L"])), []).append(float(r["lam"]))


def ms(v):
    v = np.asarray(v, float)
    return float(v.mean()), float(v.std(ddof=1) / np.sqrt(len(v)))


out = ["Flow M summary (kicked Ising ring, J = pi/4, h = 0.6, n = 20, fold:rule, kingston 2026-10-24 twin; four seeds of",
       "24 inputs each, T = 256). SE = sd of four / 2. Flow L means for comparison.", "",
       f"{'L':>4} {'lam_K':>8} {'SE':>7} {'corr':>11} {'sd z0':>11} {'q2':>5} {'us':>7} | {'lam_C':>7} {'real':>7}  side"]
mk = {}
for L in sorted(K):
    m, se = ms([r["lam"] for r in K[L]])
    mk[L] = m
    c = [r["corr"] for r in K[L]]
    sdz = [r["sd_noiseless"] for r in K[L]]
    mc, sc = ms(FL[("clifford", L)])
    line = (f"{L:>4} {m:8.4f} {se:7.4f} {min(c):5.2f}-{max(c):4.2f} {min(sdz):5.2f}-{max(sdz):4.2f} {K[L][0]['q2']:>5} "
            f"{K[L][0]['us']:>7} | {mc:7.4f}")
    if ("real", L) in FL:
        mr, sr = ms(FL[("real", L)])
        side = "CLIFFORD-SIDE" if abs(m - mc) < abs(m - mr) else "CLASSIFIER-SIDE"
        line += (f" {mr:7.4f}  {side}; |K-C| {abs(m - mc):.3f} (2 SE {2 * np.hypot(se, sc):.3f}), "
                 f"|K-real| {abs(m - mr):.3f} (2 SE {2 * np.hypot(se, sr):.3f})")
    else:
        line += f" {'-':>7}  |K-C| {abs(m - mc):.3f} (2 SE {2 * np.hypot(se, sc):.3f}); lam_K / SE {m / se:.1f}"
    out.append(line)
Ls = sorted(mk)
out += ["", "Per-layer factor of lam_K: " + ", ".join(f"L {a}-{b}: {(mk[b] / mk[a]) ** (1 / (b - a)):.4f}"
                                                     for a, b in zip(Ls, Ls[1:]))]
out.append("Shots relative to lam = 1 (1/lam^2): " + ", ".join(f"L {L}: {1 / mk[L] ** 2:.0f}" for L in Ls))
open(os.path.join(H, "summary.txt"), "w").write("\n".join(out) + "\n")
print("\n".join(out))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
fig, a = plt.subplots(figsize=(6.4, 3.8))
a.axhline(0, color="#52514e", lw=0.8)
for key, col, mk_, lab in (("real", "#eb6834", "s", "random classifier, real angles (flow L)"),
                           ("clifford", "#2a78d6", "o", "random Clifford (flow L)")):
    xs = sorted(L for (k, L) in FL if k == key)
    a.plot(xs, [np.mean(FL[(key, L)]) for L in xs], color=col, marker=mk_, lw=2, label=lab)
a.plot(Ls, [mk[L] for L in Ls], color="#1a8a5a", marker="D", lw=2, label="kicked Ising, h = 0.6 (flow M)")
for L in Ls:
    a.scatter([L] * 4, [r["lam"] for r in K[L]], s=10, color="#1a8a5a", alpha=0.4, lw=0)
a.set_xticks([8, 16, 24, 50, 100]); a.set_xlabel("depth L (layers)"); a.set_ylabel("kept signal λ")
a.set_title("n = 20 ring, fold:rule, ibm_kingston 2026-10-24 day twin — model results, not a device", fontsize=8.5,
            loc="left")
a.legend(frameon=False, fontsize=8)
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(H, f"depth_figure_lm.{ext}"), dpi=200, bbox_inches="tight")
