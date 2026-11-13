"""Is the device's error structured or random? (workplace, 2026-11-13; owner: "ノイズに規則性があるかランダム化を計測
できる？"; desk only, from released records, nothing corrected).

Per circuit of the hub_score records (z and exact per qubit in scores.json), split z = r e + rest (rest orthogonal to e,
as notes/paper9/r_thread_2026-11-13) and compare:
  1. the rest's variance with the shot variance of the same circuit, mean of (1 - z^2) / shots: random shot noise alone
     would give a ratio near 1;
  2. the rest's correlation between neighbouring qubits on the chain;
  3. the same circuit on the same qubits on two days: hubbard 11-11 L20_s4_U4 and hub-dt 11-12 L20_T1.0_s4 (same exact
     values, same chain, same physical placement, both ibm_fez): correlation of the two rests.
usage: python noise_structure.py   (from this folder; prints a table, writes noise_structure.json)
"""
import json
import os

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
SRC = (("hubbard 11-11", "results/hubbard-2026-11-11/ibm_fez"), ("hubbard-big 11-11", "results/hubbard-big-2026-11-11/ibm_fez"),
       ("hub-dt 11-12", "results/hub-dt-2026-11-12/ibm_fez"), ("xx91 11-12", "results/xx91-2026-11-12/ibm_fez"))
SHOTS = 4000


def load(p):
    return json.load(open(os.path.join(ROOT, p)))


def split(z, e):
    z, e = np.asarray(z, float), np.asarray(e, float)
    r = float(z @ e / (e @ e))
    return r, z - r * e


def main():
    out = dict(circuits=[])
    for name, d in SRC:
        for tag, c in sorted(load(d + "/scores.json")["circuits"].items()):
            z = np.asarray(c["z"])
            r, rest = split(c["z"], c["exact"])
            shot = float(np.mean((1 - z ** 2) / SHOTS))
            row = dict(record=name, circuit=tag, r=r, rest_var=float(np.mean(rest ** 2)), shot_var=shot,
                       rest_over_shot=float(np.mean(rest ** 2) / shot),
                       neighbour_corr=float(np.corrcoef(rest[:-1], rest[1:])[0, 1]))
            out["circuits"].append(row)
            print(f"{name:17s} {tag:16s} r {r:.2f}  rest / shot variance {row['rest_over_shot']:6.1f}  "
                  f"neighbour corr {row['neighbour_corr']:+.2f}")
    a = load(SRC[0][1] + "/scores.json")["circuits"]["L20_s4_U4"]
    b = load(SRC[2][1] + "/scores.json")["circuits"]["L20_T1.0_s4"]
    same_exact = bool(np.allclose(a["exact"], b["exact"], atol=1e-3))
    same_place = load(SRC[0][1] + "/runs/p2d_L20_s4_U4.json")["mapping"] == load(SRC[2][1] + "/runs/p2d_L20_T1.0_s4.json")["mapping"]
    corr = float(np.corrcoef(split(a["z"], a["exact"])[1], split(b["z"], b["exact"])[1])[0, 1])
    out["two_days"] = dict(circuits=["hubbard 11-11 L20_s4_U4", "hub-dt 11-12 L20_T1.0_s4"], same_exact=same_exact,
                           same_placement=same_place, rest_correlation=corr)
    ratios = [x["rest_over_shot"] for x in out["circuits"]]
    nc = [x["neighbour_corr"] for x in out["circuits"]]
    print(f"rest / shot variance {min(ratios):.1f}-{max(ratios):.1f} over {len(ratios)} circuits; neighbour corr "
          f"{min(nc):+.2f} to {max(nc):+.2f}; same circuit and qubits on two days: rest correlation {corr:.3f} "
          f"(same exact {same_exact}, same placement {same_place})")
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "noise_structure.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
