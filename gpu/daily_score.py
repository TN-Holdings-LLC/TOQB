"""Score one night of the daily record (prereg/daily/standing_rules.md) on one device, written before the first run.

Reads the batch job through the user entrance's own answer cards (psf_os.user2d.cards) with the night's answers and
judges each problem as the 11-04 practice test did: READS, AGREES, BEATS (gpu/practice_score.judge, unchanged), and
reports the share of qubits within 2 SE of the exact value and whether the problem is "guessable"
(|M_exact| >= 0.9 or <= 0.05: shown apart).

usage: PYTHONPATH=<psf-os 7739365> python gpu/daily_score.py RUN_DIR ANSWERS.json   (writes RUN_DIR/scores.json)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from practice_score import judge  # noqa: E402
from psf_os import user2d as U  # noqa: E402


def main(run, answers):
    ans = json.load(open(answers))
    cs = U.cards(f"{run}/job", f"{run}/runs", ans)
    res = dict(sentinel=next(iter(cs.values()))["sentinel"], problems={})
    for tag, c in cs.items():
        r = judge(c)
        q = [x for x in c["qubits"] if "exact" in x]
        r["within_2se"] = sum(abs(x["z"] - x["exact"]) <= x["two_se"] for x in q) / len(q)
        r["guessable"] = abs(r["M_exact"]) >= 0.9 or abs(r["M_exact"]) <= 0.05
        res["problems"][tag] = r
    json.dump(res, open(f"{run}/scores.json", "w"), indent=1)
    print("sentinel", res["sentinel"])
    for tag, r in res["problems"].items():
        print(f"{tag:6} {r['reads']:13} {r['agrees']:8} {r['beats']:13} M {r['M']:+.3f} exact {r['M_exact']:+.3f} "
              f"diff {r['diff']:+.3f} +- {r['two_se']:.3f}  MSE {r['mse']:.4f} / guess {r['trivial_guess_mse']:.4f}  "
              f"floor {r['floor_mean']:.3f}  within 2 SE {r['within_2se']:.0%}" + ("  (guessable)" if r["guessable"] else ""))
    return res


if __name__ == "__main__":
    main(*sys.argv[1:3])
