"""delta-free (sign of z - delta) shot-free check at theta = 0 against 500 and 16,000 loops.
usage: python theta0_dfree.py THETA0_JSON THETA0_LAM_JSON ZL_RUNS_DIR U500_UNDAMP_DIR UNDAMP_FINAL_DIR"""
import json, math, sys
import numpy as np
T0 = json.load(open(sys.argv[1])); L0 = {(r['t'], r['arm']): r for r in json.load(open(sys.argv[2]))}
R, U5, UF = (a.rstrip('/') + '/' for a in sys.argv[3:6])
def mcn(a, b):
    n10 = int(np.sum(a & ~b)); n01 = int(np.sum(~a & b)); n = n10 + n01; k = min(n10, n01)
    return n10, n01, min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)
def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); m = len(ps); adj = [0] * m; run = 0
    for r, i in enumerate(o):
        run = max(run, min(1, (m - r) * ps[i])); adj[i] = run
    return adj
A = ('psfai:template', 'psfai:template_zip')
rows = []
for t in (11, 12, 13):
    c, f, y = {}, {}, None
    for arm in A:
        b = f"L16_t{t}_s301-{arm.replace(':', '_')}"
        r = json.load(open(R + b + '.json')); yy = np.array(r['test_labels'])
        assert y is None or np.array_equal(y, yy); y = yy
        z = {0: 1 - 2 * np.array(T0[f't{t} {arm}']['standin_p1']),
             500: 1 - 2 * np.array([k for k in r['checkpoints'] if k['loop'] == 500][0]['rehearsal']['standin_p1']),
             16000: 1 - 2 * np.array(r['rehearsal']['standin_p1'])}
        d = {0: L0[(t, arm)]['delta'], 500: json.load(open(U5 + b + '.json'))['points'][0]['delta'],
             16000: json.load(open(UF + b + '.json'))['points'][0]['delta']}
        for pt in z:
            c[(arm, pt)] = np.sign(z[pt] - d[pt]) == y; f[(arm, pt)] = float(np.mean(z[pt] - d[pt] > 0))
    row = dict(t=t)
    for pt in (0, 500, 16000):
        row[pt] = (c[(A[1], pt)].mean(), c[(A[0], pt)].mean(), *mcn(c[(A[1], pt)], c[(A[0], pt)]), f[(A[0], pt)], f[(A[1], pt)])
    for arm in A:
        row[arm] = (c[(arm, 0)].mean(), c[(arm, 500)].mean(), *mcn(c[(arm, 500)], c[(arm, 0)]))
    rows.append(row)
print('delta-free, shot-free')
for pt in (0, 500, 16000):
    for r, h in zip(rows, holm([r[pt][4] for r in rows])):
        az, aq, n10, n01, p, fq, fz = r[pt]
        print(f"loop {pt:>5} t{r['t']}: zip {az:.3f} q31 {aq:.3f} gap {az-aq:+.3f} ({n10}/{n01}) holm {h:.2g} | +1 calls q31 {fq:.2f} zip {fz:.2f}")
for arm in A:
    for r, h in zip(rows, holm([r[arm][4] for r in rows])):
        a0, a5, n10, n01, p = r[arm]
        print(f"learning 0->500 {arm} t{r['t']}: {a0:.3f} -> {a5:.3f} ({a5-a0:+.3f}; {n10}/{n01}) holm {h:.2g}")
for r in rows:
    g0 = r[0][0] - r[0][1]; g5 = r[500][0] - r[500][1]
    print(f"t{r['t']}: gap 0 {g0:+.3f} -> 500 {g5:+.3f} (widening {g5-g0:+.3f})")
