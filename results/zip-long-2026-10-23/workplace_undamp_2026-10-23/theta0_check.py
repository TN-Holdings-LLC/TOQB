"""Shot-free check at theta = 0 (home's theta0.json) against the 500-loop and 16,000-loop points, raw readout.
usage: python theta0_check.py THETA0_JSON ZL_RUNS_DIR"""
import json, math, sys
import numpy as np
T0 = json.load(open(sys.argv[1])); R = sys.argv[2].rstrip('/') + '/'
def mcn(a, b):
    n10 = int(np.sum(a & ~b)); n01 = int(np.sum(~a & b)); n = n10 + n01; k = min(n10, n01)
    return n10, n01, min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)
def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); m = len(ps); adj = [0] * m; run = 0
    for r, i in enumerate(o):
        run = max(run, min(1, (m - r) * ps[i])); adj[i] = run
    return adj
rows = []
for t in ('t11', 't12', 't13'):
    z, y = {}, None
    for arm in ('psfai:template', 'psfai:template_zip'):
        r = json.load(open(R + f"L16_{t}_s301-{arm.replace(':', '_')}.json"))
        yy = np.array(r['test_labels']); assert y is None or np.array_equal(y, yy); y = yy
        z[(arm, 0)] = 1 - 2 * np.array(T0[f'{t} {arm}']['standin_p1'])
        z[(arm, 500)] = 1 - 2 * np.array([c for c in r['checkpoints'] if c['loop'] == 500][0]['rehearsal']['standin_p1'])
        z[(arm, 16000)] = 1 - 2 * np.array(r['rehearsal']['standin_p1'])
        z[(arm, 'twin0')] = 1 - 2 * np.array(T0[f'{t} {arm}']['twin_p1'])
    c = {k: np.sign(v) == y for k, v in z.items()}
    row = dict(t=t)
    for pt in (0, 500, 16000):
        row[pt] = (c[('psfai:template_zip', pt)].mean(), c[('psfai:template', pt)].mean(),
                   *mcn(c[('psfai:template_zip', pt)], c[('psfai:template', pt)]),
                   float(np.mean(z[('psfai:template', pt)] > 0)), float(np.mean(z[('psfai:template_zip', pt)] > 0)))
    for arm in ('psfai:template', 'psfai:template_zip'):
        row['learn ' + arm] = (c[(arm, 0)].mean(), c[(arm, 500)].mean(), *mcn(c[(arm, 500)], c[(arm, 0)]))
        row['twin0 ' + arm] = c[(arm, 'twin0')].mean()
        row['zabs0 ' + arm] = float(np.mean(np.abs(z[(arm, 0)])))
    rows.append(row)
for pt in (0, 500, 16000):
    hs = holm([r[pt][4] for r in rows])
    for r, h in zip(rows, hs):
        az, aq, n10, n01, p, fq, fz = r[pt]
        print(f"loop {pt:>5} {r['t']}: zip {az:.3f} q31 {aq:.3f} gap {az-aq:+.3f} ({n10}/{n01}) holm {h:.2g} | +1 calls q31 {fq:.2f} zip {fz:.2f}")
for arm in ('psfai:template', 'psfai:template_zip'):
    hs = holm([r['learn ' + arm][4] for r in rows])
    for r, h in zip(rows, hs):
        a0, a5, n10, n01, p = r['learn ' + arm]
        print(f"learning 0->500 {arm} {r['t']}: {a0:.3f} -> {a5:.3f} ({a5-a0:+.3f}; {n10}/{n01}) holm {h:.2g} | twin acc at 0 {r['twin0 '+arm]:.3f} | mean |z| stand-in at 0 {r['zabs0 '+arm]:.3f}")
