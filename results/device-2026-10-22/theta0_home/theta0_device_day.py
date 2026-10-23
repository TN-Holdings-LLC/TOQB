"""Post hoc (home, 2026-10-23): the device day's task (teacher 4, angle 0.3) at theta = 0 against the trained runs,
noiseless (exact <Z> of the logical model). Run from the TOQB root:
    python results/device-2026-10-22/theta0_home/theta0_device_day.py
"""
import glob
import json

import numpy as np

from toqb import s2r2 as S2
from toqb import task_loop as TL
from toqb import undamp as U
from toqb.s2rc import _scores

seen = {}
for f in sorted(glob.glob("results/device-2026-10-22/runs/*.json")):
    r = json.load(open(f))
    t = r["task"]
    k = json.dumps(t, sort_keys=True)
    if k not in seen:
        seen[k] = S2.teacher_data2(t)
        _, _, X, y = seen[k]
        assert np.array_equal(np.asarray(y), np.asarray(r["test_labels"])), f
        ce, acc = _scores(U.ideal_z(np.zeros(TL.n_params(t["n"], t["layers"])), X, t), np.asarray(y))
        print(f"L {t['layers']}: theta = 0 noiseless CE {ce:.4f}, accuracy {acc:.3f} ({len(y)} test points)")
    _, _, X, y = seen[k]
    assert np.array_equal(np.asarray(y), np.asarray(r["test_labels"])), f
    ce, acc = _scores(U.ideal_z(np.asarray(r["final_mean"]), X, t), np.asarray(y))
    print(f"  {f.split('/')[-1]}: trained noiseless CE {ce:.4f}, accuracy {acc:.3f}")
