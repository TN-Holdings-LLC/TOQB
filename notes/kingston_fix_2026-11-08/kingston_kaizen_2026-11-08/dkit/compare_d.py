"""D: simulated (fez calibration on the same labels; not kingston's) m_s, retention, site MSE and mirror mean for old
and line at kingston places 1, 2, t 3, 4, beside the device's values."""
import itertools, json
import numpy as np
s = json.load(open("out/kng.json"))["circuits"]
dev = json.load(open("inputs/kng_scores.json"))["arms"]
ans = json.load(open("inputs/kng_answers.json"))
sign = np.array([(-1) ** (x + y + z) for x, y, z in itertools.product(range(4), range(2), range(2))])
print(f"{'arm':10} {'sim m_s':>8} {'sim ret':>8} {'sim mse':>8} {'sim mir':>8} | {'dev ret':>8} {'dev mse':>8} {'dev mir':>8}")
for c in (1, 2):
    for t in (3, 4):
        for h in ("d", "l"):
            tag = f"h3{h}{c}_t{t}"
            z = np.asarray(s["p2d_" + tag]["z"])[:, :16].mean(axis=0)
            zm = np.asarray(s["p2d_" + tag + "_mirror"]["z"]).mean()
            ex = np.array([ans[tag][str(q)] for q in range(16)])
            ms, mse_ex = float(np.mean(sign * z)), float(np.mean(sign * ex))
            mse = float(np.mean((z - ex) ** 2))
            d = dev[tag]
            print(f"{tag:10} {ms:8.3f} {ms / mse_ex:8.3f} {mse:8.4f} {zm:8.3f} | {d['retention']:8.3f} {d['mse']:8.4f} {d['mirror_mean']:8.3f}")
