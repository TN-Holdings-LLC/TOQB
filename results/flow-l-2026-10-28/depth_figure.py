"""Depth figure of flow L (drawn by the workplace 2026-10-28, revised at home the same day: all four L = 100 seeds,
the L = 24 bridge of amendment 1, values from the raw rows, "below the real-angle lam at L = 8-24" in place of "lower
bound"). Measured values only.   usage: python depth_figure.py   (reads depth_data.csv, writes depth_figure.png/.pdf)"""
import csv
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

H = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(H, "depth_data.csv"))))
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})


def series(m):
    d = {}
    for r in rows:
        if r["measure"] == m:
            d.setdefault(int(r["L"]), []).append((float(r["lam"]), float(r["sim_seconds"])))
    return dict(sorted(d.items()))


C, R = series("clifford"), series("real")
mean = lambda d, L: float(np.mean([v[0] for v in d[L]]))
sem = lambda d, L: float(np.std([v[0] for v in d[L]], ddof=1) / np.sqrt(len(d[L])))
TICKS = [8, 16, 24, 50, 100]
fig, ax = plt.subplots(1, 3, figsize=(11, 3.6), gridspec_kw={"wspace": 0.38})

a = ax[0]
a.axhline(0, color=INK2, lw=0.8)
for d, col, mk, lab in ((C, BLUE, "o", "Clifford test"), (R, ORANGE, "s", "real angles")):
    Ls = list(d)
    for L in Ls:
        a.scatter([L] * len(d[L]), [v[0] for v in d[L]], s=12, color=col, alpha=0.35, marker=mk, lw=0, zorder=2)
    a.plot(Ls, [mean(d, L) for L in Ls], color=col, lw=2, marker=mk, ms=6, zorder=3, label=lab)
a.annotate("real angles measured to L = 24;\ndeeper, the noiseless outputs\ncollapse and λ cannot be fitted",
           (24, mean(R, 24)), color=INK, fontsize=8, xytext=(31, 0.80))
for L in (8, 16, 24):
    a.annotate(f"{mean(C, L) / mean(R, L):.2f}", (L, mean(C, L)), textcoords="offset points", xytext=(-3, -17), ha="center",
               fontsize=7.5, color=BLUE)
a.set_xlabel("depth L (layers)"); a.set_ylabel("kept signal λ")
a.set_title("A  Kept signal falls with depth", loc="left", fontsize=10, color=INK)
a.set_ylim(-0.08, 1.02); a.set_xticks(TICKS); a.grid(axis="y", color=GRID, lw=0.6)
a.legend(frameon=False, fontsize=8, loc="upper right", bbox_to_anchor=(1.02, 0.62))

b = ax[1]
for d, col, mk, lab in ((C, BLUE, "o", "Clifford test"), (R, ORANGE, "s", "real angles")):
    Ls = [L for L in d if mean(d, L) > 0.03]
    rel = [1 / mean(d, L) ** 2 for L in Ls]
    b.plot(Ls, rel, color=col, lw=2, marker=mk, ms=6, label=lab)
    for L, y in zip(Ls, rel):
        if L >= 24:
            b.annotate(f"≈{y:.1f}×" if y < 10 else f"≈{y:.0f}×", (L, y), textcoords="offset points", xytext=(6, -3),
                       fontsize=8, color=INK)
b.annotate(f"L = 100: no signal resolved\n(λ_C = {mean(C, 100):+.3f} ± {sem(C, 100):.3f})", (102, 3), fontsize=8,
           color=INK2, ha="right")
b.set_ylim(0.8, 1000); b.set_yscale("log")
b.set_xlabel("depth L (layers)"); b.set_ylabel("shots needed, relative to λ = 1  (1/λ²)")
b.set_title("B  Cost of reading it out", loc="left", fontsize=10, color=INK)
b.set_xticks(TICKS); b.set_xlim(0, 105); b.grid(axis="y", color=GRID, lw=0.6, which="major")
b.legend(frameon=False, fontsize=8, loc="center left", bbox_to_anchor=(0.0, 0.62))

c = ax[2]
Ls = list(C)
t = [float(np.mean([v[1] for v in C[L]])) for L in Ls]
c.plot(Ls, t, color=BLUE, lw=2, marker="o", ms=6)
for L, y in zip(Ls, t):
    if L >= 50:
        c.annotate(f"{y / 60:.1f} min", (L, y), textcoords="offset points", xytext=(-8, -12), fontsize=8, color=INK,
                   ha="right")
c.annotate(f"{t[0] / 60:.1f}-{t[2] / 60:.1f} min\n(L = 8-24)", (24, t[2]), textcoords="offset points",
           xytext=(12, -18), fontsize=8, color=INK)
c.set_xlabel("depth L (layers)"); c.set_ylabel("twin simulation time per Clifford set (s)")
c.set_title("C  Classical simulation is easy here", loc="left", fontsize=10, color=INK)
c.set_xticks(TICKS); c.set_ylim(0, 1000); c.grid(axis="y", color=GRID, lw=0.6)
c.text(0.02, 0.98, "n = 20, one H100, 24 circuits × 256 trajectories\n(about linear in L; n not varied here)",
       transform=c.transAxes, va="top", ha="left", fontsize=8, color=INK2)

fig.suptitle("Flow L: n = 20 ring on one 20-qubit cycle, ibm_kingston 2026-10-24 day twin  —  model results, not a device",
             x=0.01, ha="left", fontsize=10.5, color=INK, y=1.03)
fig.text(0.01, -0.13, "Points: four random classifiers (real angles; models 0-3) or four seeds of 24 random Clifford circuits; "
         "lines: their mean; numbers in A: ratio λ_C / λ. Real-angle L = 16 from flow J (model 0 re-run equal); L = 24 "
         "under amendment 1. Clifford test: noiseless value exactly ±1 by construction; circuits are drawn anew per L. It lies "
         "below the real-angle λ at L = 8-24, by a ratio that falls with depth (0.92, 0.75, 0.56).", fontsize=7.5,
         color=INK2, wrap=True)
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(H, f"depth_figure.{ext}"), dpi=200, bbox_inches="tight")
print("written depth_figure.png/.pdf")
