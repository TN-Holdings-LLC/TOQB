"""Score a 3D device test built with --choice (draft prereg/drafts-2026-11-06/os3d_probe_DRAFT.md): everything of
gpu/os3d_score.py (unchanged, A = the probe's translation against B = SABRE seed 0), and, when arm A0 (the first
translation) is in the job, per t R_probe = MSE_A / MSE_A0 with the same thresholds (HELPS <= 0.8, HURTS >= 1.25).

usage: PYTHONPATH=<psf-os> python gpu/os3d_probe_score.py RUN_DIR ANSWERS.json     (writes RUN_DIR/scores.json)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import os3d_score as S  # noqa: E402


def main(run, answers):
    res = S.main(run, answers)
    probe = {}
    for t in json.load(open(os.path.join(run, "report.json")))["ts"]:
        a, a0 = res["arms"][f"g3d_t{t}"], res["arms"].get(f"g3d0_t{t}")
        if a0 is None:
            continue
        R = a["mse"] / a0["mse"] if a0["mse"] > 0 else float("inf")
        probe[f"t{t}"] = dict(R=R, verdict="HELPS" if R <= S.HELPS else "HURTS" if R >= S.HURTS else "NO EFFECT")
        print(f"probe t{t}: R = MSE_A / MSE_A0 = {R:.3f}  {probe[f't{t}']['verdict']}")
    res["probe"] = probe or "A0 not in the job (the probe chose the first translation)"
    json.dump(res, open(os.path.join(run, "scores.json"), "w"), indent=1)
    return res


if __name__ == "__main__":
    main(*sys.argv[1:3])
