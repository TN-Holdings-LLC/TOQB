"""The untrained model (theta = 0, design C's start) through one arm: the twin's prediction and the stand-in's exact
P(1) on the test points (report and baseline, 2026-10-23).

    python -m toqb.theta0_eval PLAN.json SPEC OUT.json        (TOQB_XP=cupy on the GPU)

At theta = 0 both arms run the same logical model, so a difference between arms is the circuit's readout; against a
trained run of the same plan, the change from theta = 0 is what the training added (toqb.far_score's rule B).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

from toqb import s2r2 as S2
from toqb import task_loop as TL
from toqb.fruit_common import predict_verify


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 1
    plan_file, spec, out = argv
    if os.path.exists(out):
        print(f"STOP: {out} exists: an output is never overwritten", file=sys.stderr)
        return 2
    plan = json.load(open(plan_file, encoding="utf-8"))
    task = plan["task"]
    R = S2.Runner(plan, spec)
    _, _, Xte, yte = S2.teacher_data2(task)
    o = predict_verify(R, np.zeros(TL.n_params(task["n"], task["layers"])), Xte, yte, plan["predict"],
                       verify=plan.get("verify", True))
    rec = dict(kind="theta0", arm=spec, plan=plan.get("name"), task=task, test_labels=[int(v) for v in yte],
               prediction=o["prediction"], rehearsal=o["rehearsal"])
    json.dump(rec, open(out, "w", encoding="utf-8"))
    print(f"theta = 0, {spec}: stand-in acc {o['rehearsal']['acc']:.3f} (with shots), CE {o['rehearsal']['ce']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
