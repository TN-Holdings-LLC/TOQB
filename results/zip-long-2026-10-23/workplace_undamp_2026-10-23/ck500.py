"""Shot-free paired check at the 500-loop checkpoint, all three teachers (deltas from the u500 log, 3 decimals).
usage: python ck500.py RUNS_DIR"""
import json, math, sys
import numpy as np
R = sys.argv[1].rstrip('/') + '/'
D = {('t11', 'template'): .064, ('t11', 'template_zip'): .016, ('t12', 'template'): .060,
     ('t12', 'template_zip'): .018, ('t13', 'template'): .062, ('t13', 'template_zip'): .016}
def mcn(a, b):
    n10 = int(np.sum(a & ~b)); n01 = int(np.sum(~a & b)); n = n10 + n01; k = min(n10, n01)
    return n10, n01, min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)
def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); m = len(ps); adj = [0] * m; run = 0
    for r, i in enumerate(o):
        run = max(run, min(1, (m - r) * ps[i])); adj[i] = run
    return adj
res = {'raw': [], 'und': []}
for t in ('t11', 't12', 't13'):
    z = {}
    for a in ('template', 'template_zip'):
        r = json.load(open(R + f'L16_{t}_s301-psfai_{a}.json')); y = np.array(r['test_labels'])
        c = [c for c in r['checkpoints'] if c['loop'] == 500][0]
        z[a] = 1 - 2 * np.array(c['rehearsal']['standin_p1'])
    for k in res:
        s = {a: (z[a] if k == 'raw' else z[a] - D[(t, a)]) for a in z}
        cz, cq = np.sign(s['template_zip']) == y, np.sign(s['template']) == y
        res[k].append((t, cz.mean(), cq.mean(), *mcn(cz, cq), float(np.mean(s['template'] > 0)), float(np.mean(s['template_zip'] > 0))))
for k, rows in res.items():
    for row, h in zip(rows, holm([r[5] for r in rows])):
        t, az, aq, n10, n01, p, fq, fz = row
        print(f'{k} {t}: zip {az:.3f} q31 {aq:.3f} gap {az-aq:+.3f} ({n10}/{n01}) p {p:.2g} holm {h:.2g} | +1 calls q31 {fq:.2f} zip {fz:.2f}')
