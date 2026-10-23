"""Shot-free paired check at 500 loops from home's u500 files (full-precision lam, delta; the run files there carry the
500-loop checkpoint as their final point). usage: python ck500x.py U500_RUNS_DIR U500_UNDAMP_DIR"""
import json, math, sys
import numpy as np
R, U = (a.rstrip('/') + '/' for a in sys.argv[1:3])
def ce(z, y):
    q = np.clip((1 + np.clip(z, -1, 1)) / 2, 1e-4, 1 - 1e-4)
    return float(np.mean(np.where(y > 0, -np.log(q), -np.log(1 - q))))
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
    z, dl, y = {}, {}, None
    for a in ('template', 'template_zip'):
        b = f'L16_{t}_s301-psfai_{a}'
        r = json.load(open(R + b + '.json')); u = json.load(open(U + b + '.json'))['points'][0]
        assert u['point'] == 'loop 500'
        yy = np.array(r['test_labels']); assert y is None or np.array_equal(y, yy); y = yy
        z[a] = 1 - 2 * np.array(r['rehearsal']['standin_p1']); dl[a] = u['delta']
        zu = np.clip((z[a] - u['delta']) / u['lam'], -1, 1)
        assert abs(ce(z[a], y) - r['rehearsal']['standin_ce_exact']) < 1e-6
        assert abs(ce(zu, y) - u['undamped']['ce_exact']) < 1e-6
    for k in res:
        s = {a: (z[a] if k == 'raw' else z[a] - dl[a]) for a in z}
        cz, cq = np.sign(s['template_zip']) == y, np.sign(s['template']) == y
        res[k].append((t, cz.mean(), cq.mean(), *mcn(cz, cq), float(np.mean(s['template'] > 0)), float(np.mean(s['template_zip'] > 0))))
print('ce_exact reproduced (raw and undamped) in 6/6')
for k, rows in res.items():
    for row, h in zip(rows, holm([r[5] for r in rows])):
        t, az, aq, n10, n01, p, fq, fz = row
        print(f'{k} {t}: zip {az:.3f} q31 {aq:.3f} gap {az-aq:+.3f} ({n10}/{n01}) p {p:.2g} holm {h:.2g} | +1 calls q31 {fq:.2f} zip {fz:.2f}')
