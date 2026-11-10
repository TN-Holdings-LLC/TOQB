"""Score the N = 91 rerun with the ruler in every job (gpu/du51_build.py --rule-c --ruler-every-job; owner 2026-11-10
13:16 JST), written before the run. The 2026-11-03 judgements of du51 / du71 / du91, with the ruler taken from the
same job as the h it divides. Reads both jobs through the user entrance's answer cards (psf_os.user2d.cards).

Series: A0 (job A's h = 0), 0.05, 0.10 (job A); B0 (job B's h = 0), 0.15 (job B).
  1. READS: over the 30 on-cone points (5 series x 6 t; site t of the chain), the mean squared error of <X_t>
     against the exact value, against the mean square of the exact values: READS if at most half.
  2. Decay rate per h > 0, against the ruler of its own job (0.05 and 0.10 against A0, 0.15 against B0):
     R(t) = <X_t>(h) / <X_t>(ruler), fitted as k^t (weighted least squares on ln R through the origin, over the t
     where both exceed 3 SE); AGREES if |k - cos 2h| <= max(2 SE, 0.005), else DIFFERS; NOT TESTED if fewer than two
     t qualify.
  3. Readable depth per series: the largest t whose on-cone value exceeds 3 SE.
Reported beside, never judged: the rate of 0.15 against A0 (the cross-job ratio of the earlier runs); the ruler
ratio B0 / A0 fitted the same way (1 if the two jobs saw the same device); off-cone mean and largest |<X>|,
retention, the sentinels, CZ per point.

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/du91r_score.py OUT_DIR ANSWERS.json
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from daily import du91 as X  # noqa: E402
from psf_os import user2d as U  # noqa: E402

JOBS = ("A", "B")


def series_of(tag):
    head, h, t = tag.split("_")
    h, t = int(h[1:]) / 100.0, int(t[1:])
    if h == 0.0:
        return ("B0" if head.endswith("b") else "A0"), t
    return f"{h:.2f}", t


def fit(pts, num, den, ts_all):
    ts = [t for t in ts_all if pts[(num, t)]["on"] > 3 * pts[(num, t)]["se"] and pts[(den, t)]["on"] > 3 * pts[(den, t)]["se"]]
    if len(ts) < 2:
        return dict(verdict="NOT TESTED", ts=ts)
    a = np.array(ts, dtype=float)
    y = np.array([np.log(pts[(num, t)]["on"] / pts[(den, t)]["on"]) for t in ts])
    var = np.array([(pts[(num, t)]["se"] / pts[(num, t)]["on"]) ** 2 + (pts[(den, t)]["se"] / pts[(den, t)]["on"]) ** 2
                    for t in ts])
    w = 1 / var
    lk = float(np.sum(w * a * y) / np.sum(w * a ** 2))
    return dict(k=float(np.exp(lk)), se=float(np.exp(lk) / np.sqrt(np.sum(w * a ** 2))), ts=ts)


def main(out, answers_file):
    T = X.T_STEPS
    answers = json.load(open(answers_file))
    b = json.load(open(os.path.join(out, "build.json")))
    if not b.get("ruler_every_job"):
        raise SystemExit("STOP: not a ruler-in-every-job build")
    n = b["n"]
    site = b["user_chain"] if b["shape"] == "C" else X.snake(n, next(s for s in X.SHAPES if s[0] == b["shape"]))
    pts, sent, cz = {}, {}, {}
    for j in JOBS:
        jd, runs = os.path.join(out, j, "job"), os.path.join(out, j, "runs")
        rep = json.load(open(os.path.join(out, j, "report.json")))
        for tag, card in U.cards(jd, runs, answers).items():
            s, t = series_of(tag)
            q = {x["q"]: x for x in card["qubits"]}
            c = q[site[t]]
            off = [abs(x["z"]) for lab, x in q.items() if lab != site[t]]
            pts[(s, t)] = dict(on=c["z"], se=max(c["two_se"] / 2, 1e-4), exact=c["exact"], off_mean=float(np.mean(off)),
                               off_max=float(np.max(off)), mirror_mean=card["mirror_mean"], floor_mean=card["floor_mean"])
            sent[j] = card["sentinel"]
            cz[(s, t)] = rep["items"][tag]["cz"]
    on = np.array([v["on"] for v in pts.values()])
    ex = np.array([v["exact"] for v in pts.values()])
    mse, msq = float(np.mean((on - ex) ** 2)), float(np.mean(ex ** 2))
    res = dict(device=b["device"], sentinels=sent, points_n=len(pts), mse=mse, mean_square_exact=msq,
               reads="READS" if mse <= msq / 2 else "DOES NOT READ", rate={}, beside={}, readable_depth={}, points={})
    series = ("A0", "0.05", "0.10", "B0", "0.15")
    for s in series:
        ok = [t for t in T if pts[(s, t)]["on"] > 3 * pts[(s, t)]["se"]]
        res["readable_depth"][s] = max(ok) if ok else 0
    for s, den in (("0.05", "A0"), ("0.10", "A0"), ("0.15", "B0")):
        r = fit(pts, s, den, T)
        ck = float(np.cos(2 * float(s)))
        r.update(cos2h=ck, ruler=den)
        if "k" in r:
            r.update(diff=r["k"] - ck, verdict="AGREES" if abs(r["k"] - ck) <= max(2 * r["se"], 0.005) else "DIFFERS")
        res["rate"][s] = r
    x = fit(pts, "0.15", "A0", T)
    x.update(cos2h=float(np.cos(0.3)), ruler="A0 (other job)")
    res["beside"]["rate_0.15_vs_A0"] = x
    res["beside"]["ruler_B0_over_A0"] = fit(pts, "B0", "A0", T)
    for (s, t), v in sorted(pts.items()):
        res["points"][f"{s}_t{t}"] = dict(v, retention=v["on"] / v["exact"] if v["exact"] else None, cz=cz[(s, t)])
    json.dump(res, open(os.path.join(out, "scores.json"), "w"), indent=1)
    print(f"{b['device']}  sentinels {sent} | MSE {mse:.4f} mean square exact {msq:.4f} {res['reads']} ({len(pts)} points)")
    for s, r in res["rate"].items():
        if "k" not in r:
            print(f"rate h {s} (ruler {r['ruler']}): NOT TESTED (t {r['ts']})")
        else:
            print(f"rate h {s} (ruler {r['ruler']}): k {r['k']:.4f} +- {r['se']:.4f}  cos2h {r['cos2h']:.4f}  {r['verdict']}"
                  f"  (t {r['ts']})")
    for key, r in res["beside"].items():
        print(f"beside {key}: " + (f"k {r['k']:.4f} +- {r['se']:.4f} (t {r['ts']})" if "k" in r else f"NOT TESTED {r['ts']}"))
    print("readable depth", res["readable_depth"])
    for s in series:
        print(f"{s:5}: on " + " ".join(f"{pts[(s, t)]['on']:+.3f}" for t in T)
              + " | exact " + " ".join(f"{pts[(s, t)]['exact']:.3f}" for t in T))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
