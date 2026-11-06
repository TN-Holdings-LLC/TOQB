"""Score the 3D device test (prereg/os3d_device_2026-11-06.md) on one device; fixed with the declaration, before
any run. RUN_DIR is the folder written by gpu/os3d_compare_build.py (job/, runs/, report.json).

Per arm and t (as 2D; gpu/practice_score.judge, unchanged): READS, AGREES, BEATS. Per t: R = MSE_A / MSE_B with A =
g3d_t<t> (v3 fold) and B = sabre_t<t> (SABRE seed 0): HELPS if R <= 0.8, HURTS if R >= 1.25, NO EFFECT between.
Reported beside, not judged: retention M / M_exact (|M_exact| >= 0.1), the normalised error, the share within 2 SE,
CZ and CZ layers, floor and mirror means, the sentinel, and, if present in RUN_DIR, the CALIB_BESIDE_submit.json and
CALIB_BESIDE_run.json lines of each arm (report only).

usage: PYTHONPATH=<psf-os> python gpu/os3d_score.py RUN_DIR ANSWERS.json      (writes RUN_DIR/scores.json)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from practice_score import judge  # noqa: E402

HELPS, HURTS = 0.8, 1.25


def main(run, answers):
    from psf_os import user2d as U
    rep = json.load(open(os.path.join(run, "report.json")))
    cs = U.cards(os.path.join(run, "job"), os.path.join(run, "runs"), json.load(open(answers)))
    calib = {}
    for k in ("submit", "run"):
        f = os.path.join(run, f"CALIB_BESIDE_{k}.json")
        if os.path.exists(f):
            calib[k] = json.load(open(f))["arms"]
    res = dict(device=rep["device"], sentinel=next(iter(cs.values()))["sentinel"], arms={}, compare={})
    for tag, c in cs.items():
        r = judge(c)
        q = [x for x in c["qubits"] if "exact" in x]
        r["within_2se"] = sum(abs(x["z"] - x["exact"]) <= x["two_se"] for x in q) / len(q)
        r["retention"] = r["M"] / r["M_exact"] if abs(r["M_exact"]) >= 0.1 else None
        r["norm_error"] = abs(r["diff"]) / abs(r["M_exact"]) if r["M_exact"] else None
        r["cz"], r["cz_layers"] = rep["arms"][tag]["cz"], rep["arms"][tag]["cz_layers"]
        r["calib_beside"] = {k: v.get(f"p2d_{tag}") for k, v in calib.items()}
        res["arms"][tag] = r
    for t in rep["ts"]:
        a, b = res["arms"][f"g3d_t{t}"], res["arms"][f"sabre_t{t}"]
        R = a["mse"] / b["mse"] if b["mse"] > 0 else float("inf")
        res["compare"][f"t{t}"] = dict(R=R, verdict="HELPS" if R <= HELPS else "HURTS" if R >= HURTS else "NO EFFECT")
    json.dump(res, open(os.path.join(run, "scores.json"), "w"), indent=1)
    print(f"{res['device']}  sentinel {res['sentinel']}")
    for tag, r in res["arms"].items():
        ret = "-" if r["retention"] is None else f"{r['retention']:.3f}"
        print(f"{tag:9} {r['reads']:13} {r['agrees']:8} {r['beats']:13} M {r['M']:+.3f} exact {r['M_exact']:+.3f} "
              f"MSE {r['mse']:.4f} / guess {r['trivial_guess_mse']:.4f}  retention {ret}  CZ {r['cz']} "
              f"({r['cz_layers']} layers)  floor {r['floor_mean']:.3f}  mirror {r['mirror_mean']:.3f}")
        for k, v in r["calib_beside"].items():
            if v:
                print(f"          calib {k}: worst CZ {v['cz']['worst']} at {v['cz']['at']}, worst readout "
                      f"{v['readout']['worst']} at {v['readout']['at']}")
    for t, v in res["compare"].items():
        print(f"{t}: R = {v['R']:.3f}  {v['verdict']}")
    return res


if __name__ == "__main__":
    main(*sys.argv[1:3])
