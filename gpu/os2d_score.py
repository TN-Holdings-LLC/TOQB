"""Score the OS2D test job (prereg/drafts-2026-11-04/os2d_note_DRAFT.md), written before any device run.

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/os2d_score.py JOB_DIR RUNS_DIR ANSWERS_CPU OUT_JSON
"""
import json
import sys

import numpy as np

from psf_os import ising2d as I
from psf_os import job as J
from psf_os import mirror2d as M
from psf_os import sentinel
from psf_os.kim import z_values

TS = [1, 2, 3, 4, 5]


def mse(m, a, idx):
    return float(np.mean([(m[t][i] - a[t][i]) ** 2 for t in TS for i in idx])) if idx else None


def verdict3(r):
    if r is None:
        return "NOT TESTED"
    return "HELPS" if r <= 0.8 else "HURTS" if r >= 1.25 else "NO EFFECT"


def main(job, runs, ans_path, out):
    ans = json.load(open(ans_path))
    if ans["qubits"] != I.QUBITS:
        raise RuntimeError("answers on another qubit order")
    a = {t: ans["answers"][str(t)] for t in TS}
    sc = I.score(job, runs)
    m = {t: sc["0.53"][t] for t in TS}
    z0 = np.mean([sc["0"][t] for t in sorted(sc["0"])], axis=0)
    mir = M.score(job, runs)
    zm = np.mean([mir[t] for t in sorted(mir)], axis=0)
    fl = M.flags(z0, zm)
    n = len(I.QUBITS)
    allq = list(range(n))
    bad = [I.QUBITS.index(q) for q in fl["qubits"]]
    rest = [i for i in allq if i not in bad]
    # SE of the magnetisation per t from the counts (shot noise only)
    se_m = {}
    for name, (rec, cc) in J.read(job, runs).items():
        if rec.get("psfos_job", {}).get("kind") == "ising2d" and abs(float(rec["psfos_job"].get("theta_x", 0.53)) - 0.53) < 1e-9:
            for p in rec["points"]:
                _, se = z_values(cc[(p["input"], "z")], n)
                se_m[p["t"]] = float(np.sqrt(np.sum(se ** 2)) / n)
    rows = {t: dict(M_measured=float(np.mean(m[t])), M_exact=float(np.mean(a[t])), two_se=2 * se_m[t],
                    dev=float(abs(np.mean(m[t]) - np.mean(a[t])))) for t in TS}
    mse_all = mse(m, a, allq)
    msq = float(np.mean([a[t][i] ** 2 for t in TS for i in allq]))
    q1 = (mse(m, a, bad) / mse(m, a, rest)) if bad and rest else None
    q2 = (mse(m, a, rest) / mse_all) if bad else None
    res = dict(sentinel=sentinel.verdict(job, runs)["status"], floor=z0.tolist(), mirror_mean=zm.tolist(),
               mirror_by_t={str(t): mir[t] for t in mir}, flags=fl,
               Q1=dict(mse_flagged=mse(m, a, bad), mse_rest=mse(m, a, rest), ratio=q1,
                       verdict="NOT TESTED" if q1 is None else "LOCATES" if q1 >= 2 else "DOES NOT LOCATE"),
               Q2=dict(ratio=q2, verdict=verdict3(q2), dropped=fl["qubits"]),
               P6=dict(rows=rows, mse=mse_all, mean_square_answer=msq,
                       reads="READS" if mse_all <= msq / 2 else "DOES NOT READ",
                       agrees="AGREES" if max(r["dev"] for r in rows.values()) <= 0.05 else "DIFFERS"))
    json.dump(res, open(out, "w"), indent=1)
    print(f"sentinel {res['sentinel']}; flagged {fl['qubits']} (line {fl['line']:.3f}); Q1 {res['Q1']['verdict']} "
          f"({q1}); Q2 {res['Q2']['verdict']} ({q2}); P6 t1-5 {res['P6']['reads']} {res['P6']['agrees']}")
    return res


if __name__ == "__main__":
    main(*sys.argv[1:5])
