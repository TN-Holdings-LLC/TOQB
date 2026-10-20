"""E3: exact per-parameter closed form on C's own loss. C's loss mean((1 - y f)/2) is linear in f, and f depends on each
parameter as a + b cos u + c sin u (single rotation), so the loss along one parameter is an exact sinusoid: three
values give it, and its minimum is atan2(c, b) for mean(y f). Sweep the parameters in fixed order from theta = 0; no
random draws, no learning rate, no step size."""
import sys, time
import numpy as np
from toqb import task_loop as TL
from toqb import s2r2 as S2
L, ta, sweeps = int(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
n, enc = 10, 1.5707963267948966
task = {"n": n, "layers": L, "enc": enc, "teacher_seed": 4, "teacher_angle": ta, "teacher_gap": 0.2, "n_train": 64, "n_test": 500}
Xtr, ytr, Xte, yte = S2.teacher_data2(task)
d = TL.n_params(n, L)
z = lambda th, x: TL.exact_z0(TL.angle_list(th, x, n, L, enc), n, L)
F = lambda th: float(np.mean([y * z(th, x) for x, y in zip(Xtr, ytr)]))
def ev(th, X, y):
    zz = np.array([z(th, x) for x in X]); return float(np.mean(np.sign(zz) == y)), S2._ce(zz, y)
t0 = time.perf_counter()
th = np.zeros(d); F0 = F(th); hp = np.pi / 2
# check the sinusoid on one parameter at a fourth angle
e = np.zeros(d); e[0] = 1.0
Fp, Fm = F(th + hp * e), F(th - hp * e); a = (Fp + Fm) / 2; b = F0 - a; c = (Fp - Fm) / 2
print(f"sinusoid check: F(0.7) {F(th + 0.7 * e):.6f} vs formula {a + b * np.cos(0.7) + c * np.sin(0.7):.6f}", flush=True)
for s in range(sweeps + 1):
    tra = float(np.mean(np.sign([z(th, x) for x in Xtr]) == ytr)); a_, c_ = ev(th, Xte, yte)
    print(f"E3 ta={ta} L{L} sweep{s}: train mean(yf) {F0:.4f} acc {tra:.3f} | test acc {a_:.3f} CE {c_:.4f} |theta|max {np.abs(th).max():.3f} ({time.perf_counter()-t0:.0f} s)", flush=True)
    if s == sweeps:
        break
    for k in range(d):
        e = np.zeros(d); e[k] = 1.0
        Fp, Fm = F(th + hp * e), F(th - hp * e)
        a = (Fp + Fm) / 2; b = F0 - a; c = (Fp - Fm) / 2
        u = float(np.arctan2(c, b))
        th[k] += u
        F0 = a + np.hypot(b, c)
