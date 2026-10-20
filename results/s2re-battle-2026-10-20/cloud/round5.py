"""E4: E3's exact per-parameter solve with a proper scoring rule instead of C's linear loss.
Per parameter, every training point's output is exactly f_i(u) = a_i + b_i cos u + c_i sin u (three circuit values per
point). The loss along u is then an explicit function: 'ce' -mean log((1 + y f)/2) (the score's own CE, p = (1 + f)/2) or
'brier' mean ((f - y)/2)^2. Its global minimum over one period is found on the explicit formula (dense grid of 4096
angles, then a parabola polish); no further circuit calls, no random draws, no learning rate."""
import sys, time
import numpy as np
from toqb import task_loop as TL
from toqb import s2r2 as S2
loss, L, ta, sweeps = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
n, enc = 10, 1.5707963267948966
task = {"n": n, "layers": L, "enc": enc, "teacher_seed": 4, "teacher_angle": ta, "teacher_gap": 0.2, "n_train": 64, "n_test": 500}
Xtr, ytr, Xte, yte = S2.teacher_data2(task)
d = TL.n_params(n, L)
z = lambda th, x: TL.exact_z0(TL.angle_list(th, x, n, L, enc), n, L)
fv = lambda th: np.array([z(th, x) for x in Xtr])
def lossf(F):  # F: (..., m)
    if loss == "ce":
        p = np.clip((1 + F * ytr) / 2, 1e-4, 1)
        return -np.log(p).mean(axis=-1)
    return (((F - ytr) / 2) ** 2).mean(axis=-1)
def ev(th, X, y):
    zz = np.array([z(th, x) for x in X]); return float(np.mean(np.sign(zz) == y)), S2._ce(zz, y)
U = np.linspace(-np.pi, np.pi, 4096, endpoint=False)
CU, SU = np.cos(U), np.sin(U)
t0 = time.perf_counter()
th = np.zeros(d); f = fv(th); hp = np.pi / 2
for s in range(sweeps + 1):
    a_, c_ = ev(th, Xte, yte)
    print(f"E4-{loss} ta={ta} L{L} sweep{s}: train loss {float(lossf(f)):.4f} acc {np.mean(np.sign(f) == ytr):.3f} | test acc {a_:.3f} CE {c_:.4f} |theta|max {np.abs(th).max():.3f} ({time.perf_counter()-t0:.0f} s)", flush=True)
    if s == sweeps:
        break
    for k in range(d):
        e = np.zeros(d); e[k] = hp
        fp, fm = fv(th + e), fv(th - e)
        a = (fp + fm) / 2; b = f - a; c = (fp - fm) / 2
        F = a[None, :] + CU[:, None] * b[None, :] + SU[:, None] * c[None, :]
        Lu = lossf(F)
        j = int(np.argmin(Lu)); u = U[j]
        l0, l1, l2 = Lu[j - 1], Lu[j], Lu[(j + 1) % len(U)]
        den = l0 - 2 * l1 + l2
        if den > 0:
            u += 0.5 * (l0 - l2) / den * (U[1] - U[0])
        if lossf(a + b * np.cos(u) + c * np.sin(u)) <= lossf(f):
            th[k] += u
            f = a + b * np.cos(u) + c * np.sin(u)
