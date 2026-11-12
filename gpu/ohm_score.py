"""Score the Ohm device job (gpu/ohm_build.py), written before the run (workplace, 2026-11-12; not declared).

The measure: the transferred magnetization of each circuit, M = (number of |1> on the right half at the end) - (at
the start), in quanta (one quantum = one spin moved), from the per-qubit <Z> of the user entrance's answer cards:
M = sum over the right half of (1 - z) / 2 minus the string's own count of 1 on the right. It is the quantity whose
growth in time the question is about; it is exact per circuit (each circuit is one product state), so the device is
compared with the exact value of the same string, and the spread between strings is not part of the comparison.
Per arm (A0 / A1 / A2) and cycle count, over its 2K circuits (K strings and their complements):
  READS if the mean squared difference of M (device - exact) is at most half the mean square of the exact M;
  AGREES counted per circuit, |M_device - M_exact| <= 0.2 quanta (0.01 per right-half qubit at N 40; about three
  times the shot error of one circuit at 1000 shots, per-shot variance of the count up to 3.5 by the design check).
Reported beside, never judged and never used to correct:
  the wall's transfer W(t) = mean over strings of (M_s - M_c) / 2 (string minus its complement), device and exact, and
  its exponent log2(W(6) / W(3)) per arm; the prediction is about this ordering (A0 > A1 > A2);
  the drift D(t) = mean of (M_s + M_c) / 2 (decay towards |0> lowers both; the exact value is near 0);
  the per-qubit <Z> verdict of every circuit as hub_score (MSE <= half the mean square), floor, mirror, sentinel, CZ.
usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/ohm_score.py OUT ANSWERS_BY_LABEL.json   (writes OUT/scores.json)
"""
import json
import os
import sys

import numpy as np

AGREE = 0.2


def main(out, answers_file):
    from psf_os import user2d as U
    A = json.load(open(answers_file))
    b = json.load(open(os.path.join(out, "build.json")))
    cards = U.cards(os.path.join(out, "job"), os.path.join(out, "runs"), A["z"])
    chain, N = b["chain"]["labels"], b["N"]
    right = chain[N // 2:]
    res = dict(device=b["device"], circuits={}, arms={})
    for tag in sorted(cards):
        arm, tt, name = tag.split("_")
        bits = b["strings"][name]
        m0 = sum(int(x) for x in bits[N // 2:])
        q = {x["q"]: x for x in cards[tag]["qubits"]}
        z = np.array([q[lab]["z"] for lab in chain])
        e = np.array([q[lab]["exact"] for lab in chain])
        zr, er = np.array([q[lab]["z"] for lab in right]), np.array([q[lab]["exact"] for lab in right])
        Md, Me = float(((1 - zr) / 2).sum() - m0), float(((1 - er) / 2).sum() - m0)
        mse_z, msq_z = float(np.mean((z - e) ** 2)), float(np.mean(e ** 2))
        res["circuits"][tag] = dict(cz=b["cz"][tag], M=Md, M_exact=Me,
                                    z_reads="READS" if mse_z <= msq_z / 2 else "DOES NOT READ",
                                    z_mse=mse_z, z_mean_square=msq_z, floor=cards[tag]["floor_mean"],
                                    mirror=cards[tag]["mirror_mean"], sentinel=cards[tag]["sentinel"])
    for arm in sorted({t.split("_")[0] for t in res["circuits"]}):
        for t in b["cycles"]:
            c = {n: res["circuits"][f"{arm}_t{t}_{n}"] for n in b["strings"]}
            d = np.array([c[n]["M"] - c[n]["M_exact"] for n in c])
            ex = np.array([c[n]["M_exact"] for n in c])
            mse, msq = float(np.mean(d ** 2)), float(np.mean(ex ** 2))
            ks = sorted({n[1:] for n in c})
            W = float(np.mean([(c["s" + k]["M"] - c["c" + k]["M"]) / 2 for k in ks]))
            We = float(np.mean([(c["s" + k]["M_exact"] - c["c" + k]["M_exact"]) / 2 for k in ks]))
            D = float(np.mean([(c["s" + k]["M"] + c["c" + k]["M"]) / 2 for k in ks]))
            De = float(np.mean([(c["s" + k]["M_exact"] + c["c" + k]["M_exact"]) / 2 for k in ks]))
            res["arms"][f"{arm}_t{t}"] = dict(reads="READS" if mse <= msq / 2 else "DOES NOT READ", mse=mse,
                                              mean_square=msq, agrees=int(np.sum(np.abs(d) <= AGREE)),
                                              circuits=len(c), W=W, W_exact=We, D=D, D_exact=De,
                                              z_reads=sum(c[n]["z_reads"] == "READS" for n in c))
            r = res["arms"][f"{arm}_t{t}"]
            print(f"{arm} t {t}: {r['reads']} (MSE {mse:.4f} / mean square {msq:.4f}), AGREES {r['agrees']}/{len(c)}; "
                  f"beside: W {W:.3f} (exact {We:.3f}), D {D:+.3f} (exact {De:+.3f}), per-qubit READS "
                  f"{r['z_reads']}/{len(c)}")
    res["exponent"] = {}
    for arm in sorted({k.split("_")[0] for k in res["arms"]}):
        t3, t6 = min(b["cycles"]), max(b["cycles"])
        w = res["arms"]
        f = np.log(max(t6, 1) / t3) if t6 != t3 else None
        if f:
            ed = np.log(w[f"{arm}_t{t6}"]["W"] / w[f"{arm}_t{t3}"]["W"]) / f if w[f"{arm}_t{t3}"]["W"] > 0 and \
                w[f"{arm}_t{t6}"]["W"] > 0 else None
            ee = np.log(w[f"{arm}_t{t6}"]["W_exact"] / w[f"{arm}_t{t3}"]["W_exact"]) / f
            res["exponent"][arm] = dict(device=ed, exact=float(ee))
            print(f"{arm}: exponent {t3} -> {t6} of W: device {ed if ed is None else round(float(ed), 3)}, "
                  f"exact {ee:.3f} (beside)")
    ex = res["exponent"]
    if all(ex.get(a, {}).get("device") is not None for a in ("A0", "A1", "A2")):
        order = ex["A0"]["device"] > ex["A1"]["device"] > ex["A2"]["device"]
        res["prediction_order_kept"] = bool(order)
        print(f"prediction (A0 > A1 > A2 on the device): {'KEPT' if order else 'NOT KEPT'}")
    json.dump(res, open(os.path.join(out, "scores.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
