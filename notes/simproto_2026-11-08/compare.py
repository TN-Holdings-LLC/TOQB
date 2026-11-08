"""Compare the trajectory estimate (expsim.py) with the fez device, once, nothing fitted (2026-11-08).

Per arm: the observable per trajectory (Heisenberg: Neel order m_s = mean of (-1)^(x+y+z) <Z>; Ising: M = mean <Z>),
its mean over all trajectories and over the first 40, the standard error (std / sqrt(N)), the retention
(sim / exact and device / exact) and their ratio. The exact value is recomputed from the sealed answers and checked
against the device scores' own exact value.

usage: python compare.py SIM.json ANSWERS.json DEVICE_SCORES.json heis|ising
"""
import itertools
import json
import sys

import numpy as np

sim_f, ans_f, dev_f, kind = sys.argv[1:5]
sim = json.load(open(sim_f))
ans = json.load(open(ans_f))
dev = json.load(open(dev_f))["arms"]


def obs(z, n):
    z = np.asarray(z)[:, :n]
    if kind == "heis":
        sign = np.array([(-1) ** (x + y + w) for x, y, w in itertools.product(range(4), range(n // 8), range(2))])
        return (z * sign).mean(axis=1)
    return z.mean(axis=1)


key_dev, key_ex = ("m_s", "m_s_exact") if kind == "heis" else ("M", "M_exact")
print(f"noise {sim['noise']}  trajectories {sim['traj']}  workers {sim['workers']}  wall {sim['wall_seconds']:.0f} s")
print(f"{'arm':14} {'CZ':>4} {'s/traj':>6} | {'exact':>6} {'sim':>13} {'sim(40)':>13} {'device':>6} |"
      f" {'ret sim':>7} {'ret dev':>7} {'sim/dev':>7}")
rows = []
for name, r in sim["circuits"].items():
    tag = name[4:] if name.startswith("p2d_") else name
    n = len(ans[tag])
    ex_vec = np.array([ans[tag][str(s)] for s in range(n)])
    ex = float(obs(ex_vec[None, :], n)[0])
    d = dev[tag]
    assert abs(ex - d[key_ex]) < 1e-9, (tag, ex, d[key_ex])
    o = obs(r["z"], n)
    N = len(o)
    m, se = float(o.mean()), float(o.std(ddof=1) / np.sqrt(N))
    o40 = o[:40]
    m40, se40 = float(o40.mean()), float(o40.std(ddof=1) / np.sqrt(len(o40)))
    rs, rd = m / ex, d[key_dev] / ex
    rows.append(dict(arm=tag, cz=r["cz"], sec_per_traj=r["sec_per_traj"], exact=ex, sim=m, sim_se=se, sim40=m40,
                     sim40_se=se40, device=d[key_dev], ret_sim=rs, ret_dev=rd, ratio=rs / rd, traj=N,
                     traj_std=float(o.std(ddof=1))))
    print(f"{tag:14} {r['cz']:4} {r['sec_per_traj']:6.2f} | {ex:+6.3f} {m:+7.3f}+-{se:.3f} {m40:+7.3f}+-{se40:.3f}"
          f" {d[key_dev]:+6.3f} | {rs:7.3f} {rd:7.3f} {rs / rd:7.3f}")
r_ = np.array([x["ratio"] for x in rows])
print(f"ratio sim/device retention: mean {r_.mean():.3f}  min {r_.min():.3f}  max {r_.max():.3f}  (arms {len(rows)})")
json.dump(dict(noise=sim["noise"], kind=kind, rows=rows), open(sim_f.replace(".json", "_compare.json"), "w"), indent=1)
