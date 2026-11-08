"""Compare the simulator's trajectory estimate (realsim.py --expect) of a built job with the device's scores and the
exact answers, per arm: Neel order m_s (3D Heisenberg) or mean <Z> M (kicked Ising), and retention. Not a verdict;
nothing is fitted (2026-11-08, owner "進めて": one comparison of the simulator against the device, recorded as is).

usage: python expect_compare.py SIM_RUN_DIR ANSWERS.json DEVICE_SCORES.json [heis|ising]
"""
import itertools
import json
import sys

import numpy as np

run, ans_file, dev_file = sys.argv[1:4]
kind = sys.argv[4] if len(sys.argv) > 4 else "heis"
ex = json.load(open(ans_file))
e = json.load(open(run + "/expect.json"))
dev = json.load(open(dev_file))["arms"]
print(f"trajectories {e['trajectories']}  noise {e['noise']}")
print(f"{'arm':12} {'exact':>7} {'sim':>7} {'device':>7} | retention sim / device")
for name, z in sorted(e["z"].items()):
    tag = name[4:] if name.startswith("p2d_") else name
    if tag not in ex or tag not in dev:
        continue
    n = len(ex[tag])
    if kind == "heis":
        sign = [(-1) ** (x + y + zz) for x, y, zz in itertools.product(range(4), range(n // 8), range(2))]
        f = lambda v: float(np.mean([sign[s] * v[str(s)] for s in range(n)]))
        d = dev[tag]["m_s"]
    else:
        f = lambda v: float(np.mean([v[str(s)] for s in range(n)]))
        d = dev[tag]["M"]
    m_ex, m_sim = f(ex[tag]), f(z)
    print(f"{tag:12} {m_ex:+7.3f} {m_sim:+7.3f} {d:+7.3f} | {m_sim / m_ex:.3f} / {d / m_ex:.3f}")
