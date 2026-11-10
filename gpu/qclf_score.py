"""Score a classifier job (gpu/qclf_build.py, the fold:rule arm alone: owner 2026-11-10 11:05 JST) against the sealed
answers (gpu/qclf_task.py); written before any run, to be fixed with the declaration. 10-30's classifier and
subsampling unchanged (toqb.qelm: features 1 - 2 k1 / S, least squares with intercept on the 128 training points,
sign on the 200 test points; S = 16 ... 250 drawn from the 250-shot counts without replacement, seeds as 10-30).

Judged (per job):
  A  READS if the S = 250 test accuracy is above the majority-class guess: one-sided exact binomial test of the
     number correct against p0 = the majority share of the 200 test labels, at 0.05; else DOES NOT READ.
  M  the signed margin: mean over the test points of y * z (z the least-squares output at S = 250), with its SE
     (sd / sqrt(200)).
Beside, never judged: accuracy at every S; the noiseless ceiling; the reach (acc - 0.5) / (ceiling - 0.5) at S = 250;
the median lambda per basis (affine fit of device to noiseless features on the training points); the share of test
points answered +1; floor and mirror P(0) over the measured bits; the sentinel.

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/qclf_score.py OUT ANSWERS.json   (writes OUT/scores.json)
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from toqb import qelm as Q  # noqa: E402


def k1_of(cc, n, points):
    """(rows point-major basis-minor, n) counts of ones per measured bit, and the shots."""
    k1 = np.zeros((len(points), n), dtype=int)
    S = None
    for r, pt in enumerate(points):
        counts = cc[(pt["input"], pt["setting"])]
        S = sum(counts.values())
        for key, v in counts.items():
            b = key.replace(" ", "")[::-1]
            for q in range(n):
                if b[q] == "1":
                    k1[r, q] += v
    return k1, S


def p0_mean(cc, n):
    tot, ones = 0, 0
    for counts in cc.values():
        for key, v in counts.items():
            b = key.replace(" ", "")[::-1]
            ones += v * sum(b[q] == "1" for q in range(n))
            tot += v * n
    return 1 - ones / tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("answers")
    a = ap.parse_args()
    from scipy.stats import binomtest
    from psf_os import job as J
    from psf_os import sentinel
    rep = json.load(open(os.path.join(a.out, "report.json")))
    ans = json.load(open(a.answers))
    n, L = rep["n"], rep["L"]
    F0 = np.array(ans["features"])
    ytr, yte = np.array(ans["y_train"]), np.array(ans["y_test"])
    po = rep.get("points_override")
    if po:
        F0 = np.vstack([F0[:po], F0[len(ytr):len(ytr) + po]])
        ytr, yte = ytr[:po], yte[:po]
    ntr = len(ytr)
    F0tr, F0te = F0[:ntr], F0[ntr:]
    jd, runs = os.path.join(a.out, "job"), os.path.join(a.out, "runs")
    cells = J.read(jd, runs)
    majority = float(max(np.mean(yte == 1), np.mean(yte == -1)))
    ceiling = Q.accuracy(Q.ols_predict(Q.ols_fit(F0tr, ytr), F0te), yte)
    res = dict(device=rep["device"], L=L, answers_sha256=rep["answers_sha256"], majority=majority, ceiling=ceiling,
               sentinel=sentinel.verdict(jd, runs)["status"], arms={})
    for arm, r in rep["arms"].items():
        tag = r["tag"]
        rec, cc = cells[f"q_{tag}"]
        k1, S0 = k1_of(cc, n, rec["points"])
        Fd = Q.device_features(k1, S0, n)
        aa, lam = Q.affine_fit(Fd[:ntr], F0tr)
        ar = dict(cz_per_circuit=r["cz_per_circuit"], shots=S0,
                  lambda_median=[float(np.median(lam[i * n:(i + 1) * n])) for i in range(3)], acc={})
        for S in Q.SUBSAMPLE:
            kS = Q.subsample(k1, S0, S, Q.SHOT_SEED + 7 * S)
            FdS = Q.device_features(kS, S, n)
            z = Q.ols_predict(Q.ols_fit(FdS[:ntr], ytr), FdS[ntr:])
            ar["acc"][S] = Q.accuracy(z, yte)
            if S == S0:
                ok = Q.correct(z, yte)
                m = yte * z
                ar["share_plus"] = float(np.mean(np.sign(z) == 1))
        k = int(ok.sum())
        p = float(binomtest(k, len(ok), majority, alternative="greater").pvalue)
        ar["A"] = dict(correct=k, of=len(ok), p0=majority, p=p, verdict="READS" if p <= 0.05 else "DOES NOT READ")
        ar["M"] = dict(margin=float(np.mean(m)), se=float(np.std(m, ddof=1) / math.sqrt(len(m))))
        ar["reach"] = (ar["acc"][S0] - 0.5) / (ceiling - 0.5) if ceiling > 0.5 else None
        ar["floor_p0"] = p0_mean(cells[f"q_{tag}_floor"][1], n)
        ar["mirror_p0"] = p0_mean(cells[f"q_{tag}_mirror"][1], n)
        res["arms"][arm] = ar
    json.dump(res, open(os.path.join(a.out, "scores.json"), "w"), indent=1, default=str)
    print(f"{res['device']}  L {L}  sentinel {res['sentinel']}  majority {majority:.3f}  ceiling {ceiling:.3f}")
    for arm, ar in res["arms"].items():
        A, M = ar["A"], ar["M"]
        reach = f"{ar['reach']:.3f}" if ar["reach"] is not None else "-"
        print(f"{arm}: CZ {ar['cz_per_circuit']}  A {A['correct']}/{A['of']} against p0 {A['p0']:.3f}: p {A['p']:.3g} "
              f"{A['verdict']}  M margin {M['margin']:+.4f} (SE {M['se']:.4f})")
        print("  beside: acc " + ", ".join(f"S{S} {v:.3f}" for S, v in ar["acc"].items()) +
              f"; reach {reach}; lambda (X, Y, Z) {', '.join(f'{v:.3f}' for v in ar['lambda_median'])}; share(+1) "
              f"{ar['share_plus']:.3f}; floor {ar['floor_p0']:.3f}; mirror {ar['mirror_p0']:.3f}")


if __name__ == "__main__":
    main()
