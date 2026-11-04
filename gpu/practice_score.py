"""Score the practice test (prereg/drafts-2026-11-04/practice_note.md), written before the device run.

Reads the batch job through the user entrance's own answer cards (psf_os.user2d.cards) with the sealed answers, then
judges each problem: READS (MSE <= half the mean square answer), AGREES (|M - M_exact| <= 0.05) and BEATS (MSE below
the better trivial guess: every <Z> = 0 or every <Z> = 1).

usage: PYTHONPATH=<psf-os ac84182> python gpu/practice_score.py RUN_DIR ANSWERS.json   (writes RUN_DIR/scores.json)
"""
import json
import sys

import numpy as np

from psf_os import user2d as U

sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from practice_circuits import CHAIN  # noqa: E402


def judge(c):
    q = [x for x in c["qubits"] if "exact" in x]
    z = np.array([x["z"] for x in q])
    a = np.array([x["exact"] for x in q])
    mse = float(np.mean((z - a) ** 2))
    msq = float(np.mean(a ** 2))
    diff = float(z.mean() - a.mean())
    guess = min(msq, float(np.mean((1 - a) ** 2)))  # the better trivial guess: every <Z> = 0, or every <Z> = 1
    return dict(beats="BEATS" if mse < guess else "DOES NOT BEAT", trivial_guess_mse=guess, n=len(q), M=float(z.mean()), M_exact=float(a.mean()), diff=diff, two_se=c["answered"]["two_se"],
                mse=mse, mean_square_answer=msq, reads="READS" if mse <= msq / 2 else "DOES NOT READ",
                agrees="AGREES" if abs(diff) <= 0.05 else "DIFFERS", floor_mean=c["floor_mean"],
                mirror_mean=c["mirror_mean"], mirror_flags=c["mirror_flags"]["qubits"],
                worst=[x["q"] for x in sorted(q, key=lambda x: -abs(x["z"] - x["exact"]))[:5]])


def main(run, answers):
    ans = json.load(open(answers))
    cs = U.cards(f"{run}/job", f"{run}/runs", ans)  # user2d's fixed layout under the run folder
    res = dict(sentinel=next(iter(cs.values()))["sentinel"], problems={})
    for tag, c in cs.items():
        r = judge(c)
        if tag.startswith("p4_"):
            t = int(tag.split("_t")[1])
            # the light-cone site of P4: site t of the chain as the user wrote it
            site = next(x for x in c["qubits"] if x["q"] == CHAIN[t])
            r["light_cone_site"] = dict(q=site["q"], z=site["z"], exact=site.get("exact"))
        res["problems"][tag] = r
    fam = {}
    for tag, r in res["problems"].items():
        f, t = tag.rsplit("_t", 1)
        fam.setdefault(f, []).append((int(t), r))
    res["readable_depth"] = {f: dict(reads=max([t for t, r in v if r["reads"] == "READS"], default=0),
                                     agrees=max([t for t, r in v if r["agrees"] == "AGREES"], default=0),
                                     beats=max([t for t, r in v if r["beats"] == "BEATS"], default=0))
                             for f, v in fam.items()}
    json.dump(res, open(f"{run}/scores.json", "w"), indent=1)
    print("sentinel", res["sentinel"])
    for tag, r in res["problems"].items():
        lc = r.get("light_cone_site")
        print(f"{tag:16} {r['reads']:13} {r['agrees']:8} {r['beats']:13} M {r['M']:+.3f} exact {r['M_exact']:+.3f} diff {r['diff']:+.3f} "
              f"+- {r['two_se']:.3f}  MSE {r['mse']:.4f} / half {r['mean_square_answer'] / 2:.4f}  floor {r['floor_mean']:.3f}"
              + (f"  light cone {lc['z']:+.3f} vs {lc['exact']:+.3f}" if lc else ""))
    print("readable depth", res["readable_depth"])
    return res


if __name__ == "__main__":
    main(*sys.argv[1:3])
