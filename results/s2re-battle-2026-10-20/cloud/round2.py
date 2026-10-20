"""C's update rule, noiseless (exact <Z0> instead of the twin), from a chosen start; and E at a chosen teacher scale."""
import sys, math, time, json
import numpy as np
from toqb import task_loop as TL
from toqb import s2r2 as S2
mode, L, seed, start, ta = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], float(sys.argv[5])
n, enc = 10, 1.5707963267948966
task = {"n": n, "layers": L, "enc": enc, "teacher_seed": 4, "teacher_angle": ta, "teacher_gap": 0.2, "n_train": 64, "n_test": 500}
Xtr, ytr, Xte, yte = S2.teacher_data2(task)
d = TL.n_params(n, L)
z = lambda th, x: TL.exact_z0(TL.angle_list(th, x, n, L, enc), n, L)
def ev(th, X, y):
    zz = np.array([z(th, x) for x in X]); return float(np.mean(np.sign(zz) == y)), S2._ce(zz, y)
t0 = time.perf_counter()
if mode == "C":
    rng = np.random.default_rng(seed)
    m = rng.uniform(-1.0, 1.0, d)          # as s2rc (init 1.0); the draw is kept so the stream matches
    if start == "zero":
        m = np.zeros(d)
    K, b, h, lr = 8, 4, 0.1, 0.4
    for k in range(1, 2001):
        idx = rng.choice(len(Xtr), b, replace=False)
        D = rng.choice([-1.0, 1.0], (K, d))
        cands = np.vstack([m[None, :] + h * D, m[None, :] - h * D])
        zs = np.array([[z(th, Xtr[i]) for i in idx] for th in cands])
        ls = ((1 - zs * ytr[idx][None, :]) / 2).mean(axis=1)
        g = (((ls[:K] - ls[K:]) / (2 * h))[:, None] * D).mean(axis=0)
        m = m - lr * g
    a, c = ev(m, Xte, yte)
    print(f"C start={start} teacher_angle={ta} L{L} s{seed}: test acc {a:.3f} CE {c:.4f} ({time.perf_counter()-t0:.0f} s)", flush=True)
else:
    th0 = np.zeros(d)
    f0 = np.array([z(th0, x) for x in Xtr])
    G = np.zeros((len(Xtr), d))
    for k in range(d):
        e = np.zeros(d); e[k] = math.pi / 2
        G[:, k] = [(z(th0 + e, x) - z(th0 - e, x)) / 2 for x in Xtr]
    tau = float(np.sqrt(np.mean(f0 ** 2)))
    w = np.linalg.pinv(G) @ (ytr * tau - f0)
    a, c = ev(w, Xte, yte); a0, c0 = ev(th0, Xte, yte)
    print(f"E teacher_angle={ta} L{L}: test acc {a:.3f} CE {c:.4f}; theta=0: acc {a0:.3f} CE {c0:.4f} ({time.perf_counter()-t0:.0f} s)", flush=True)
