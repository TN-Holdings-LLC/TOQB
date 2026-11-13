"""Paper 9 thread: is "READS" set by the share r the device keeps? (workplace, 2026-11-13; home's instruction of 01:50
CET; desk only, results/ and declarations untouched).

For every judged unit whose device values z and exact values e can be had (per qubit, or per point where the unit's
verdict is over points), with r = sum z e / sum e^2 and the rest z - r e (orthogonal to e), exactly
    MSE / mean square = (1 - r)^2 + mean(rest^2) / mean(e^2).
Sources, in the order of the boundary table (notes/boundary_2026-11-12/boundary.json) plus the 11-12 records:
  - hub_score records (z and exact per qubit in scores.json): hubbard 11-11, hubbard-big 11-11, hub-dt 11-12, xx91 11-12;
  - utility 11-10 and its depth scan 11-11: per theta point (z, exact) in scores.json;
  - isingL 11-10: per site, from the user entrance's cards (psf-os user2d.cards) and the released answers (keyed by
    site, which is the card's label), as gpu/isingL_score.py;
  - ohm 11-12 (fez, kingston): per qubit from the cards and the released answers, every circuit of an arm and cycle
    count together (a Z-level unit recomputed here, not a declared verdict: the declared unit was M per circuit).
Every unit's MSE / mean square is recomputed from its vectors and compared with the stored one (printed; scores.json
keeps z to 4 digits, so the hub_score records differ by up to 1e-4).
Everything else of the boundary table is listed as not obtainable, with the reason.
usage: PYTHONPATH=<psf-os>:<lab-notebook> python r_thread.py OUT_DIR
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
R = lambda *p: os.path.join(ROOT, *p)  # noqa: E731
LINE = 1 - 1 / np.sqrt(2)


def load(p):
    return json.load(open(R(p)))


def unit(family, result, name, z, e, verdict, cz_layers=None, cz_per_qubit=None, stored=None, note=""):
    z, e = np.asarray(z, float), np.asarray(e, float)
    ms = float(np.mean(e ** 2))
    r = float(np.dot(z, e) / np.dot(e, e))
    rest = z - r * e
    ratio = float(np.mean((z - e) ** 2) / ms)
    shrink, other = (1 - r) ** 2, float(np.mean(rest ** 2) / ms)
    return dict(family=family, result=result, unit=name, n=len(z), r=r, shrink=shrink, rest=other, ratio=ratio,
                identity_error=abs(ratio - shrink - other), mean_square=ms, verdict=verdict,
                reads=("READS" in verdict and "NOT READ" not in verdict), cz_layers=cz_layers,
                cz_per_qubit=cz_per_qubit, stored_ratio=stored, note=note)


def main(od):
    os.makedirs(od, exist_ok=True)
    b = load("notes/boundary_2026-11-12/boundary.json")
    rows = {(r["source"], r["unit"]): r for r in b["rows"]}
    U = []
    covered = set()

    # hub_score records
    def hub_family(tag):
        return "Hubbard U4" if tag.endswith("U4") else "Hubbard ruler U0"
    for res, path in (("hubbard-fez-2026-11-11", "results/hubbard-2026-11-11/ibm_fez/scores.json"),
                      ("hubbard-big-fez-2026-11-11", "results/hubbard-big-2026-11-11/ibm_fez/scores.json")):
        bl = {r["unit"].split(" ")[0]: r for r in b["rows"] if r["source"] == path}
        s = load(path)
        for tag, c in sorted(s["circuits"].items()):
            br = bl.get(tag, {})
            covered.add((path, br.get("unit")))
            U.append(unit(hub_family(tag), res, tag, c["z"], c["exact"], c["reads"], br.get("cz_layers"),
                          float(br["cz_per_qubit"]) if br.get("cz_per_qubit") else None, c["mse"] / c["mean_square"]))
    s = load("results/hub-dt-2026-11-12/ibm_fez/scores.json")
    steps = {"L20_T0.5_s1": 1, "L20_T0.5_s2": 2, "L20_T1.0_s2": 2, "L20_T1.0_s4": 4}
    for tag, c in sorted(s["circuits"].items()):
        U.append(unit("Hubbard U4 (dt)", "hub-dt-fez-2026-11-12", tag, c["z"], c["exact"], c["reads"],
                      12 * steps[tag], c["cz"] / 40, c["mse"] / c["mean_square"],
                      note="CZ layers 12 per step (both step sizes)"))
    s = load("results/xx91-2026-11-12/ibm_fez/scores.json")
    for tag, c in sorted(s["circuits"].items()):
        st = int(tag.split("_s")[1])
        fam = "XX91 theta pi/4" if "th0785" in tag else "XX91 theta pi/2 (ruler)"
        U.append(unit(fam, "xx91-fez-2026-11-12", tag, c["z"], c["exact"], c["reads"], 4 * st, c["cz"] / 91,
                      c["mse"] / c["mean_square"]))

    # utility (points over theta)
    for res, path in (("utility-fez-2026-11-10", "results/utility-2026-11-10/ibm_fez/scores.json"),
                      ("utility-depth-fez-2026-11-11", "results/utility-depth-2026-11-11/ibm_fez/scores.json")):
        s = load(path)
        for name, o in s["observables"].items():
            br = next((r for r in b["rows"] if r["source"] == path and r["unit"].startswith(name)), {})
            covered.add((path, br.get("unit")))
            z = [p["z"] for p in o["points"]]
            e = [p["exact"] for p in o["points"]]
            U.append(unit("IBM 2023 utility (points over theta)", res, name, z, e, o["reads"], br.get("cz_layers"),
                          float(br["cz_per_qubit"]) if br.get("cz_per_qubit") else None,
                          o["mse"] / o["mean_square_exact"], note="vector over the 17 theta points"))

    # isingL (cards)
    from psf_os import user2d as UD
    base = "results/night-2026-11-10/isingL"
    s = load(base + "/ibm_fez/scores.json")
    ans = load(base + "/answers/isingL_fez.json")
    cards = UD.cards(R(base, "ibm_fez", "job"), R(base, "ibm_fez", "runs"), ans)   # answers keyed by site = label
    for tag, a in sorted(s["arms"].items()):
        q = {str(x["q"]): x for x in cards[tag]["qubits"]}
        n = int(np.prod(a["lattice"]))
        z = [q[str(k)]["z"] for k in range(n)]
        e = [q[str(k)]["exact"] for k in range(n)]
        sites = range(n)
        br = next((r for r in b["rows"] if "isingL" in r["source"] and r["unit"].startswith(tag)), {})
        covered.add((br.get("source"), br.get("unit")))
        U.append(unit("Ising 3D (isingL)", "isingL-fez-2026-11-10", tag, z, e, a["reads"], a.get("cz_layers"),
                      a["cz"] / n, a["mse"] / a["mean_square_exact"]))

    # ohm (cards), Z level per arm and cycle count
    for res, d, af in (("ohm-fez-2026-11-12", "results/ohm-2026-11-12/ibm_fez", "results/ohm-2026-11-12/answers/ohm_ibm_fez_ans.json"),
                       ("ohm-kingston-2026-11-12", "results/ohm-kingston-2026-11-12/ibm_kingston",
                        "results/ohm-kingston-2026-11-12/answers/ohm_ibm_kingston_ans.json")):
        A = load(af)["z"]
        bj = load(d + "/build.json")
        cards = UD.cards(R(d, "job"), R(d, "runs"), A)
        for arm in ("A0", "A1", "A2"):
            for t in bj["cycles"]:
                z, e = [], []
                tags = [g for g in cards if g.startswith(f"{arm}_t{t}_")]
                for g in tags:
                    for x in cards[g]["qubits"]:
                        z.append(x["z"])
                        e.append(x["exact"])
                lay = bj["cz_depth"][tags[0]]
                U.append(unit(f"Ohm Z level ({arm})", res, f"{arm}_t{t} ({len(tags)} circuits)", z, e,
                              "READS" if np.mean((np.array(z) - np.array(e)) ** 2) <= np.mean(np.array(e) ** 2) / 2
                              else "DOES NOT READ", lay, bj["cz"][tags[0]] / bj["N"], None,
                              note="Z-level unit recomputed here (the declared unit was M per circuit)"))

    missing = []
    for (src, un), r in rows.items():
        if (src, un) in covered:
            continue
        why = "scores.json keeps no per-qubit z (only scalars: M, m_s, retention, MSE)" \
            if any(k in src for k in ("practice", "daily", "heis", "physA", "schw")) else \
            "scores keep only per-step or per-t summaries (mean M, the light-cone site), and the declared MSE is over " \
            "per-qubit values not stored (tried: the summaries do not give the declared MSE / mean square)" \
            if any(k in src for k in ("p6-", "os2d", "du51", "du71", "du91-2026-11-09")) else \
            "unit is a rate or a per-distance front, not a vector of z against e" \
            if any(k in src for k in ("du", "lc3d", "night-2026-11-10/du91r")) else \
            "corrected / derived values only (diffs)" if "corr" in src else "not attempted"
        missing.append(dict(result=r["result"], source=src, unit=un, reason=why))
    json.dump(dict(units=U, not_obtainable=missing), open(os.path.join(od, "r_thread.json"), "w"), indent=1)
    return U, missing


def report(U, missing, od):
    import collections
    lines = []
    worst_id = max(u["identity_error"] for u in U)
    stored = [abs(u["ratio"] - u["stored_ratio"]) for u in U if u["stored_ratio"] is not None]
    lines.append(f"units {len(U)}; decomposition identity worst {worst_id:.1e}; recomputed MSE / mean square against "
                 f"stored: worst {max(stored):.1e} over {len(stored)} units; not obtainable {len(missing)}")
    fam = collections.OrderedDict()
    for u in U:
        fam.setdefault(u["family"], []).append(u)
    for f, us in fam.items():
        rd = [u for u in us if u["reads"]]
        nr = [u for u in us if not u["reads"]]
        by_line = sum((u["r"] >= LINE) == u["reads"] for u in us)
        rest_share = np.mean([u["rest"] / u["ratio"] for u in us if u["ratio"] > 0])
        lay = [(u["cz_layers"], u["r"]) for u in us if u["cz_layers"] and u["r"] > 0]
        slope = None
        if len({x for x, _ in lay}) >= 2:
            x = np.array([a for a, _ in lay], float)
            y = np.log([b for _, b in lay])
            k = np.polyfit(x, y, 1)[0]
            slope = -1 / k if k < 0 else None
        lines.append(f"{f}: {len(us)} units ({len(rd)} READS); r >= 0.293 matches the verdict in {by_line}/{len(us)}; "
                     f"rest's share of MSE / mean square, mean {rest_share:.2f}; r falls by e every "
                     f"{'%.0f' % slope if slope else '-'} CZ layers")
        for u in us:
            lines.append(f"   {u['unit'][:34]:34s} layers {str(u['cz_layers']):>4s} r {u['r']:+.3f} (1-r)^2 {u['shrink']:.3f} "
                         f"rest {u['rest']:.3f} ratio {u['ratio']:.3f} {'READS' if u['reads'] else 'not'}"
                         f"{'  <- r line disagrees' if (u['r'] >= LINE) != u['reads'] else ''}")
    open(os.path.join(od, "r_thread.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return fam


def figures(fam, od):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    marks = "osD^v<>Ph*X"
    for key, xl, fn, logy, xf, yf in (
            ("a", "(1 - r)^2 (shrink only)", "r_thread_a.png", False, lambda u: u["shrink"], lambda u: u["ratio"]),
            ("b", "CZ layers", "r_thread_b_layers.png", True, lambda u: u["cz_layers"], lambda u: u["r"]),
            ("c", "CZ per qubit", "r_thread_c_per_qubit.png", True, lambda u: u["cz_per_qubit"], lambda u: u["r"])):
        fig, ax = plt.subplots(figsize=(7.5, 5.2))
        for i, (f, us) in enumerate(fam.items()):
            pts = [(xf(u), yf(u), u["reads"]) for u in us if xf(u) is not None and yf(u) is not None
                   and (not logy or yf(u) > 0)]
            if not pts:
                continue
            for rd in (True, False):
                xs = [p[0] for p in pts if p[2] == rd]
                ys = [p[1] for p in pts if p[2] == rd]
                ax.scatter(xs, ys, marker=marks[i % len(marks)], s=36, facecolors=f"C{i}" if rd else "none",
                           edgecolors=f"C{i}", label=f"{f} ({'READS' if rd else 'not'})" if xs else None)
        if key == "a":
            lim = 1.0
            ax.plot([0, lim], [0, lim], "k-", lw=0.8, label="shrink only")
            ax.axhline(0.5, color="gray", ls="--", lw=0.8, label="READS line 0.5")
            ax.set_xlim(0, lim)
            ax.set_ylim(0, lim)
            ax.set_ylabel("MSE / mean square")
        else:
            ax.axhline(LINE, color="gray", ls="--", lw=0.8, label="r = 0.293")
            ax.set_yscale("log")
            ax.set_ylabel("r (share kept)")
        ax.set_xlabel(xl)
        ax.legend(fontsize=6, loc="best")
        fig.tight_layout()
        fig.savefig(os.path.join(od, fn), dpi=150)
        plt.close(fig)


if __name__ == "__main__":
    od = sys.argv[1]
    U, missing = main(od)
    fam = report(U, missing, od)
    figures(fam, od)
