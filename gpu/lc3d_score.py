"""Score a light-cone job (gpu/lc3d_build.py), written before any run. Through the user entrance's answer cards.

Occupation of site i: n_i = (1 - <Z_i>) / 2 (the probability that the flipped spin sits there; 0 everywhere in the
no-flip arm, whose exact <Z> is +1). Distance d: Manhattan distance on the 4 x 2 x 2 lattice from the source site.
  P(d, t)  = sum of n_i over the sites at distance d, flip arm; B(d, t) the same in the no-flip arm (noise background)
  S(d, t)  = P - B (the excitation's own part); its SE from the cards' per-site SE, sites taken as independent:
             SE_P = sqrt(sum (se_i / 2)^2), SE_S = sqrt(SE_P^2 + SE_B^2)
  exact    P_ex(d, t) from the sealed answers (B_ex = 0)
Choice (rule "top"): the candidate whose two t = 1 arms (flip and no flip) have the highest mean mirror; judged there.
Per judged t:
  per d <= 3: AGREES if |S - P_ex| <= 0.05, else DIFFERS; ARRIVED if S >= 0.03 and S > 3 SE_S (the same 0.03 as
             the exact arrival, and beyond the shot noise)
  the excitation kept: K(t) = sum_d S(d, t) (exact 1) and the background total sum_d B(d, t) (exact 0)
  shape: TVD(t) = 1/2 sum_d |S(d, t) / K(t) - P_ex(d, t)| (when K > 0.1)
Front, per d = 1, 2, 3: exact arrival = the first t with P_ex(d, t) >= 0.03; measured arrival = the first t with
ARRIVED (same threshold); FRONT AGREES if the two are the same t (both "none within the run" counts as the same), else FRONT DIFFERS.
Every candidate is reported beside; the sentinel as recorded.

usage: PYTHONPATH=<psf-os>:<TOQB>/gpu python gpu/lc3d_score.py OUT ANSWERS.json   (writes OUT/scores.json)
"""
import json
import os
import sys

import numpy as np

from psf_os import grid3d as G
from psf_os import user2d as U

DMAX = 3
ARRIVE_EXACT = 0.03


def main(out, answers_file):
    rep = json.load(open(os.path.join(out, "report.json")))
    answers = json.load(open(answers_file))
    L, M, N = rep["lattice"]
    sites = list(G.sites(L, M, N))
    src = tuple(rep["source"])
    dist = {str(i): sum(abs(a - b) for a, b in zip(s, src)) for i, s in enumerate(sites)}
    cards = U.cards(os.path.join(out, "job"), os.path.join(out, "runs"), answers)
    per = {}
    for tag, c in cards.items():
        q = {str(x["q"]): x for x in c["qubits"]}
        P, se2, Pex = {}, {}, {}
        for s, d in dist.items():
            P[d] = P.get(d, 0.0) + (1 - q[s]["z"]) / 2
            se2[d] = se2.get(d, 0.0) + (q[s]["two_se"] / 2 / 2) ** 2
            Pex[d] = Pex.get(d, 0.0) + (1 - q[s]["exact"]) / 2
        a = rep["arms"][tag]
        per[tag] = dict(candidate=a["candidate"], t=a["t"], flip=a["flip"], cz=a["cz"], P=P, se2=se2, Pex=Pex,
                        mirror_mean=c["mirror_mean"], floor_mean=c["floor_mean"], sentinel=c["sentinel"])
    t1 = min(rep["ts"])
    m1 = {}
    for v in per.values():
        if v["t"] == t1:
            m1.setdefault(v["candidate"], []).append(v["mirror_mean"])
    chosen = max(m1, key=lambda c: (float(np.mean(m1[c])), -c))
    res = dict(device=rep["device"], rule="top", chosen=chosen, source=rep["source"],
               sentinel=next(iter(per.values()))["sentinel"], candidates={})
    for c in sorted(m1):
        rows, arrived = {}, {}
        for t in rep["ts"]:
            f, z = per[f"lc{c}_t{t}"], per[f"lz{c}_t{t}"]
            row = dict(cz=f["cz"], mirror_flip=f["mirror_mean"], mirror_noflip=z["mirror_mean"], d={})
            K, Bt = 0.0, 0.0
            for d in range(0, max(dist.values()) + 1):
                S = f["P"][d] - z["P"][d]
                se = float(np.sqrt(f["se2"][d] + z["se2"][d]))
                K += S
                Bt += z["P"][d]
                row["d"][str(d)] = dict(S=S, B=z["P"][d], P=f["P"][d], exact=f["Pex"][d], se=se,
                                        agrees="AGREES" if abs(S - f["Pex"][d]) <= 0.05 else "DIFFERS",
                                        arrived=bool(S >= ARRIVE_EXACT and S > 3 * se))
                if 1 <= d <= DMAX and S >= ARRIVE_EXACT and S > 3 * se and str(d) not in arrived:
                    arrived[str(d)] = t
            row["K"], row["background_total"] = K, Bt
            row["tvd"] = (0.5 * sum(abs(row["d"][str(d)]["S"] / K - row["d"][str(d)]["exact"])
                                    for d in range(0, max(dist.values()) + 1)) if K > 0.1 else None)
            rows[str(t)] = row
        front = {}
        for d in range(1, DMAX + 1):
            ex = next((t for t in rep["ts"] if rows[str(t)]["d"][str(d)]["exact"] >= ARRIVE_EXACT), None)
            me = arrived.get(str(d))
            front[str(d)] = dict(exact_arrival=ex, measured_arrival=me,
                                 verdict="FRONT AGREES" if ex == me else "FRONT DIFFERS")
        res["candidates"][str(c)] = dict(judged=c == chosen, mean_t1_mirror=float(np.mean(m1[c])), rows=rows,
                                         front=front)
    json.dump(res, open(os.path.join(out, "scores.json"), "w"), indent=1)
    print(f"{rep['device']}  sentinel {res['sentinel']}  judged candidate {chosen}  source {rep['source']}")
    for c, v in res["candidates"].items():
        mark = "JUDGED" if v["judged"] else "beside"
        print(f"candidate {c} {mark} (mean t1 mirror {v['mean_t1_mirror']:.3f})")
        for t, r in v["rows"].items():
            ds = "  ".join(f"d{d} {r['d'][str(d)]['S']:+.3f}/{r['d'][str(d)]['exact']:.3f}"
                           f"{'*' if r['d'][str(d)]['arrived'] else ' '}{'' if r['d'][str(d)]['agrees'] == 'AGREES' else '!'}"
                           for d in range(0, DMAX + 1))
            tvd = f"{r['tvd']:.3f}" if r["tvd"] is not None else "-"
            print(f"  t{t} CZ {r['cz']:4}  {ds}  K {r['K']:.3f} bg {r['background_total']:.3f} TVD {tvd}")
        print("  front: " + "  ".join(f"d{d} exact t{f['exact_arrival']} measured t{f['measured_arrival']} "
                                      f"{f['verdict']}" for d, f in v["front"].items()))
    print("(S/exact per distance; * ARRIVED, ! DIFFERS)")
    return res


if __name__ == "__main__":
    main(*sys.argv[1:3])
