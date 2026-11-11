"""Paper 8 figures, from the committed records only (home, 2026-11-10; owner 22:05 JST: figures 1-3).

  fig1  decay rate k - cos 2h against h for the dual-unitary chain: N = 51, 71 (kingston), 91 (marrakesh), 91 (fez,
        ruler in both jobs); bars 2 SE.
  fig2  kicked Ising 4x4x3 (fez 11-07, judged place): retention of the bulk (4 sites) and the surface (44 sites) per
        theta and t; the split is the scorer's own (gpu/os3d_v31_score.py, reported beside, not judged).
  fig3  (moved to paper 9, owner 2026-11-11; kept here, not built into paper 8) IBM 2023 utility observables (fez 11-10): raw value and exact value against theta_h for Z_106 (4 steps), the
        weight-10 (5 steps), the weight-17 (5 steps) and the Fig. 4a product.
usage: python notes/paper8/figures.py [OUT_DIR]
"""
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def load(rel):
    return json.load(open(os.path.join(ROOT, rel)))


def fig1(out):
    runs = [("N 51, kingston 11-07", "results/du51-2026-11-07/ibm_kingston/run/scores.json", None, "o"),
            ("N 71, kingston 11-07", "results/du71-2026-11-07/ibm_kingston/run/scores.json", None, "s"),
            ("N 91, marrakesh 11-09", "results/du91-2026-11-09/ibm_marrakesh/run/scores.json", None, "^"),
            ("N 91, fez 11-10 (ruler in both jobs)", "results/night-2026-11-10/du91r/ibm_fez/scores.json", "r", "D")]
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    for i, (lab, rel, kind, mk) in enumerate(runs):
        sc = load(rel)
        hs, d, e = [], [], []
        for h, key in ((0.05, "0.05"), (0.10, "0.10" if kind else "0.1"), (0.15, "0.15")):
            r = sc["rate"][key]
            if "k" not in r:
                continue
            hs.append(h + (i - 1.5) * 0.004)
            d.append(r["k"] - math.cos(2 * h))
            e.append(2 * r["se"])
        ax.errorbar(hs, d, yerr=e, fmt=mk, capsize=3, label=lab)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("h")
    ax.set_ylabel("k - cos 2h")
    ax.set_xticks([0.05, 0.10, 0.15])
    ax.legend(fontsize=7, frameon=False)
    ax.set_title("Dual-unitary chain, raw: decay rate against the exact cos 2h", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "fig1_dual_unitary_rates.pdf"))
    plt.close(fig)


def fig2(out):
    sc = load("results/os3d-physA-2026-11-07/j1_4x4x3/scores.json")
    arms = [a for a in sc["arms"].values() if a["candidate"] == sc["chosen"] and a["kind"] == "3D"]
    fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.6), sharey=True)
    for ax, th in zip(axs, sorted({a["theta"] for a in arms})):
        sub = sorted((a for a in arms if a["theta"] == th), key=lambda a: a["t"])
        ts = [a["t"] for a in sub]
        ax.plot(ts, [a["classes"]["bulk"]["retention"] for a in sub], "o-", label="bulk (4 sites)")
        ax.plot(ts, [a["classes"]["surface"]["retention"] for a in sub], "s--", label="surface (44 sites)")
        ax.set_title(f"theta {th}", fontsize=9)
        ax.set_xlabel("t")
        ax.set_xticks(ts)
    axs[0].set_ylabel("retention M / M exact")
    axs[0].legend(fontsize=7, frameon=False)
    fig.suptitle("Kicked Ising 4x4x3, ibm_fez 2026-11-07, judged place (after the fact)", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "fig2_ising_bulk_surface.pdf"))
    plt.close(fig)


def fig3(out):
    sc = load("results/utility-2026-11-10/ibm_fez/scores.json")
    names = [("z106_t4", "Z_106, 4 steps (READS)"), ("w10_t5", "weight-10, 5 steps (READS)"),
             ("w17_t5", "weight-17, 5 steps (does not read)"), ("w17b_t5x", "Fig. 4a, 5 steps + R_X (does not read)")]
    fig, axs = plt.subplots(1, 4, figsize=(9.0, 2.6), sharey=True)
    for ax, (key, title) in zip(axs, names):
        r = sc["observables"][key]
        th = [p["k"] * math.pi / 32 for p in r["points"]]
        ax.plot(th, [p["exact"] for p in r["points"]], "k-", lw=1, label="exact")
        ax.errorbar(th, [p["z"] for p in r["points"]], yerr=[2 * p["se"] for p in r["points"]], fmt="o", ms=3,
                    capsize=2, label="device, raw")
        ax.set_title(title, fontsize=8)
        ax.set_xlabel("theta_h")
        ax.axhline(0, color="0.7", lw=0.6)
    axs[0].set_ylabel("expectation value")
    axs[0].legend(fontsize=7, frameon=False)
    fig.suptitle("IBM's 2023 utility observables on the Eagle graph embedded in ibm_fez, 2026-11-10, no mitigation",
                 fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "fig3_utility_observables.pdf"))
    plt.close(fig)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "notes", "paper8", "out")
    os.makedirs(out, exist_ok=True)
    fig1(out)
    fig2(out)
    print("written", sorted(f for f in os.listdir(out) if f.startswith("fig")))
