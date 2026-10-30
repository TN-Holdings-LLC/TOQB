"""Post-hoc: mask the near-random sites found in one kingston run, read the other run on the remaining sites only."""
import gzip, json, sys
import numpy as np
import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
from toqb import kising_charge as KC
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
S = R + '/rerun-rule-only/job'
def load(man, raw):
    m = json.load(open(man)); r = json.load(gzip.open(raw) if raw.endswith('.gz') else open(raw))['rows']
    out = {}
    for k, p in enumerate(m['pubs']):
        c = m['cells'][p['cell']]
        if c['arm'] != 'fold:rule':
            continue
        out.setdefault(c['name'], {})[p['point']] = r[k]['counts']
    return out
A = {}
for t in ('test2', 'test3E'):
    A.update(load(f'{R}/{t}/kingston/job/manifest.json', f'{R}/{t}/kingston/job/raw_counts.json.gz'))
B = load(f'{S}/manifest.json', f'{S}/raw_counts.json.gz')
PTS = [(i, 'echo') for i in KC.INPUTS] + [(i, 'ref') for i in KC.INPUTS]
def zarr(counts, n):
    keys = list(counts); cnt = np.array([counts[k] for k in keys], float)
    z = np.array([[1 - 2 * int(k.replace(' ', '')[n - 1 - j]) for j in range(n)] for k in keys], float)
    return z, cnt
def cell(run, name, n, mask):
    """rho_E over the masked sites (same estimator as kising_echo.estimate), its SE, and the per-bit accuracy."""
    num = vnum = den = vden = 0.0; acc = []
    for p, (i, st) in enumerate(PTS):
        zin = 1 - 2 * np.array(KC.input_bits(i, n)); s = -zin if st == 'echo' else zin
        z, cnt = zarr(run[name][p], n); N = cnt.sum()
        v = (z[:, mask] * s[mask]).sum(1); mu = (v * cnt).sum() / N; var = (cnt * (v - mu) ** 2).sum() / (N - 1) / N
        if st == 'echo':
            num += mu; vnum += var
            acc.append(((z[:, mask] * s[mask] + 1) / 2 * cnt[:, None]).sum(0) / N)
        else:
            den += mu; vden += var
    rho, se = KC.ratio(num, vnum, den, vden)
    return rho, se, float(np.mean(acc))
def site_signal(run, name, n):
    sig = np.zeros(n)
    for p, (i, st) in enumerate(PTS[:4]):
        zin = 1 - 2 * np.array(KC.input_bits(i, n)); z, cnt = zarr(run[name][p], n)
        sig += (-zin * (z * cnt[:, None]).sum(0) / cnt.sum()) / 4
    return sig
res = {}
for n in (20, 36, 40, 72):
    for src, tgt, lab in ((A, B, 'mask from morning, read rerun'), (B, A, 'mask from rerun, read morning')):
        sig = np.mean([site_signal(src, f'kecho_n{n}_D24_hz{hz:g}_h0.6-fold_rule', n) for hz in (0, 0.1, 0.3)], axis=0)
        live = sig >= 0.12
        for hz in (0, 0.1, 0.3):
            rows = []
            for D in (24, 50, 100):
                nm = f'kecho_n{n}_D{D}_hz{hz:g}_h0.6-fold_rule'
                ra, sa, aa = cell(tgt, nm, n, np.ones(n, bool)); rl, sl, al = cell(tgt, nm, n, live)
                rows.append(dict(D=D, rho_all=ra, se_all=sa, acc_all=aa, rho_live=rl, se_live=sl, acc_live=al))
            fa = KC.decay_length([r['D'] for r in rows], [r['rho_all'] for r in rows], [r['se_all'] for r in rows])
            fl = KC.decay_length([r['D'] for r in rows], [r['rho_live'] for r in rows], [r['se_live'] for r in rows])
            res[(n, hz, lab)] = dict(live=int(live.sum()), rows=rows, L_all=fa, L_live=fl)
json.dump({f'{k[0]}|{k[1]}|{k[2]}': v for k, v in res.items()}, open(os.path.join(os.path.dirname(__file__), 'live_sites.json'), 'w'), indent=1, default=str)
for (n, hz, lab), v in res.items():
    d24 = v['rows'][0]
    f = lambda x: 'n/a' if x is None or x[0] is None else f'{x[0]:.1f}±{x[1]:.1f}'
    print(f'n{n:2d} hz{hz:<3} [{lab[:16]}] live {v["live"]:2d}/{n}: D24 acc all {d24["acc_all"]:.3f} live {d24["acc_live"]:.3f}; '
          f'rho all {d24["rho_all"]:.3f} live {d24["rho_live"]:.3f}; L* all {f(v["L_all"])} live {f(v["L_live"])}')
