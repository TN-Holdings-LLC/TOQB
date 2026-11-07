"""Score a 3D Heisenberg job (draft B; written before any run). Through the user entrance's answer cards.

Choice (rule "top", as declared for the 3D Ising runs of 2026-11-07): the candidate whose own t = 1 arm has the
highest mirror mean is judged at every t. Per judged arm:
  READS   the mean squared error of the site <Z> against the exact values is at most half their mean square;
  AGREES  |m_s - m_s exact| <= 0.05, m_s = mean over sites of (-1)^(x+y+z) <Z> (the Neel order; 1 at the start);
  retention m_s / m_s exact (when |m_s exact| >= 0.1).
Every candidate is reported beside; the sentinel as recorded.

usage: PYTHONPATH=<psf-os>:<TOQB>/gpu python gpu/heis3d_score.py OUT ANSWERS.json   (writes OUT/scores.json)
"""
import json
import os
import sys

import numpy as np

from psf_os import user2d as U


def main(out, answers_file):
    rep = json.load(open(os.path.join(out, "report.json")))
    answers = json.load(open(answers_file))
    L, M, N = rep["lattice"]
    import itertools
    sign = {str(i): (-1) ** (x + y + z) for i, (x, y, z) in enumerate(itertools.product(range(L), range(M), range(N)))}
    cards = U.cards(os.path.join(out, "job"), os.path.join(out, "runs"), answers)
    arms = {}
    for tag, c in cards.items():
        q = {str(x["q"]): x for x in c["qubits"]}
        z = np.array([q[s]["z"] for s in sign])
        ex = np.array([q[s]["exact"] for s in sign])
        sg = np.array([sign[s] for s in sign])
        ms, mse = float(np.mean(sg * z)), float(np.mean(sg * ex))
        err, msq = float(np.mean((z - ex) ** 2)), float(np.mean(ex ** 2))
        arms[tag] = dict(candidate=rep["arms"][tag]["candidate"], t=rep["arms"][tag]["t"], cz=rep["arms"][tag]["cz"],
                         m_s=ms, m_s_exact=mse, mse=err, mean_square_exact=msq,
                         reads="READS" if err <= msq / 2 else "DOES NOT READ",
                         agrees="AGREES" if abs(ms - mse) <= 0.05 else "DIFFERS",
                         retention=ms / mse if abs(mse) >= 0.1 else None,
                         mirror_mean=c["mirror_mean"], floor_mean=c["floor_mean"], sentinel=c["sentinel"])
    t1 = min(rep["ts"])
    top = max((a for a in arms.values() if a["t"] == t1), key=lambda a: (a["mirror_mean"], -a["candidate"]))
    chosen = top["candidate"]
    res = dict(device=rep["device"], rule="top", chosen=chosen, arms=arms,
               sentinel=next(iter(arms.values()))["sentinel"])
    json.dump(res, open(os.path.join(out, "scores.json"), "w"), indent=1)
    print(f"{rep['device']}  sentinel {res['sentinel']}  judged candidate {chosen} (own t{t1} mirror "
          f"{top['mirror_mean']:.3f})")
    for tag, a in sorted(arms.items(), key=lambda kv: (kv[1]["candidate"], kv[1]["t"])):
        mark = "JUDGED" if a["candidate"] == chosen else "beside"
        ret = f"{a['retention']:.3f}" if a["retention"] is not None else "-"
        print(f"{tag:9} {mark:6} {a['reads']:13} {a['agrees']:7} m_s {a['m_s']:+.3f} exact {a['m_s_exact']:+.3f} "
              f"retention {ret}  MSE {a['mse']:.4f}/{a['mean_square_exact']:.4f}  CZ {a['cz']}  "
              f"floor {a['floor_mean']:.3f} mirror {a['mirror_mean']:.3f}")
    return res


if __name__ == "__main__":
    main(*sys.argv[1:3])
