"""Noiseless test fit of the test match's final parameters: exact <Z0> on the 500 test points (accuracy, CE), beside
the noiseless training accuracy, to separate overfitting from the noise's shrinkage of the outputs."""
import json, glob, sys, time
import numpy as np
from toqb import task_loop as TL
from toqb import s2r2 as S2
runs = sys.argv[1]
for L in (16, 8):
    for ts in (4, 5, 6):
        task = {"n": 10, "layers": L, "enc": 1.5707963267948966, "teacher_seed": ts, "teacher_angle": 1.0, "teacher_gap": 0.2, "n_train": 64, "n_test": 500}
        t0 = time.time()
        Xtr, ytr, Xte, yte = S2.teacher_data2(task)
        z = lambda th, X: np.array([TL.exact_z0(TL.angle_list(th, x, 10, L, task["enc"]), 10, L) for x in X])
        d = TL.n_params(10, L)
        out = []
        for role, th in [("theta0", np.zeros(d))] + [(f.split("/")[-1][1:3], np.array(json.load(open(f))["final_mean"])) for f in sorted(glob.glob(f"{runs}/*_L{L}_t{ts}-*.json")) if "Z_" not in f]:
            ftr, fte = z(th, Xtr), z(th, Xte)
            out.append(f"{role} train acc {np.mean(np.sign(ftr) == ytr):.3f} test acc {np.mean(np.sign(fte) == yte):.3f} test CE {S2._ce(fte, yte):.4f}")
        print(f"L{L} t{ts} ({time.time()-t0:.0f} s): " + " | ".join(out), flush=True)
