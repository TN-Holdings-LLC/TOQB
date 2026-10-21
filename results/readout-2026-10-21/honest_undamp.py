"""Honest label-free undamping (small test): (lam, delta) from the TWIN alone on the 64 training inputs (64 trajectories,
seed predict.seed + 5; no labels, no stand-in), against exact noiseless outputs on the same inputs; then applied to the
stand-in's recorded test outputs: p = (1 + (z - delta) / lam) / 2. Noise in the twin's outputs sits in the dependent
variable of the fit, so the slope is unbiased with few trajectories."""
import json, glob, sys, time
import numpy as np
from toqb import task_loop as TL
from toqb import s2r2 as S2
def ce(p, y):
    p = np.clip(p, 1e-4, 1 - 1e-4); return float(np.mean(-np.where(y > 0, np.log(p), np.log(1 - p))))
d, part, nparts, T = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
jobs = []
for f in sorted(glob.glob(d + '/*.json')):
    n = f.split('/')[-1]
    if n.startswith('3'): continue
    r = json.load(open(f)); role = n.split('_')[0][1:]
    d0 = TL.n_params(10, 8)
    pts = [('final', np.array(r['final_mean']) if role != 'Z' else np.zeros(d0), r['rehearsal']['standin_p1'])]
    if r.get('checkpoints'):
        c = r['checkpoints'][0]; pts.append(('first', np.array(c['theta']), c['rehearsal']['standin_p1']))
    for p in pts: jobs.append((n, role, r, p))
for i, (n, role, r, (lab, th, sp1)) in enumerate(jobs):
    if i % nparts != part: continue
    t0 = time.time()
    plan = dict(name='u', device=r['device'], task=r['task'], train=r['train'], predict=r['predict'], standin=r['standin'])
    R = S2.Runner(plan, r['arm']); Xtr, ytr, Xte, yte = S2.teacher_data2(r['task'])
    zt = R.z('sim', [R.compile(th, x) for x in Xtr], T, int(r['predict']['seed']) + 5)
    z0 = np.array([TL.exact_z0(TL.angle_list(th, x, 10, 8, r['task']['enc']), 10, 8) for x in Xtr])
    lam, delta = np.polyfit(z0, zt, 1)
    zn = 1 - 2 * np.array(sp1); y = np.array(r['test_labels'], float)
    pu = (1 + (zn - delta) / lam) / 2
    print(json.dumps(dict(file=n, role=role, point=lab, angle=r['task']['teacher_angle'], lam=round(lam, 4), delta=round(delta, 4),
                          raw_ce=round(ce((1 + zn) / 2, y), 4), undamped_ce=round(ce(pu, y), 4),
                          raw_acc=round(float(np.mean(np.sign(zn) == y)), 3), undamped_acc=round(float(np.mean((pu > 0.5) == (y > 0))), 3),
                          sec=round(time.time() - t0))), flush=True)
