"""Score the Hubbard device job (gpu/hub_build.py), written before the run (home, 2026-11-11).
Per circuit (L, steps, arm U4 / U0 ruler) over its 2L qubits, through the user entrance's answer cards:
  1. READS if the mean squared error of the per-qubit <Z> against the exact value is at most half the mean square of
     the exact values; AGREES counted per qubit (|z - e| <= 0.05).
Reported beside, never judged and never used to correct: the amplitude ratio r = sum z e / sum e^2 (how much of the
exact pattern the device keeps) of each arm and the ratio r(U4) / r(U0) per step; the per-site charge |z_up + z_dn|
(exactly 0 for the Neel start at any U); floor, mirror, sentinel, CZ.
usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/hub_score.py OUT ANSWERS.json   (writes OUT/scores.json)
"""
import json
import os
import sys

import numpy as np


def main(out, answers_file):
    from psf_os import user2d as U
    answers = json.load(open(answers_file))
    b = json.load(open(os.path.join(out, "build.json")))
    cards = U.cards(os.path.join(out, "job"), os.path.join(out, "runs"), answers)
    res = dict(device=b["device"], circuits={}, ratio={})
    for tag in sorted(cards):
        card = cards[tag]
        L = int(tag.split("_")[0][1:])
        chain = b["chains"][str(L)]["labels"]
        q = {x["q"]: x for x in card["qubits"]}
        z = np.array([q[lab]["z"] for lab in chain])
        e = np.array([q[lab]["exact"] for lab in chain])
        mse, msq = float(np.mean((z - e) ** 2)), float(np.mean(e ** 2))
        charge = np.abs(z[0::2] + z[1::2])
        r = dict(cz=b["cz"][tag], mse=mse, mean_square=msq, reads="READS" if mse <= msq / 2 else "DOES NOT READ",
                 agrees=int(np.sum(np.abs(z - e) <= 0.05)), qubits=len(chain),
                 amplitude_ratio=float(np.dot(z, e) / np.dot(e, e)) if msq > 0 else None,
                 charge_mean=float(charge.mean()), charge_max=float(charge.max()),
                 floor=card["floor_mean"], mirror=card["mirror_mean"], sentinel=card["sentinel"],
                 z=z.round(4).tolist(), exact=e.round(4).tolist())
        res["circuits"][tag] = r
        print(f"{tag}: CZ {r['cz']}  {r['reads']} (MSE {mse:.4f} / mean square {msq:.4f})  AGREES {r['agrees']}/{len(chain)}"
              f"  r {r['amplitude_ratio']:.3f}  charge {r['charge_mean']:.3f}  floor {r['floor']:+.3f} mirror {r['mirror']:+.3f}")
    for tag in res["circuits"]:
        if tag.endswith("_U4"):
            t0 = tag[:-2] + "U0"
            a, c = res["circuits"][tag]["amplitude_ratio"], res["circuits"][t0]["amplitude_ratio"]
            res["ratio"][tag[:-3]] = a / c if c else None
            print(f"{tag[:-3]}: r(U4) / r(U0) = {res['ratio'][tag[:-3]]:.3f} (beside)")
    json.dump(res, open(os.path.join(out, "scores.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
