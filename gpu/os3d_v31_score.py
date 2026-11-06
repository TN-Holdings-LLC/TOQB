"""Score the job of gpu/os3d_v31_build.py (draft prereg/drafts-2026-11-06/os3d_v31_DRAFT.md).

The 3D arm judged is the one the job's own probes choose (psf_os.grid3d.probe_choose: the first candidate whose
touched qubits all read |0> floor >= 0.8 and |1> floor <= -0.8; if none, candidate 0, marked "probe passed none").
Judged per t, for that 3D arm and for the 2D arm, against the exact answers: READS, AGREES, BEATS
(gpu/practice_score.judge, unchanged). Beside: retention, normalised error, CZ and layers, floor, mirror, the probe
readings, every other candidate's scores (shown, never judged), the price of the dimension (3D / 2D CZ, layers,
retention), the sentinel.

usage: PYTHONPATH=<psf-os> python gpu/os3d_v31_score.py RUN_DIR ANSWERS.json [relative|best|mirror|gate]
The probe rule is fixed by the declaration: "relative" (first clean candidate) or "best" (owner's "white of white":
the clean candidate whose weakest touched qubit reads best).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from practice_score import judge  # noqa: E402


def main(run, answers, rule="relative"):
    from psf_os import grid3d as G
    from psf_os import user2d as U
    rep = json.load(open(os.path.join(run, "report.json")))
    job, runs = os.path.join(run, "job"), os.path.join(run, "runs")
    cs = U.cards(job, runs, json.load(open(answers)))
    if rule == "mirror":
        # draft rule (2026-11-07, after the 11-07 run; to be declared and tested before use): candidates marked by the
        # probes (relative line) are passed over; among the rest (all, if none is clean), the one whose own t = 1 arm
        # has the highest mean mirror. Reads the probes and the arms' mirror check circuits, never an answer.
        ch = G.probe_choose(job, runs, rule="relative")
        t1 = min(rep["ts"])
        for r in ch["candidates"]:
            r["mirror_t1"] = cs[f"g3d{r['index']}_t{t1}"]["mirror_mean"]
        clean = [r for r in ch["candidates"] if not r["low"]] or ch["candidates"]
        best = max(clean, key=lambda r: (r["mirror_t1"], -r["index"]))
        ch.update(rule="mirror", chosen=best["index"], passed_none=not any(not r["low"] for r in ch["candidates"]))
    elif rule == "gate":
        # draft rule (2026-11-07, owner: the test after choosing must work as a gate; to be declared and tested before
        # use). Candidates in order of their own t = 1 mirror (the arm's gates and bridges in operation, run back and
        # forth). The first one that passes the gate is judged: (a) no site of its t = 1 mirror below the job's mirror
        # median - max(5 x 1.4826 MAD, 0.05) over all candidates' t = 1 mirror sites, (b) no qubit marked by the
        # |1> floor (relaxation, which a mirror cannot see), (c) its mean t = 1 mirror within 0.1 of the best mean.
        # If none passes: nothing 3D is judged ("no healthy place"). Never reads an answer.
        import numpy as np
        ch = G.probe_choose(job, runs, rule="relative")
        t1 = min(rep["ts"])
        msites = {}
        for r in ch["candidates"]:
            q = cs[f"g3d{r['index']}_t{t1}"]["qubits"]
            msites[r["index"]] = [x["mirror"] for x in q]
            r["mirror_t1"] = float(np.mean(msites[r["index"]]))
        allm = np.array([v for vs in msites.values() for v in vs])
        med = float(np.median(allm))
        line_m = med - max(5 * 1.4826 * float(np.median(np.abs(allm - med))), 0.05)
        top = max(r["mirror_t1"] for r in ch["candidates"])
        chosen_r = None
        for r in sorted(ch["candidates"], key=lambda r: (-r["mirror_t1"], r["index"])):
            f1_marked = [q for q, v in r.get("floor1", {}).items() if ch["line1"] is not None and v > ch["line1"]]
            r["gate"] = dict(mirror_low_sites=int(sum(v < line_m for v in msites[r["index"]])), floor1_marked=f1_marked,
                             within_best=r["mirror_t1"] >= top - 0.1)
            r["gate"]["pass"] = (r["gate"]["mirror_low_sites"] == 0 and not f1_marked and r["gate"]["within_best"])
            if chosen_r is None and r["gate"]["pass"]:
                chosen_r = r
        ch.update(rule="gate", line_mirror=line_m, chosen=None if chosen_r is None else chosen_r["index"],
                  passed_none=chosen_r is None)
    else:
        ch = G.probe_choose(job, runs, rule=rule)
    if rule == "gate" and ch["chosen"] is None:
        res = dict(device=rep["device"], probe=ch, chosen=None, verdict="no healthy place: nothing 3D judged")
        json.dump(res, open(os.path.join(run, "scores.json"), "w"), indent=1, default=str)
        print(res["verdict"])
        for r in ch["candidates"]:
            print(f"  candidate {r['index']}: mirror t1 {r['mirror_t1']:.3f}  gate {r['gate']}")
        return res
    chosen = ch["chosen"] if ch["chosen"] is not None else 0
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
               chosen=chosen, probe_passed_none=ch.get("passed_none", ch["chosen"] is None), judged=judged, arms=arms,
               price=price)
    json.dump(res, open(os.path.join(run, "scores.json"), "w"), indent=1)
    print(f"{res['device']}  sentinel {res['sentinel']}  probe chose candidate {chosen}"
          + ("  (probe passed none)" if res["probe_passed_none"] else ""))
    for r in ch["candidates"]:
        print(f"  candidate {r['index']} (r0 {r['r0']}, c0 {r['c0']}): |0> floor min {r.get('min_floor', float('nan')):.3f}"
              f"  |1> floor max {r.get('max_floor1', float('nan')):.3f}  X echo min {r.get('min_echo_x', float('nan')):.3f}"
              f"  weakest {r.get('worst', float('nan')):.3f}"
              + (f"  mirror t1 {r['mirror_t1']:.3f}" if "mirror_t1" in r else "") + f"  marked: {r['low']}"
              + (f"  gate {'PASS' if r['gate']['pass'] else 'FAIL'} {r['gate']}" if "gate" in r else ""))
    for tag, r in sorted(arms.items(), key=lambda kv: (kv[1]["kind"], kv[1].get("candidate") or 0, kv[1]["t"])):
        mark = "JUDGED" if (r["kind"] == "2D" or r["candidate"] == chosen) else "beside"
        ret = "-" if r["retention"] is None else f"{r['retention']:.3f}"
        print(f"{tag:9} {mark:6} {r['reads']:13} {r['agrees']:8} {r['beats']:13} M {r['M']:+.3f} exact "
              f"{r['M_exact']:+.3f} MSE {r['mse']:.4f}/{r['trivial_guess_mse']:.4f} retention {ret} CZ {r['cz']}"
              f" floor {r['floor_mean']:.3f} mirror {r['mirror_mean']:.3f}")
    return res


if __name__ == "__main__":
    main(*sys.argv[1:4])   # RUN_DIR ANSWERS [relative | best]
