"""Round 6 (noiseless, exploratory): same start (theta = 0), same cost (circuit evaluations), C0 against E4 with the
exact quartic Brier minimum (toqb.s2re.train_e4). Budget: C0's 2,000 loops x 16 candidates x 4 points = 128,000
evaluations; E4 takes the whole sweeps that fit (64 + sweeps x 2 x d x 64)."""
import sys, time
import numpy as np
from toqb import task_loop as TL
from toqb import s2r2 as S2
from toqb import s2re as E
mode, L, ta, ts, seed = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
n, enc = 10, 1.5707963267948966
task = {"n": n, "layers": L, "enc": enc, "teacher_seed": ts, "teacher_angle": ta, "teacher_gap": 0.2, "n_train": 64, "n_test": 500}
Xtr, ytr, Xte, yte = S2.teacher_data2(task)
d = TL.n_params(n, L)
z = lambda th, x: TL.exact_z0(TL.angle_list(th, x, n, L, enc), n, L)
def ev(th, X, y):
    zz = np.array([z(th, x) for x in X]); return float(np.mean(np.sign(zz) == y)), S2._ce(zz, y)
BUDGET = 2000 * 16 * 4
t0 = time.perf_counter()
tag = f"teacher {ta} ts{ts} L{L}"
if mode == "zero":
    a, c = ev(np.zeros(d), Xte, yte)
    print(f"theta0 {tag}: test acc {a:.3f} CE {c:.4f}", flush=True)
elif mode == "C0":
    rng = np.random.default_rng(seed)
    rng.uniform(-1.0, 1.0, d)
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
    print(f"C0 s{seed} {tag}: test acc {a:.3f} CE {c:.4f} evals {BUDGET} ({time.perf_counter()-t0:.0f} s)", flush=True)
else:
    sweeps = (BUDGET - 64) // (2 * d * 64)
    fv = lambda th: np.array([z(th, x) for x in Xtr]); fv.y = ytr
    th = np.zeros(d)
    for s in range(1, sweeps + 1):
        th, hist = E.train_e4(fv, th, 1)
        a, c = ev(th, Xte, yte)
        print(f"E4q {tag} sweep{s}/{sweeps}: train Brier {hist[-1]:.4f} | test acc {a:.3f} CE {c:.4f} evals {64 + s * 2 * d * 64} ({time.perf_counter()-t0:.0f} s)", flush=True)
