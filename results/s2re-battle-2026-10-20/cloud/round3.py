"""E2: the E formula iterated (Gauss-Newton, min-norm step, no random draws, no learning rate): re-linearize at the
current theta by parameter shift, then theta <- theta + pinv(G)(y tau - f). tau fixed at rms(f) at theta0 = 0."""
import sys, math, time
import numpy as np
from toqb import task_loop as TL
from toqb import s2r2 as S2
L, ta, iters = int(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
n, enc = 10, 1.5707963267948966
task = {"n": n, "layers": L, "enc": enc, "teacher_seed": 4, "teacher_angle": ta, "teacher_gap": 0.2, "n_train": 64, "n_test": 500}
Xtr, ytr, Xte, yte = S2.teacher_data2(task)
d = TL.n_params(n, L)
z = lambda th, x: TL.exact_z0(TL.angle_list(th, x, n, L, enc), n, L)
def ev(th, X, y):
    zz = np.array([z(th, x) for x in X]); return float(np.mean(np.sign(zz) == y)), S2._ce(zz, y)
t0 = time.perf_counter()
th = np.zeros(d); tau = None
for it in range(iters + 1):
    f = np.array([z(th, x) for x in Xtr])
    if tau is None:
        tau = float(np.sqrt(np.mean(f ** 2)))
    tra = float(np.mean(np.sign(f) == ytr)); res = float(np.sqrt(np.mean((ytr * tau - f) ** 2)))
    a, c = ev(th, Xte, yte)
    print(f"E2 ta={ta} L{L} it{it}: train acc {tra:.3f} resid {res:.4f} | test acc {a:.3f} CE {c:.4f} |theta|max {np.abs(th).max():.3f} ({time.perf_counter()-t0:.0f} s)", flush=True)
    if it == iters:
        break
    G = np.zeros((len(Xtr), d))
    for k in range(d):
        e = np.zeros(d); e[k] = math.pi / 2
        G[:, k] = [(z(th + e, x) - z(th - e, x)) / 2 for x in Xtr]
    th = th + np.linalg.pinv(G) @ (ytr * tau - f)
