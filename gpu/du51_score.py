"""Score the N = 51 dual-unitary run (prereg/drafts-2026-11-06/du51_DRAFT.md section 4, the 2026-11-03 judgements),
written before the run. Reads both jobs through the user entrance's answer cards (psf_os.user2d.cards).

  1. READS: over the 24 on-cone points (site t of the chain), the mean squared error of <X_t> against the exact
     value, against the mean square of the exact values: READS if at most half.
  2. Decay rate per h > 0: R(t) = <X_t>(h) / <X_t>(h = 0), fitted as k^t (weighted least squares on ln R through the
     origin, over the t where both values exceed 3 SE); AGREES if |k - cos 2h| <= max(2 SE, 0.005), else DIFFERS;
     NOT TESTED if fewer than two t qualify.
  3. Readable depth per h: the largest t whose on-cone value exceeds 3 SE (a number).
Reported: off-cone mean and largest |<X>| per point, retention <X_t> / exact, the sentinels, CZ per point.

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/du51_score.py OUT_DIR ANSWERS.json [--ts 4,8 (dry check only)]
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from daily import du91 as X  # noqa: E402
from psf_os import user2d as U  # noqa: E402

JOBS = ("A", "B")


def parse(tag):
    _, h, t = tag.split("_")
    return int(h[1:]) / 100.0, int(t[1:])


def main(out, answers_file, ts_only=None):
    """ts_only: the dry check's subset of depths (the declared run uses every depth)."""
    T_STEPS = tuple(ts_only) if ts_only else X.T_STEPS
    answers = json.load(open(answers_file))
    shape = json.load(open(os.path.join(out, "build.json")))["shape"]
    site = X.snake(51, next(s for s in X.SHAPES if s[0] == shape))   # site k of the chain -> the user's label
    pts, sent, cz = {}, {}, {}
    for j in JOBS:
        jd, runs = os.path.join(out, j, "job"), os.path.join(out, j, "runs")
        rep = json.load(open(os.path.join(out, j, "report.json")))
        for tag, card in U.cards(jd, runs, answers).items():
            h, t = parse(tag)
            if t not in T_STEPS:
                continue
            q = {x["q"]: x for x in card["qubits"]}       # the card lists the qubits by sorted label, not by site
            c = q[site[t]]
            on, se = c["z"], max(c["two_se"] / 2, 1e-4)   # floor: a noiseless +-1 has SE 0 (dry check only)
            off = [abs(x["z"]) for lab, x in q.items() if lab != site[t]]
            pts[(h, t)] = dict(on=on, se=se, exact=c["exact"], off_mean=float(np.mean(off)),
                               off_max=float(np.max(off)), mirror_mean=card["mirror_mean"], floor_mean=card["floor_mean"])
            sent[j] = card["sentinel"]
            cz[(h, t)] = rep["items"][tag]["cz"]
    on = np.array([v["on"] for v in pts.values()])
    ex = np.array([v["exact"] for v in pts.values()])
    mse, msq = float(np.mean((on - ex) ** 2)), float(np.mean(ex ** 2))
    res = dict(sentinels=sent, mse=mse, mean_square_exact=msq, reads="READS" if mse <= msq / 2 else "DOES NOT READ",
               rate={}, readable_depth={}, points={})
    for h in X.H_VALUES:
        ok = [t for t in T_STEPS if pts[(h, t)]["on"] > 3 * pts[(h, t)]["se"]]
        res["readable_depth"][str(h)] = max(ok) if ok else 0
    for h in X.H_VALUES[1:]:
        ts = [t for t in T_STEPS if pts[(h, t)]["on"] > 3 * pts[(h, t)]["se"]
              and pts[(0.0, t)]["on"] > 3 * pts[(0.0, t)]["se"]]
        ck = float(np.cos(2 * h))
        if len(ts) < 2:
            res["rate"][str(h)] = dict(verdict="NOT TESTED", ts=ts, cos2h=ck)
            continue
        a = np.array(ts, dtype=float)
        y = np.array([np.log(pts[(h, t)]["on"] / pts[(0.0, t)]["on"]) for t in ts])
        var = np.array([(pts[(h, t)]["se"] / pts[(h, t)]["on"]) ** 2 + (pts[(0.0, t)]["se"] / pts[(0.0, t)]["on"]) ** 2
                        for t in ts])
        w = 1 / var
        lk = float(np.sum(w * a * y) / np.sum(w * a ** 2))
        k, sk = float(np.exp(lk)), float(np.exp(lk) / np.sqrt(np.sum(w * a ** 2)))
        res["rate"][str(h)] = dict(k=k, se=sk, cos2h=ck, diff=k - ck, ts=ts,
                                   verdict="AGREES" if abs(k - ck) <= max(2 * sk, 0.005) else "DIFFERS")
    for (h, t), v in sorted(pts.items()):
        res["points"][f"h{h}_t{t}"] = dict(v, retention=v["on"] / v["exact"] if v["exact"] else None, cz=cz[(h, t)])
    json.dump(res, open(os.path.join(out, "scores.json"), "w"), indent=1)
    print("sentinels", sent, "| MSE", round(mse, 4), "mean square exact", round(msq, 4), res["reads"])
    for h, r in res["rate"].items():
        if r["verdict"] == "NOT TESTED":
            print(f"rate h {h}: NOT TESTED (t {r['ts']})")
        else:
            print(f"rate h {h}: k {r['k']:.4f} +- {r['se']:.4f}  cos2h {r['cos2h']:.4f}  {r['verdict']}  (t {r['ts']})")
    print("readable depth", res["readable_depth"])
    for h in X.H_VALUES:
        print(f"h {h}: on " + " ".join(f"{pts[(h, t)]['on']:+.3f}" for t in T_STEPS)
              + " | exact " + " ".join(f"{pts[(h, t)]['exact']:.3f}" for t in T_STEPS)
              + " | off max " + " ".join(f"{pts[(h, t)]['off_max']:.3f}" for t in T_STEPS))


if __name__ == "__main__":
    ts = [int(v) for v in sys.argv[sys.argv.index("--ts") + 1].split(",")] if "--ts" in sys.argv else None
    main(sys.argv[1], sys.argv[2], ts)
