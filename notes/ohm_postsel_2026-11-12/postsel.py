"""Ohm 6 cycles, fez and kingston: post-selection on the number of |1> (a check of why the device did not read; NOT a
verdict: the declared verdict stays the uncorrected one in scores.json, and post-selection is never used to judge).
(home VS Claude, 2026-11-12, for home Claude's instruction of 2026-11-12 13:10 CET.)

The circuits (fSim and RZ) keep the total number of |1>; without noise every shot has as many 1 as the initial string.
Per user circuit (kind user2d) and per mirror (user2d_mirror, back to all 0):
  1. kept share: the shots whose number of 1 equals the initial number (mirror: equals 0);
  2. the discarded shots: the change d = (1 in the shot) - (1 at the start), shares d < 0 (decay direction) and d > 0
     (readout 0 -> 1 and the like), and the histogram;
  3. post-selected numbers from the kept shots only, computed exactly as gpu/ohm_score.py computes the uncorrected ones
     (per-qubit Z -> M; M MSE / mean square, READS line 1/2; AGREES 0.2; per-qubit READS; W; exponent
     log2(W(6) / W(3)); mixed share p = (W - W_exact) / (W_mixed - W_exact), W_mixed = W of every Z = 0 (5.5 here)),
     beside the uncorrected numbers recomputed from all shots (checked equal to scores.json);
  4. how much the M MSE falls (uncorrected -> post-selected);
  5. circuits left with fewer than 100 kept shots.
Shots are read the way psf_os.user2d.card reads them (clbit k = k-th character from the right = rec["labels"][k]).
The initial value of chain label chain[i] is bit i of build.json's string. No light-cone selection.
usage: PYTHONPATH=<psf-os> python notes/ohm_postsel_2026-11-12/postsel.py   (from the repository root)"""
import json
import os
from collections import Counter

import numpy as np

from psf_os import job as J
from psf_os import user2d as U

RUNS = {"ibm_fez": ("results/ohm-2026-11-12/ibm_fez", "results/ohm-2026-11-12/answers/ohm_ibm_fez_ans.json"),
        "ibm_kingston": ("results/ohm-kingston-2026-11-12/ibm_kingston",
                         "results/ohm-kingston-2026-11-12/answers/ohm_ibm_kingston_ans.json")}
AGREE, FEW = 0.2, 100
HERE = os.path.dirname(os.path.abspath(__file__))


def z_of(counts, n):
    """Per-clbit <Z> (psf_os.kim.z_values' reading) and the number of shots."""
    tot = sum(counts.values())
    if tot == 0:
        return np.full(n, np.nan), 0
    m = np.zeros(n)
    for key, c in counts.items():
        b = key.replace(" ", "")
        m += c * (1 - 2 * np.array([int(b[-1 - k]) for k in range(n)]))
    return m / tot, tot


def ones(key):
    return key.replace(" ", "").count("1")


def exact_of(ex, lab):
    return ex[str(lab)] if str(lab) in ex else ex[lab]


def one_device(dev, out, ans_file):
    b = json.load(open(os.path.join(out, "build.json")))
    A = json.load(open(ans_file))["z"]
    sc = json.load(open(os.path.join(out, "scores.json")))
    chain, N = b["chain"]["labels"], b["N"]
    right = chain[N // 2:]
    read = J.read(os.path.join(out, "job"), os.path.join(out, "runs"))
    circ, mirr = {}, {}
    for name, (rec, cc) in read.items():
        kind = rec.get("psfos_job", {}).get("kind")
        if kind not in ("user2d", "user2d_mirror"):
            continue
        tag = U._tag_of(name, rec)
        counts = cc[(rec["points"][0]["input"], "z")]
        labels = rec["labels"]
        assert sorted(labels) == sorted(chain), (tag, "measured qubits are not the chain")
        n = len(labels)
        sname = tag.split("_")[2]
        bits = b["strings"][sname]
        init = {lab: int(bits[i]) for i, lab in enumerate(chain)}
        n0 = sum(init.values()) if kind == "user2d" else 0
        tot = sum(counts.values())
        dh = Counter()
        for key, c in counts.items():
            dh[ones(key) - n0] += c
        kept = {k: c for k, c in counts.items() if ones(k) == n0}
        row = dict(shots=tot, kept=sum(kept.values()), kept_share=sum(kept.values()) / tot,
                   d_neg=sum(c for d, c in dh.items() if d < 0) / tot,
                   d_pos=sum(c for d, c in dh.items() if d > 0) / tot,
                   d_hist={int(d): c for d, c in sorted(dh.items())})
        if kind == "user2d_mirror":
            mirr[tag] = row
            continue
        m0 = sum(init[lab] for lab in right)
        ex = A[tag]
        e = np.array([exact_of(ex, lab) for lab in chain])
        er = np.array([exact_of(ex, lab) for lab in right])
        row["M_exact"] = float(((1 - er) / 2).sum() - m0)
        row["n_ones"] = n0
        for which, cnt in (("raw", counts), ("ps", kept)):
            zz, _ = z_of(cnt, n)
            zl = {lab: zz[k] for k, lab in enumerate(labels)}
            z = np.array([zl[lab] for lab in chain])
            zr = np.array([zl[lab] for lab in right])
            row[f"M_{which}"] = float(((1 - zr) / 2).sum() - m0)
            mse_z, msq_z = float(np.mean((z - e) ** 2)), float(np.mean(e ** 2))
            row[f"z_reads_{which}"] = bool(mse_z <= msq_z / 2)
            row[f"z_mse_{which}"] = mse_z
        circ[tag] = row
    worst = max(abs(circ[t]["M_raw"] - sc["circuits"][t]["M"]) for t in circ)
    ks = sorted({n[1:] for n in b["strings"]})
    m0s = {n: sum(int(x) for x in b["strings"][n][N // 2:]) for n in b["strings"]}
    # every Z = 0: M = (N/2) / 2 - m0, so W = (m0(c) - m0(s)) / 2 averaged over the pairs
    W_mixed = float(np.mean([(m0s["c" + k] - m0s["s" + k]) / 2 for k in ks]))
    arms = {}
    for arm in sorted({t.split("_")[0] for t in circ}):
        for t in b["cycles"]:
            c = {n: circ[f"{arm}_t{t}_{n}"] for n in b["strings"]}
            mi = [mirr[f"{arm}_t{t}_{n}"] for n in c]
            r = dict(kept_mean=float(np.mean([x["kept_share"] for x in c.values()])),
                     kept_min=float(min(x["kept_share"] for x in c.values())),
                     d_neg=float(np.mean([x["d_neg"] for x in c.values()])),
                     d_pos=float(np.mean([x["d_pos"] for x in c.values()])),
                     mirror_kept_mean=float(np.mean([x["kept_share"] for x in mi])),
                     mirror_kept_min=float(min(x["kept_share"] for x in mi)),
                     mirror_d_pos=float(np.mean([x["d_pos"] for x in mi])))
            ex_ = np.array([x["M_exact"] for x in c.values()])
            msq = float(np.mean(ex_ ** 2))
            We = float(np.mean([(c["s" + k]["M_exact"] - c["c" + k]["M_exact"]) / 2 for k in ks]))
            for which in ("raw", "ps"):
                d = np.array([x[f"M_{which}"] - x["M_exact"] for x in c.values()])
                mse = float(np.mean(d ** 2))
                W = float(np.mean([(c["s" + k][f"M_{which}"] - c["c" + k][f"M_{which}"]) / 2 for k in ks]))
                r[which] = dict(mse=mse, mse_over_msq=mse / msq, reads=bool(mse <= msq / 2),
                                agrees=int(np.sum(np.abs(d) <= AGREE)),
                                z_reads=int(sum(x[f"z_reads_{which}"] for x in c.values())),
                                W=W, p=(W - We) / (W_mixed - We))
            r["W_exact"], r["mean_square"], r["circuits"] = We, msq, len(c)
            r["mse_drop"] = 1 - r["ps"]["mse"] / r["raw"]["mse"]
            s = sc["arms"][f"{arm}_t{t}"]
            r["check_scores"] = max(abs(r["raw"]["mse"] - s["mse"]), abs(r["raw"]["W"] - s["W"]),
                                    abs(r["raw"]["agrees"] - s["agrees"]), abs(r["raw"]["z_reads"] - s["z_reads"]),
                                    float(r["raw"]["reads"] != (s["reads"] == "READS")))
            arms[f"{arm}_t{t}"] = r
    t3, t6 = min(b["cycles"]), max(b["cycles"])
    expo = {}
    for arm in sorted({k.split("_")[0] for k in arms}):
        e = {}
        for which in ("raw", "ps"):
            w3, w6 = arms[f"{arm}_t{t3}"][which]["W"], arms[f"{arm}_t{t6}"][which]["W"]
            e[which] = float(np.log(w6 / w3) / np.log(t6 / t3)) if w3 > 0 and w6 > 0 else None
        e["exact"] = float(np.log(arms[f"{arm}_t{t6}"]["W_exact"] / arms[f"{arm}_t{t3}"]["W_exact"]) / np.log(t6 / t3))
        dv = sc["exponent"][arm]["device"]
        e["check_scores"] = abs(e["raw"] - dv) if e["raw"] is not None and dv is not None else None
        expo[arm] = e
    few = sorted((t, x["kept"]) for t, x in circ.items() if x["kept"] < FEW)
    dall = Counter()
    for x in circ.values():
        for d, cnum in x["d_hist"].items():
            dall[int(d)] += cnum
    return dict(device=dev, note="CHECK ONLY, not a verdict", W_mixed=W_mixed, check_circuit_M_worst=worst, arms=arms,
                exponent=expo, few_kept=few, d_hist_all={int(d): c for d, c in sorted(dall.items())},
                circuits=circ, mirrors=mirr)


def main():
    res = {}
    for dev, (out, ans) in RUNS.items():
        r = one_device(dev, out, ans)
        res[dev] = r
        print(f"== {dev} (CHECK ONLY, not a verdict)  W_mixed {r['W_mixed']:.3f}; recomputed M vs scores.json worst "
              f"{r['check_circuit_M_worst']:.1e}")
        print("arm    kept mean/min | d<0  d>0 | mirror kept mean/min | M MSE/msq raw->ps (READS raw/ps) | AGREES raw/ps "
              "| z READS raw/ps | W raw/ps (exact) | p raw/ps | MSE drop | check")
        for k, a in r["arms"].items():
            rw, ps = a["raw"], a["ps"]
            print(f"{k:6} {a['kept_mean']:.3f}/{a['kept_min']:.3f} | {a['d_neg']:.3f} {a['d_pos']:.3f} | "
                  f"{a['mirror_kept_mean']:.3f}/{a['mirror_kept_min']:.3f} | {rw['mse_over_msq']:.3f} -> "
                  f"{ps['mse_over_msq']:.3f} ({'R' if rw['reads'] else '-'}/{'R' if ps['reads'] else '-'}) | "
                  f"{rw['agrees']}/{ps['agrees']} | {rw['z_reads']}/{ps['z_reads']} | {rw['W']:.3f}/{ps['W']:.3f} "
                  f"({a['W_exact']:.3f}) | {rw['p']:.3f}/{ps['p']:.3f} | {a['mse_drop']:.1%} | {a['check_scores']:.1e}")
        f = lambda v: "none" if v is None else f"{v:.3f}"
        for arm, e in r["exponent"].items():
            print(f"{arm}: exponent log2(W6/W3) raw {f(e['raw'])} ps {f(e['ps'])} exact {e['exact']:.3f} "
                  f"(check vs scores.json {f(e['check_scores'])})")
        tot = sum(r["d_hist_all"].values())
        print("d over all user shots: " + ", ".join(f"{d:+d}: {c / tot:.3f}" for d, c in r["d_hist_all"].items()
                                                     if c / tot >= 0.001))
        print(f"circuits with fewer than {FEW} kept shots: {len(r['few_kept'])} {r['few_kept']}")
    json.dump(res, open(os.path.join(HERE, "postsel.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
