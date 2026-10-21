"""Small test (noiseless, exact <Z0>): a calibrated readout p = sigmoid(a z + b), (a, b) the exact maximum-likelihood
fit on the 64 training points (convex; Newton to convergence), against the fixed readout p = (1 + z) / 2, on the 500
test points, for the fruit match's recorded parameters."""
import json, glob, sys
import numpy as np
from toqb import task_loop as TL
from toqb import s2r2 as S2

def fit(z, y):
    t = (y > 0).astype(float); X = np.c_[z, np.ones_like(z)]; w = np.zeros(2)
    for _ in range(100):
        p = 1 / (1 + np.exp(-X @ w)); g = X.T @ (p - t); H = (X * (p * (1 - p))[:, None]).T @ X + 1e-12 * np.eye(2)
        step = np.linalg.solve(H, g); w -= step
        if np.abs(step).max() < 1e-10: break
    return w
def ce(p, y):
    p = np.clip(p, 1e-4, 1 - 1e-4); return float(np.mean(-np.where(y > 0, np.log(p), np.log(1 - p))))
d = sys.argv[1]; cache = {}
rows = []
for f in sorted(glob.glob(d + '/*.json')):
    n = f.split('/')[-1]
    if n.startswith('3'): continue
    r = json.load(open(f)); t = r['task']; k = (t['teacher_seed'], t['teacher_angle'])
    if k not in cache: cache[k] = S2.teacher_data2(t)
    Xtr, ytr, Xte, yte = cache[k]
    role = n.split('_')[0][1:]
    pts = [('final', np.array(r['final_mean']) if role != 'Z' else np.zeros(TL.n_params(10, 8)))]
    if r.get('checkpoints'): pts.append(('first', np.array(r['checkpoints'][0]['theta'])))
    for lab, th in pts:
        z = lambda X: np.array([TL.exact_z0(TL.angle_list(th, x, 10, 8, t['enc']), 10, 8) for x in X])
        ztr, zte = z(Xtr), z(Xte)
        a, b = fit(ztr, ytr)
        pc = 1 / (1 + np.exp(-(a * zte + b)))
        rows.append(dict(role=role, point=lab, angle=t['teacher_angle'], raw_ce=ce((1 + zte) / 2, yte), cal_ce=ce(pc, yte),
                         raw_acc=float(np.mean(np.sign(zte) == yte)), cal_acc=float(np.mean((pc > 0.5) == (yte > 0))), a=a, b=b))
        print(json.dumps({k2: (round(v, 4) if isinstance(v, float) else v) for k2, v in rows[-1].items()}), flush=True)
