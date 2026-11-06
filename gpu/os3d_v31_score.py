"""Score the job of gpu/os3d_v31_build.py (draft prereg/drafts-2026-11-06/os3d_v31_DRAFT.md).

The 3D arm judged is the one the job's own probes choose (psf_os.grid3d.probe_choose: the first candidate whose
touched qubits all read |0> floor >= 0.8 and |1> floor <= -0.8; if none, candidate 0, marked "probe passed none").
Judged per t, for that 3D arm and for the 2D arm, against the exact answers: READS, AGREES, BEATS
(gpu/practice_score.judge, unchanged). Beside: retention, normalised error, CZ and layers, floor, mirror, the probe
readings, every other candidate's scores (shown, never judged), the price of the dimension (3D / 2D CZ, layers,
retention), the sentinel.

usage: PYTHONPATH=<psf-os> python gpu/os3d_v31_score.py RUN_DIR ANSWERS.json     (writes RUN_DIR/scores.json)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from practice_score import judge  # noqa: E402


def main(run, answers):
    from psf_os import grid3d as G
    from psf_os import user2d as U
    rep = json.load(open(os.path.join(run, "report.json")))
    job, runs = os.path.join(run, "job"), os.path.join(run, "runs")
    ch = G.probe_choose(job, runs)
    chosen = ch["chosen"] if ch["chosen"] is not None else 0
    cs = U.cards(job, runs, json.load(open(answers)))
    arms = {}
    for tag, c in cs.items():
        if tag not in rep["arms"]:
            continue
        r = judge(c)
        r["retention"] = r["M"] / r["M_exact"] if abs(r["M_exact"]) >= 0.1 else None
        r["norm_error"] = abs(r["diff"]) / abs(r["M_exact"]) if r["M_exact"] else None
        r.update({k: rep["arms"][tag].get(k) for k in ("kind", "candidate", "t", "cz", "cz_layers")})
        arms[tag] = r
    judged, price = {}, {}
    for t in rep["ts"]:
        a3, a2 = arms[f"g3d{chosen}_t{t}"], arms[f"hex_t{t}"]
        judged[f"t{t}"] = {"3D": {k: a3[k] for k in ("reads", "agrees", "beats")},
                           "2D": {k: a2[k] for k in ("reads", "agrees", "beats")}}
        price[f"t{t}"] = dict(cz_ratio=a3["cz"] / a2["cz"] if a2["cz"] else None,
                              retention_3d=a3["retention"], retention_2d=a2["retention"])
    res = dict(device=rep["device"], sentinel=next(iter(cs.values()))["sentinel"], probe=ch,
               chosen=chosen, probe_passed_none=ch["chosen"] is None, judged=judged, arms=arms, price=price)
    json.dump(res, open(os.path.join(run, "scores.json"), "w"), indent=1)
    print(f"{res['device']}  sentinel {res['sentinel']}  probe chose candidate {ch['chosen']}"
          + ("  (passed none: candidate 0 judged)" if ch["chosen"] is None else ""))
    for r in ch["candidates"]:
        print(f"  candidate {r['index']} (r0 {r['r0']}, c0 {r['c0']}): |0> floor min {r.get('min_floor', float('nan')):.3f}"
              f"  |1> floor max {r.get('max_floor1', float('nan')):.3f}  outside +-{ch['threshold']}: {r['low']}")
    for tag, r in sorted(arms.items(), key=lambda kv: (kv[1]["kind"], kv[1].get("candidate") or 0, kv[1]["t"])):
        mark = "JUDGED" if (r["kind"] == "2D" or r["candidate"] == chosen) else "beside"
        ret = "-" if r["retention"] is None else f"{r['retention']:.3f}"
        print(f"{tag:9} {mark:6} {r['reads']:13} {r['agrees']:8} {r['beats']:13} M {r['M']:+.3f} exact "
              f"{r['M_exact']:+.3f} MSE {r['mse']:.4f}/{r['trivial_guess_mse']:.4f} retention {ret} CZ {r['cz']}"
              f" floor {r['floor_mean']:.3f} mirror {r['mirror_mean']:.3f}")
    return res


if __name__ == "__main__":
    main(*sys.argv[1:3])
