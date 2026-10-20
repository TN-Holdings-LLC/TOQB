import json, glob, os, sys, time, math
import numpy as np
from toqb import task_loop as TL
from toqb import s2r2 as S2
REH = sys.argv[1]
L = int(sys.argv[2])
n, enc = 10, 1.5707963267948966
task = {"n": n, "layers": L, "enc": enc, "teacher_seed": 4, "teacher_angle": 0.3, "teacher_gap": 0.2, "n_train": 64, "n_test": 500}
Xtr, ytr, Xte, yte = S2.teacher_data2(task)
d = TL.n_params(n, L)
z = lambda th, x: TL.exact_z0(TL.angle_list(th, x, n, L, enc), n, L)
t0 = time.perf_counter()
# tangent features at theta = 0, exact by the parameter-shift rule (every trainable angle is a single ry or rz)
th0 = np.zeros(d)
f0 = np.array([z(th0, x) for x in Xtr])
G = np.zeros((len(Xtr), d))
for k in range(d):
    e = np.zeros(d); e[k] = math.pi / 2
    G[:, k] = [(z(th0 + e, x) - z(th0 - e, x)) / 2 for x in Xtr]
t1 = time.perf_counter()
tau = float(np.sqrt(np.mean(f0 ** 2)))
w = np.linalg.pinv(G) @ (ytr * tau - f0)
def acc(th, X, y):
    zz = np.array([z(th, x) for x in X]); return float(np.mean(np.sign(zz) == y)), S2._ce(zz, y)
a_tr, ce_tr = acc(w, Xtr, ytr); a_te, ce_te = acc(w, Xte, yte)
print(f"L{L}: d={d}, features {t1-t0:.0f} s, tau {tau:.3f}, |w|max {np.abs(w).max():.3f} rms {np.sqrt(np.mean(w**2)):.3f}")
print(f"  E (closed form, noiseless): train acc {a_tr:.3f} CE {ce_tr:.4f}; test acc {a_te:.3f} CE {ce_te:.4f}")
a0, c0 = acc(th0, Xte, yte); print(f"  theta = 0 (no learning): test acc {a0:.3f} CE {c0:.4f}")
for f in sorted(glob.glob(f"{REH}/runs/L{L}_s*.json")):
    r = json.load(open(f)); m = np.array(r["final_mean"])
    a, c = acc(m, Xte, yte)
    print(f"  C {os.path.basename(f)[:-5]} (2,000 gradient loops, evaluated noiseless): test acc {a:.3f} CE {c:.4f}")
