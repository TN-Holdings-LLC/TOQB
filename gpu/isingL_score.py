"""Score the Ising line-against-fold job (gpu/isingL_build.py), written before any run; main measure as declared on
2026-11-08 (notes/reporting/layout_comparison_metric.md): the normalised per-site error.

Per arm (cards of the user entrance): nMSE = mean_i (z_i - e_i)^2 / mean_i e_i^2; its SE by propagation from the
cards' per-site SE (sites independent): SE = 2 sqrt(sum_i (z_i - e_i)^2 se_i^2) / (n mean_i e_i^2); M = mean <Z>,
retention M / M_exact (when |M_exact| >= 0.1); READS if MSE <= mean square / 2; AGREES if |M - M_exact| <= 0.05.
Per lattice, choice (rule "top"): the candidate whose two t = 1 arms (fold, line) have the highest mean mirror.
Comparison per t at the judged place: d = nMSE(line) - nMSE(fold) (negative: the line is closer to the exact answer);
"resolved" when |d| > 2 sqrt(SE_line^2 + SE_fold^2), else "within the shot noise". Retention of both beside. Every
candidate is reported beside; the sentinel as recorded.

usage: PYTHONPATH=<psf-os>:<TOQB>/gpu python gpu/isingL_score.py OUT ANSWERS.json   (writes OUT/scores.json)
"""
import json
import os
import sys

import numpy as np

from psf_os import user2d as U


def main(out, answers_file):
    rep = json.load(open(os.path.join(out, "report.json")))
    answers = json.load(open(answers_file))
    cards = U.cards(os.path.join(out, "job"), os.path.join(out, "runs"), answers)
    arms = {}
    for tag, c in cards.items():
        a = rep["arms"][tag]
        n = int(np.prod(a["lattice"]))
        q = {str(x["q"]): x for x in c["qubits"]}
        z = np.array([q[str(s)]["z"] for s in range(n)])
        e = np.array([q[str(s)]["exact"] for s in range(n)])
        se = np.array([q[str(s)]["two_se"] / 2 for s in range(n)])
        msq = float(np.mean(e ** 2))
        mse = float(np.mean((z - e) ** 2))
        M, Mx = float(np.mean(z)), float(np.mean(e))
        arms[tag] = dict(a, nmse=mse / msq, nmse_se=float(2 * np.sqrt(np.sum((z - e) ** 2 * se ** 2)) / (n * msq)),
                         mse=mse, mean_square_exact=msq, M=M, M_exact=Mx,
                         retention=M / Mx if abs(Mx) >= 0.1 else None,
                         reads="READS" if mse <= msq / 2 else "DOES NOT READ",
                         agrees="AGREES" if abs(M - Mx) <= 0.05 else "DIFFERS",
                         mirror_mean=c["mirror_mean"], floor_mean=c["floor_mean"], sentinel=c["sentinel"])
    res = dict(device=rep["device"], rule="top", theta=rep["theta"], arms=arms,
               sentinel=next(iter(arms.values()))["sentinel"], lattices={})
    t1 = min(rep["ts"])
    for lat in rep["candidates"]:
        sub = {k: v for k, v in arms.items() if "x".join(map(str, v["lattice"])) == lat}
        m1 = {}
        for v in sub.values():
            if v["t"] == t1:
                m1.setdefault(v["candidate"], []).append(v["mirror_mean"])
        chosen = max(m1, key=lambda c: (float(np.mean(m1[c])), -c))
        cmp = {}
        for c in sorted(m1):
            for t in rep["ts"]:
                f = next(v for v in sub.values() if v["candidate"] == c and v["t"] == t and v["layout"] == "fold")
                l = next(v for v in sub.values() if v["candidate"] == c and v["t"] == t and v["layout"] == "line")
                d = l["nmse"] - f["nmse"]
                bound = 2 * float(np.sqrt(l["nmse_se"] ** 2 + f["nmse_se"] ** 2))
                cmp[f"c{c}_t{t}"] = dict(candidate=c, t=t, judged=c == chosen, nmse_fold=f["nmse"], nmse_line=l["nmse"],
                                         line_minus_fold=d, bound=bound, resolved=bool(abs(d) > bound),
                                         retention_fold=f["retention"], retention_line=l["retention"],
                                         cz_fold=f["cz"], cz_line=l["cz"])
        res["lattices"][lat] = dict(chosen=chosen, mean_t1_mirror={str(c): float(np.mean(v)) for c, v in m1.items()},
                                    comparison=cmp)
    json.dump(res, open(os.path.join(out, "scores.json"), "w"), indent=1)
    print(f"{rep['device']}  sentinel {res['sentinel']}  theta {rep['theta']}")
    for lat, r in res["lattices"].items():
        print(f"{lat}: judged candidate {r['chosen']} (mean t1 mirror {r['mean_t1_mirror'][str(r['chosen'])]:.3f})")
        for k, v in r["comparison"].items():
            rf = f"{v['retention_fold']:.3f}" if v["retention_fold"] is not None else "-"
            rl = f"{v['retention_line']:.3f}" if v["retention_line"] is not None else "-"
            print(f"  {k:6} {'JUDGED' if v['judged'] else 'beside':6} nMSE fold {v['nmse_fold']:.4f} (CZ {v['cz_fold']})"
                  f"  line {v['nmse_line']:.4f} (CZ {v['cz_line']})  line - fold {v['line_minus_fold']:+.4f}"
                  f" ({'resolved' if v['resolved'] else 'within the shot noise'} {v['bound']:.4f})"
                  f"  retention {rf} / {rl}")
    for tag, v in sorted(arms.items()):
        print(f"  {tag:10} {v['reads']:13} {v['agrees']:7} M {v['M']:+.3f} exact {v['M_exact']:+.3f}  floor "
              f"{v['floor_mean']:.3f} mirror {v['mirror_mean']:.3f}")
    return res


if __name__ == "__main__":
    main(*sys.argv[1:3])
