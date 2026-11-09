"""Score a Schwinger job (gpu/schw_build.py), written before any run. Through the user entrance's answer cards.

Per circuit (sites n = 1..N, read on the labels where the swap network left them):
  nMSE  = mean_n (z_n - e_n)^2 / mean_n e_n^2 (the main measure, notes/reporting/layout_comparison_metric.md)
  READS if MSE <= mean square / 2
  BEATS if MSE is below both guesses' MSE: the bare vacuum (z_n = +1 on odd n, -1 on even n) and all zero
  nu    = (1 / 2N) sum_n (1 + (-1)^n z_n) (particle density; 0 in the bare vacuum); AGREES if |nu - nu_exact| <= 0.05
  charge = sum_n z_n (conserved: exact 0); reported as a raw check, never used to change a value
Every circuit is reported; the sentinel as recorded.

usage: PYTHONPATH=<psf-os>:<TOQB>/gpu python gpu/schw_score.py OUT ANSWERS.json   (writes OUT/scores.json)
"""
import json
import os
import sys

import numpy as np

from psf_os import user2d as U


def main(out, answers_file):
    b = json.load(open(os.path.join(out, "build.json")))
    answers = json.load(open(answers_file))
    jd = os.path.join(out, "job_build")
    cards = U.cards(os.path.join(jd, "job"), os.path.join(jd, "runs"), answers)
    res = dict(device=b["device"], items={})
    for tag, c in sorted(cards.items()):
        m = b["items"][tag]
        n = m["n"]
        q = {str(x["q"]): x for x in c["qubits"]}
        z = np.array([q[str(m["label_of_site"][str(s)])]["z"] for s in range(1, n + 1)])
        e = np.array([q[str(m["label_of_site"][str(s)])]["exact"] for s in range(1, n + 1)])
        vac = np.array([1.0 if s % 2 == 1 else -1.0 for s in range(1, n + 1)])
        msq = float(np.mean(e ** 2))
        mse = float(np.mean((z - e) ** 2))
        g_vac, g_zero = float(np.mean((vac - e) ** 2)), msq
        nu = lambda v: float(np.sum(1 + np.array([(-1) ** s for s in range(1, n + 1)]) * v) / (2 * n))
        res["items"][tag] = dict(n=n, params=m["params"], steps=m["steps"], cz=b["cz"][tag], nmse=mse / msq, mse=mse,
                                 mean_square_exact=msq, mse_vacuum_guess=g_vac, mse_zero_guess=g_zero,
                                 reads="READS" if mse <= msq / 2 else "DOES NOT READ",
                                 beats="BEATS" if mse < min(g_vac, g_zero) else "DOES NOT BEAT",
                                 nu=nu(z), nu_exact=nu(e),
                                 nu_agrees="AGREES" if abs(nu(z) - nu(e)) <= 0.05 else "DIFFERS",
                                 charge=float(np.sum(z)), mirror_mean=c["mirror_mean"], floor_mean=c["floor_mean"],
                                 sentinel=c["sentinel"])
    res["sentinel"] = next(iter(res["items"].values()))["sentinel"]
    json.dump(res, open(os.path.join(out, "scores.json"), "w"), indent=1)
    print(f"{b['device']}  sentinel {res['sentinel']}")
    for tag, r in res["items"].items():
        print(f"{tag:14} CZ {r['cz']:4} nMSE {r['nmse']:.3f} {r['reads']:13} {r['beats']:13} "
              f"(MSE {r['mse']:.3f} / vacuum {r['mse_vacuum_guess']:.3f} / zero {r['mse_zero_guess']:.3f})  "
              f"nu {r['nu']:.3f} exact {r['nu_exact']:.3f} {r['nu_agrees']}  charge {r['charge']:+.3f}  "
              f"floor {r['floor_mean']:.3f} mirror {r['mirror_mean']:.3f}")
    return res


if __name__ == "__main__":
    main(*sys.argv[1:3])
