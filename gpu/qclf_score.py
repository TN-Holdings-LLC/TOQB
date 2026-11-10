"""Score a classifier job (gpu/qclf_build.py) against the sealed answers (gpu/qclf_task.py); written before any run,
to be fixed with the declaration. 10-30's classifier and subsampling unchanged (toqb.qelm: features 1 - 2 k1 / S,
least squares with intercept on the 128 training points, sign on the 200 test points; S = 16 ... 250 drawn from the
250-shot counts without replacement, seeds as 10-30).

Judged (per job):
  A  rule (fold:rule) more accurate than SABRE (qiskit:2:blind:template): one-sided McNemar on the 200 test points at
     S = 64 and S = 250, Holm over the two at 0.05 -> "RESOLVED" (rule more accurate) / "NOT RESOLVED".
  M  the signed margin: mean over the test points of y * z (z the least-squares output at S = 250), per arm; the
     difference rule - SABRE with its paired standard error (sd of the per-point difference / sqrt(200)).
Beside, never judged: accuracy at every S; baselines (majority class, the noiseless ceiling); per arm the median lambda per basis (affine fit of device to noiseless features on the training points),
the share of test points answered +1, floor and mirror means (P(0) over the measured bits), the sentinel; the band
from given L* values (reference only, owner 2026-11-10), with --lstar.

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/qclf_score.py OUT ANSWERS.json [--lstar rule=A,sabre=B]
       (writes OUT/scores.json)
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from toqb import qelm as Q  # noqa: E402

RULE, SABRE = "fold:rule", "qiskit:2:blind:template"


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


def holm_two(pa, pb):
    ps = sorted([(pa, 0), (pb, 1)])
    rej = [False, False]
    if ps[0][0] <= 0.025:
        rej[ps[0][1]] = True
        if ps[1][0] <= 0.05:
            rej[ps[1][1]] = True
    return rej


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("answers")
    ap.add_argument("--lstar", default=None, help="reference band only: rule=L*,sabre=L*")
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
    res = dict(device=rep["device"], L=L, answers_sha256=rep["answers_sha256"], arms={},
               baselines=dict(majority=float(max(np.mean(yte == 1), np.mean(yte == -1))),
                              ceiling=Q.accuracy(Q.ols_predict(Q.ols_fit(F0tr, ytr), F0te), yte)),
               sentinel=sentinel.verdict(jd, runs)["status"])
    corr, marg = {}, {}
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
            corr.setdefault(S, {})[arm] = Q.correct(z, yte)
            if S == S0:
                marg[arm] = yte * z
                ar["share_plus"] = float(np.mean(np.sign(z) == 1))
        ar["margin"] = float(np.mean(marg[arm]))
        ar["floor_p0"] = p0_mean(cells[f"q_{tag}_floor"][1], n)
        ar["mirror_p0"] = p0_mean(cells[f"q_{tag}_mirror"][1], n)
        res["arms"][arm] = ar

    def one_sided(x, y):
        b, c = int(np.sum((x == 1) & (y == 0))), int(np.sum((x == 0) & (y == 1)))
        return b, c, (1.0 if b + c == 0 else float(binomtest(b, b + c, 0.5, alternative="greater").pvalue))
    t = {S: one_sided(corr[S][RULE], corr[S][SABRE]) for S in (64, 250)}
    rej = holm_two(t[64][2], t[250][2])
    res["A"] = dict(S64=t[64], S250=t[250], holm=rej, verdict="RESOLVED" if any(rej) else "NOT RESOLVED")
    d = marg[RULE] - marg[SABRE]
    res["M"] = dict(rule=float(np.mean(marg[RULE])), sabre=float(np.mean(marg[SABRE])), diff=float(np.mean(d)),
                    se=float(np.std(d, ddof=1) / math.sqrt(len(d))))
    if a.lstar:
        ls = dict(kv.split("=") for kv in a.lstar.split(","))
        m = F0.shape[1]
        res["band_reference"] = {}
        for arm, key in ((RULE, "rule"), (SABRE, "sabre")):
            lam = math.exp(-L / float(ls[key]))
            res["band_reference"][arm] = dict(lstar=float(ls[key]), lam=lam, S250=Q.predicted_band(
                F0tr, F0te, ytr, yte, np.zeros(m), np.full(m, lam), 250, seed=11))
    json.dump(res, open(os.path.join(a.out, "scores.json"), "w"), indent=1, default=str)
    b = res["baselines"]
    print(f"{res['device']}  L {L}  sentinel {res['sentinel']}  majority {b['majority']:.3f}  ceiling {b['ceiling']:.3f}")
    for arm, ar in res["arms"].items():
        print(f"{arm:26} CZ {ar['cz_per_circuit']}  lambda (X, Y, Z) {', '.join(f'{v:.3f}' for v in ar['lambda_median'])}"
              f"  acc " + ", ".join(f"S{S} {v:.3f}" for S, v in ar["acc"].items()) +
              f"  margin {ar['margin']:+.3f}  share(+1) {ar['share_plus']:.3f}  floor {ar['floor_p0']:.3f}  "
              f"mirror {ar['mirror_p0']:.3f}")
    x = res["A"]
    print(f"A (rule more accurate than SABRE): S64 {x['S64'][0]}/{x['S64'][1]} p {x['S64'][2]:.3g}; S250 "
          f"{x['S250'][0]}/{x['S250'][1]} p {x['S250'][2]:.3g}; Holm {x['holm']}: {x['verdict']}")
    print(f"M (signed margin): rule {res['M']['rule']:+.4f}  SABRE {res['M']['sabre']:+.4f}  rule - SABRE "
          f"{res['M']['diff']:+.4f} (SE {res['M']['se']:.4f})")
    for arm, v in res.get("band_reference", {}).items():
        print(f"  band (reference only) {arm}: L* {v['lstar']} lambda {v['lam']:.3f} S250 {v['S250'][0]:.3f} "
              f"[{v['S250'][1]:.3f}, {v['S250'][2]:.3f}]")


if __name__ == "__main__":
    main()
