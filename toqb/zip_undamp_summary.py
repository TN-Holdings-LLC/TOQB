"""Summary of the undamped readout on the zipper comparison (report only, declared in
prereg/drafts-2026-10-22/zip_undamp_note.md):

    python -m toqb.zip_undamp_summary RUNS_DIR UNDAMP_DIR > summary.md

Per run: lam, delta; the stand-in CE / accuracy, raw and undamped; whether each falls in its prediction's 99 % interval;
and W12's check on the trained model itself: the mean |z| of its exact noiseless output on the test points, with the
noiseless CE and accuracy (is a small output the model's own or the noise's).
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

from toqb import s2r2 as S2
from toqb import undamp as U
from toqb.s2rc import _scores


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    runs, und = argv[0], argv[1]
    print("| run | lam | delta | stand-in CE raw -> undamped | acc raw -> undamped | inside raw / undamped | "
          "noiseless mean abs z | noiseless CE / acc |")
    print("|---|---|---|---|---|---|---|---|")
    for f in sorted(glob.glob(os.path.join(runs, "*.json"))):
        name = os.path.basename(f)[:-5]
        uf = os.path.join(und, name + ".json")
        if not os.path.exists(uf):
            print(f"| {name} | (no undamp output) |")
            continue
        rec, u = json.load(open(f)), json.load(open(uf))
        p = u["points"][-1]
        _, _, Xte, yte = S2.teacher_data2(rec["task"])
        zi = U.ideal_z(np.array(rec["final_mean"]), Xte, rec["task"])
        ce0, acc0 = _scores(zi, np.asarray(yte))
        print(f"| {name} | {p['lam']:.3f} | {p['delta']:+.3f} | {p['raw']['ce']:.4f} -> {p['undamped']['ce']:.4f} | "
              f"{p['raw']['acc']:.3f} -> {p['undamped']['acc']:.3f} | {p['raw']['inside']} / {p['undamped']['inside']} | "
              f"{float(np.mean(np.abs(zi))):.3f} | {ce0:.4f} / {acc0:.3f} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
