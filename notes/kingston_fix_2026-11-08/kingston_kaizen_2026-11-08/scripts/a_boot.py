"""A: are the kingston line - old (and carry - old) retention differences resolved? Per-shot Neel order
m_s = mean_s (-1)^(x+y+z) z_s from the raw counts (clbit k = site k), retention = m_s / exact (each arm's own exact),
analytic SE from the per-shot spread and a bootstrap over shots (4000 resamples, each arm resampled on its own)."""
import itertools, json, sys
import numpy as np
from psf_os import job as J

R = sys.argv[1]
B = 4000
rng = np.random.default_rng(20261108)
read = J.read(f"{R}/kingston/job", f"{R}/kingston/runs")
scores = json.load(open(f"{R}/kingston/scores.json"))["arms"]
sign = np.array([(-1) ** (x + y + z) for x, y, z in itertools.product(range(4), range(2), range(2))])


def shots(tag):
    rec, cc = read["p2d_" + tag]
    counts = cc[("u", "z")]
    n = len(rec["labels"])
    vals, w = [], []
    for bits, c in counts.items():
        b = bits.replace(" ", "")
        z = np.array([1 - 2 * int(b[len(b) - 1 - k]) for k in range(n)])      # clbit k from the right
        vals.append(float(np.mean(sign * z))); w.append(c)
    return np.repeat(np.array(vals), w)


out = {}
print(f"{'place':5} {'t':2} {'pair':12} {'diff':>7} {'SE(analytic)':>12} {'SE(boot)':>9} {'z':>6} {'boot 95%':>18}  shot bound")
for c in range(4):
    for t in range(1, 5):
        arms = {v: f"h3{h}{c}_t{t}" for v, h in (("old", "d"), ("carry", "c"), ("line", "l"))}
        data = {}
        for v, tag in arms.items():
            m = shots(tag)
            ex = scores[tag]["m_s_exact"]
            assert abs(m.mean() - scores[tag]["m_s"]) < 1e-9, (tag, m.mean(), scores[tag]["m_s"])
            data[v] = (m, ex)
        for v in ("line", "carry"):
            (m1, e1), (m0, e0) = data[v], data["old"]
            d = m1.mean() / e1 - m0.mean() / e0
            se = np.hypot(m1.std(ddof=1) / np.sqrt(len(m1)) / abs(e1), m0.std(ddof=1) / np.sqrt(len(m0)) / abs(e0))
            bs = np.array([rng.choice(m1, len(m1)).mean() / e1 - rng.choice(m0, len(m0)).mean() / e0 for _ in range(B)])
            lo, hi = np.percentile(bs, [2.5, 97.5])
            bound = 2 * np.hypot(1 / np.sqrt(len(m1)) / abs(e1), 1 / np.sqrt(len(m0)) / abs(e0))
            key = f"{v}-old"
            out[f"c{c}_t{t}_{key}"] = dict(diff=d, se=se, se_boot=float(bs.std(ddof=1)), z=d / se, lo=lo, hi=hi, bound=bound)
            print(f"{c:5} {t:2} {key:12} {d:+7.3f} {se:12.4f} {bs.std(ddof=1):9.4f} {d / se:+6.1f} [{lo:+.3f}, {hi:+.3f}]  {bound:.3f}")
json.dump(out, open("a_boot.json", "w"), indent=1)
