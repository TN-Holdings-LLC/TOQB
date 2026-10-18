"""How well does the simulator's model know the stand-in's gradient?

    python -m toqb.gradcos SPEC L K b T [seed]        (from the TOQB root; TOQB_XP=cupy for the GPU)

For K random +-1 directions D at a random student mean m (uniform in [-1, 1], from `seed`), the training-loss
difference L(m + hD) - L(m - hD) (h = 0.1) on b training points, in the simulator's model and on the stand-in
(trajectory means, T each, in two independent halves). The correlation of the two over the K directions estimates the
cosine of the two gradients; each side is corrected for its own trajectory noise by its split-half reliability
(Spearman-Brown) and the raw correlation divided by the square root of their product. sd_* are the spreads of the
differences (the gradients' sizes along random directions)."""
import json
import sys

import numpy as np

from toqb import s2r2 as S2
from toqb import task_loop as TL

spec, L, K, b, T, h = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), 0.1
seed = int(sys.argv[6]) if len(sys.argv) > 6 else 5
plan = {"name": "gradcos", "device": "fake:FakeFez",
        "task": {"n": 10, "layers": L, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_angle": 0.3,
                 "teacher_gap": 0.2, "n_train": 64, "n_test": 100},
        "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017}}
R = S2.Runner(plan, spec)
Xtr, ytr, _, _ = S2.teacher_data2(plan["task"])
d = TL.n_params(10, L)
rng = np.random.default_rng(seed)
m = rng.uniform(-1, 1, d)
idx = rng.choice(len(Xtr), b, replace=False)
D = rng.choice([-1.0, 1.0], (K, d))
cs = [R.compile(m + s * h * D[k], Xtr[i]) for k in range(K) for s in (1, -1) for i in idx]
out = {}
for model in ("sim", "dev"):
    halves = []
    for half in range(2):
        z = R.z(model, cs, T, 100 + half).reshape(K, 2, b)
        lo = ((1 - z * ytr[idx][None, None, :]) / 2).mean(2)
        halves.append(lo[:, 0] - lo[:, 1])
    out[model] = halves
def corr(a, c):
    return float(np.corrcoef(a, c)[0, 1])
rel = {mo: corr(*out[mo]) for mo in out}
sd = (out["sim"][0] + out["sim"][1]) / 2
dd = (out["dev"][0] + out["dev"][1]) / 2
raw = corr(sd, dd)
# split-half reliabilities of the averages (Spearman-Brown) and the disattenuated correlation
rb = {mo: 2 * r / (1 + r) for mo, r in rel.items()}
print(json.dumps(dict(spec=spec, L=L, seed=seed, K=K, b=b, T=T, raw_corr=raw, reliab=rb,
                      cos_est=raw / np.sqrt(max(rb["sim"], 1e-9) * max(rb["dev"], 1e-9)),
                      sd_sim=float(np.std(sd)), sd_dev=float(np.std(dd)))), flush=True)
