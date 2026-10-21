"""Small test: a label-free 'undamping' of the readout. The twin's noise shrinks and shifts <Z0>: z_noisy ~ lam z + delta.
(lam, delta) are fitted by least squares between the noisy and the noiseless outputs over input points WITHOUT labels;
the answer is p = clip((1 + (z_noisy - delta) / lam) / 2). Diagnostic here: the stand-in's test outputs (records) and
exact noiseless outputs on the same test inputs (labels used only for scoring). On the pod the fit would use the twin
on the training inputs instead (no device, no labels)."""
import json, glob, sys
import numpy as np
from toqb import task_loop as TL
from toqb import s2r2 as S2
def ce(p, y):
    p = np.clip(p, 1e-4, 1 - 1e-4); return float(np.mean(-np.where(y > 0, np.log(p), np.log(1 - p))))
d = sys.argv[1]; cache = {}
for f in sorted(glob.glob(d + '/*.json')):
    n = f.split('/')[-1]
    if n.startswith('3'): continue
    r = json.load(open(f)); t = r['task']; k = (t['teacher_seed'], t['teacher_angle'])
    if k not in cache: cache[k] = S2.teacher_data2(t)
    _, _, Xte, yte = cache[k]
    role = n.split('_')[0][1:]
    pts = [('final', np.array(r['final_mean']) if role != 'Z' else np.zeros(TL.n_params(10, 8)), r['rehearsal']['standin_p1'])]
    if r.get('checkpoints'):
        c = r['checkpoints'][0]; pts.append(('first', np.array(c['theta']), c['rehearsal']['standin_p1']))
    for lab, th, sp1 in pts:
        z0 = np.array([TL.exact_z0(TL.angle_list(th, x, 10, 8, t['enc']), 10, 8) for x in Xte])
        zn = 1 - 2 * np.array(sp1)
        lam, delta = np.polyfit(z0, zn, 1)
        pu = (1 + (zn - delta) / lam) / 2
        print(json.dumps(dict(role=role, point=lab, angle=t['teacher_angle'], lam=round(lam, 4), delta=round(delta, 4),
                              noisy_ce=round(ce((1 + zn) / 2, yte), 4), undamped_ce=round(ce(pu, yte), 4),
                              noiseless_ce=round(ce((1 + z0) / 2, yte), 4), noisy_acc=round(float(np.mean(np.sign(zn) == yte)), 3),
                              undamped_acc=round(float(np.mean((pu > 0.5) == (yte > 0))), 3))), flush=True)
