"""Quick test: the twin-only, label-free undamping applied to both compiler arms (PSF and Qiskit) of the design C
rehearsal of 2026-10-20 (same task, each arm trained on its own twin). (lam, delta) from the arm's twin on the 64
training inputs (T trajectories, seed predict.seed + 5) against exact noiseless outputs; applied to the stand-in's
recorded test outputs."""
import json, sys, time
import numpy as np
from toqb import task_loop as TL
from toqb import s2r2 as S2
def ce(p, y):
    p = np.clip(p, 1e-4, 1 - 1e-4); return float(np.mean(-np.where(y > 0, np.log(p), np.log(1 - p))))
T = int(sys.argv[1])
for f in sys.argv[2:]:
    t0 = time.time(); r = json.load(open(f)); t = r['task']; th = np.array(r['final_mean'])
    plan = dict(name='u', device=r['device'], task=t, train=r['train'], predict=r['predict'], standin=r['standin'])
    R = S2.Runner(plan, r['arm']); Xtr, ytr, Xte, yte = S2.teacher_data2(t)
    zt = R.z('sim', [R.compile(th, x) for x in Xtr], T, int(r['predict']['seed']) + 5)
    z0 = np.array([TL.exact_z0(TL.angle_list(th, x, t['n'], t['layers'], t['enc']), t['n'], t['layers']) for x in Xtr])
    lam, delta = np.polyfit(z0, zt, 1)
    zn = 1 - 2 * np.array(r['rehearsal']['standin_p1']); y = np.array(r['test_labels'], float)
    pu = (1 + (zn - delta) / lam) / 2
    print(json.dumps(dict(file=f.split('/')[-1], arm=r['arm'], L=t['layers'], seed=r['seed'], lam=round(lam, 4), delta=round(delta, 4),
                          raw_ce=round(ce((1 + zn) / 2, y), 4), undamped_ce=round(ce(pu, y), 4),
                          raw_acc=round(float(np.mean(np.sign(zn) == y)), 3), undamped_acc=round(float(np.mean((pu > 0.5) == (y > 0))), 3),
                          sec=round(time.time() - t0))), flush=True)
