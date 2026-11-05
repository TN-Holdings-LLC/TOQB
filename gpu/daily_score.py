"""Score one night of the daily record (prereg/daily/standing_rules.md) on one device, written before the first run.

Reads the batch job through the user entrance's own answer cards (psf_os.user2d.cards) with the night's answers and
judges each problem as the 11-04 practice test did: READS, AGREES, BEATS (gpu/practice_score.judge, unchanged), and
reports the share of qubits within 2 SE of the exact value and whether the problem is "guessable"
(|M_exact| >= 0.9 or <= 0.05: shown apart).

Added 2026-11-05 evening (owner: report beside the judgements, the judgements unchanged): retention R = M / M_exact
(meaningful when |M_exact| >= 0.1), normalised error |M - M_exact| / |M_exact|, the per-qubit slope
sum(z a) / sum(a^2), the MSE left after that one scale, and the decay per CZ layer -ln(slope) / L (L: CZ layers of the
compiled circuit).

usage: PYTHONPATH=<psf-os 7739365> python gpu/daily_score.py RUN_DIR ANSWERS.json   (writes RUN_DIR/scores.json)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from practice_score import judge  # noqa: E402
from psf_os import user2d as U  # noqa: E402


def cz_layers(qpy_file):
    """CZ layers of the compiled circuit: each CZ goes one layer after the latest CZ on either of its qubits."""
    from qiskit import qpy
    (c,) = qpy.load(open(qpy_file, "rb"))
    last, n = {}, 0
    for ins in c.data:
        if ins.operation.name == "cz":
            qs = [c.find_bit(x).index for x in ins.qubits]
            k = max(last.get(q, 0) for q in qs) + 1
            for q in qs:
                last[q] = k
            n = max(n, k)
    return n


def main(run, answers):
    ans = json.load(open(answers))
    cs = U.cards(f"{run}/job", f"{run}/runs", ans)
    res = dict(sentinel=next(iter(cs.values()))["sentinel"], problems={})
    for tag, c in cs.items():
        r = judge(c)
        q = [x for x in c["qubits"] if "exact" in x]
        r["within_2se"] = sum(abs(x["z"] - x["exact"]) <= x["two_se"] for x in q) / len(q)
        r["guessable"] = abs(r["M_exact"]) >= 0.9 or abs(r["M_exact"]) <= 0.05
        z = [x["z"] for x in q]
        a = [x["exact"] for x in q]
        slope = sum(zi * ai for zi, ai in zip(z, a)) / sum(ai * ai for ai in a)
        layers = cz_layers(f"{run}/runs/p2d_{tag}.qpy")
        r.update(retention=r["M"] / r["M_exact"] if abs(r["M_exact"]) >= 0.1 else None,
                 norm_error=abs(r["diff"]) / abs(r["M_exact"]) if r["M_exact"] else None, slope=slope,
                 mse_after_scale=sum((zi - slope * ai) ** 2 for zi, ai in zip(z, a)) / len(a), cz_layers=layers,
                 decay_per_layer=(-__import__("math").log(slope) / layers) if slope > 0 and layers else None)
        res["problems"][tag] = r
    json.dump(res, open(f"{run}/scores.json", "w"), indent=1)
    print("sentinel", res["sentinel"])
    for tag, r in res["problems"].items():
        print(f"{tag:6} {r['reads']:13} {r['agrees']:8} {r['beats']:13} M {r['M']:+.3f} exact {r['M_exact']:+.3f} "
              f"diff {r['diff']:+.3f} +- {r['two_se']:.3f}  MSE {r['mse']:.4f} / guess {r['trivial_guess_mse']:.4f}  "
              f"floor {r['floor_mean']:.3f}  within 2 SE {r['within_2se']:.0%}" + ("  (guessable)" if r["guessable"] else ""))
        print(f"       retention {r['retention'] if r['retention'] is None else round(r['retention'], 3)}  slope {r['slope']:.3f}  "
              f"MSE after one scale {r['mse_after_scale']:.4f}  CZ layers {r['cz_layers']}  decay/layer "
              + (f"{r['decay_per_layer']:.4f}" if r["decay_per_layer"] is not None else "-"))
    return res


if __name__ == "__main__":
    main(*sys.argv[1:3])
