"""Which sets the shrink lam: the trained model or the circuit? (report only, 2026-10-22, the workplace's check 3)

    python -m toqb.lam_swap RUNS_DIR OUT.json

For L 8 and 16, the final parameters trained through each arm (item 31 `psfai:template`, zipper `psfai:template_zip`)
are run on each arm's circuit; (lam, delta) come from the twin on the 64 training inputs against the exact noiseless
model (toqb.undamp.estimate, 1,024 trajectories, seed predict.seed + 5, as undamp_run). No labels, no stand-in.
"""
from __future__ import annotations

import json
import sys

import numpy as np

from toqb import s2r2 as S2
from toqb import undamp as U

ARMS = {"t": "psfai:template", "z": "psfai:template_zip"}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    runs, out_file = argv[0], argv[1]
    rows = []
    for L in (8, 16):
        for model in ("t", "z"):
            rec = json.load(open(f"{runs}/L{L}_s301-{ARMS[model].replace(':', '_')}.json"))
            theta = np.array(rec["final_mean"])
            Xtr = S2.teacher_data2(rec["task"])[0]
            for circ in ("t", "z"):
                plan = dict(name=rec["plan"], device=rec["device"], task=rec["task"], train=rec["train"],
                            predict=rec["predict"], standin=rec["standin"])
                R = S2.Runner(plan, ARMS[circ])
                lam, delta, rms = U.estimate(R, theta, Xtr, rec["task"], 1024, rec["predict"]["seed"] + 5)
                row = dict(L=L, model=model, circuit=circ, lam=float(lam), delta=float(delta), fit_rms=float(rms))
                rows.append(row)
                print(json.dumps(row), flush=True)
    json.dump(rows, open(out_file, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
