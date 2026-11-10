"""3: simulated nMSE (FakeFez noise, not tuned) of fold and line at the judged 4 x 3 x 2 place, t 1-4, beside the
device's; nMSE = mean over sites of (z - exact)^2 / mean of exact^2 (as scores.json); d = line - fold with a bootstrap
SE over trajectories."""
import json
import numpy as np
s = json.load(open("out/q32.json"))["circuits"]
ans = json.load(open("inputs/q32_answers.json"))
dev = json.load(open("inputs/q32_scores.json"))["arms"]
rng = np.random.default_rng(1)

def nmse(z, ex):
    return float(np.mean((z - ex) ** 2) / np.mean(ex ** 2))

print(f"{'t':2} {'sim fold':>9} {'sim line':>9} {'sim d':>14} | {'dev fold':>9} {'dev line':>9} {'dev d':>8}  traj")
for t in (1, 2, 3, 4):
    vals = {}
    for lay in ("f", "l"):
        tag = f"q32{lay}0_t{t}"
        Z = np.asarray(s["p2d_" + tag]["z"])[:, :24]
        ex = np.array([ans[tag][str(q)] for q in range(24)])
        vals[lay] = (Z, ex)
    nf, nl = nmse(vals["f"][0].mean(0), vals["f"][1]), nmse(vals["l"][0].mean(0), vals["l"][1])
    bs = []
    for _ in range(2000):
        i = rng.integers(0, len(vals["f"][0]), len(vals["f"][0])); j = rng.integers(0, len(vals["l"][0]), len(vals["l"][0]))
        bs.append(nmse(vals["l"][0][j].mean(0), vals["l"][1]) - nmse(vals["f"][0][i].mean(0), vals["f"][1]))
    df, dl = dev[f"q32f0_t{t}"]["nmse"], dev[f"q32l0_t{t}"]["nmse"]
    print(f"{t:2} {nf:9.4f} {nl:9.4f} {nl - nf:+7.4f}+-{np.std(bs):.4f} | {df:9.4f} {dl:9.4f} {dl - df:+8.4f}  {len(vals['f'][0])}/{len(vals['l'][0])}")
