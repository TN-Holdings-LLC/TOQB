"""S2, owner-decision box (post hoc, nothing judged): the 11-04 correction with rule R's dropped qubits AND their patch
neighbours left out (returned as 'not readable'), on the corr runs of fez and marrakesh. Own recomputation (the raw MSE
base here is over all qubits with an answer; the official scorer's ratios differ in the third digit).
usage: PYTHONPATH=<psf-os>:. python notes/s1_2026-11-05/s2_dropnb.py DATA.json OUT.json"""
import json, sys
import numpy as np
sys.path.insert(0, 'gpu'); sys.path.insert(0, 'notes/s1_2026-11-05')
import corr_score as C  # noqa: E402
from s1_analyse import LAYERS  # noqa: E402

D = json.load(open(sys.argv[1])); Q = D['qubits']; ix = {q: i for i, q in enumerate(Q)}
adj = {q: set() for q in Q}
for L in LAYERS:
    for a, b in L:
        adj[a].add(b); adj[b].add(a)
out = {}
for run in ('corr_fez', 'corr_marrakesh'):
    R = D['runs'][run]; fl = {int(t): np.array(v) for t, v in R['z']['0'].items()}
    keep, _ = C.rule_r(fl); F = C.floor_fn(fl)
    drop = [Q[i] for i in np.where(~keep)[0]]
    nb = {n for d in drop for n in adj[d]} - set(drop)
    keep2 = keep.copy()
    for n in nb:
        keep2[ix[n]] = False
    for tx in ('0.53', '0.3', '0.8'):
        mir = {int(t): v for t, v in R['mirror'][tx].items()}
        res = {}
        for nm, k in (('as declared', keep), ('drop nb', keep2)):
            aa, _ = C.gate_rate(mir, F, k)
            ds, mc, mr = [], [], []
            for t in range(1, 10):
                z = np.array(R['z'][tx][str(t)])
                A = np.array([np.nan if x is None else x for x in D['answers'][tx][str(t)]], float)
                zc = z / (F(t) * np.exp(aa * t)); ok = k & ~np.isnan(A); okr = ~np.isnan(A)
                ds.append(zc[ok].mean() - A[ok].mean()); mc.append(np.mean((zc[ok] - A[ok]) ** 2)); mr.append(np.mean((z[okr] - A[okr]) ** 2))
            r = np.mean(mc) / np.mean(mr)
            res[nm] = dict(n=int(k.sum()), ratio=round(float(r), 3), worst=round(float(ds[int(np.argmax(np.abs(ds)))]), 3),
                           agrees=bool(max(abs(x) for x in ds) <= 0.05))
        out[f'{run} {tx}'] = dict(dropped=drop, neighbours=sorted(nb), **res)
        print(run, tx, out[f'{run} {tx}'])
json.dump(out, open(sys.argv[2], 'w'), indent=1)
