"""The three declared predictions of prereg/xxsize_2026-11-14.md, and the beside quantities, from the recorded scores.
usage: python notes/xxsize_2026-11-14/verdicts.py   (from the repository root)"""
import json
import math

import numpy as np

DEV = ("ibm_marrakesh", "ibm_fez")
STEPS = (2, 4, 8, 12, 16)
C = {}
for d in DEV:
    for n in (33, 81):
        s = json.load(open(f"results/xxsize-2026-11-14-{d[4:]}/{d}_n{n}/scores.json"))["circuits"]
        for t, v in s.items():
            C[(d, n, "pi4" if "_th0785_" in t else "pi2", int(t.split("_s")[1]))] = v
r = lambda d, n, th, s: C[(d, n, th, s)]["amplitude_ratio"]
print("device N steps layers | pi/4 MSE/msq verdict r | pi/2 MSE/msq verdict r")
for d in DEV:
    for n in (33, 81):
        for s in STEPS:
            a, b = C[(d, n, "pi4", s)], C[(d, n, "pi2", s)]
            print(f"{d[4:]:10s} {n} {s:2d} {4 * s:2d} | {a['mse'] / a['mean_square']:.3f} {a['reads']:13s} {a['amplitude_ratio']:.3f}"
                  f" | {b['mse'] / b['mean_square']:.3f} {b['reads']:13s} {b['amplitude_ratio']:.3f}")
p1 = [(d, n, s, r(d, n, "pi4", s) - r(d, n, "pi2", s)) for d in DEV for n in (33, 81) for s in STEPS]
p2 = [(d, th, s, r(d, 81, th, s) - r(d, 33, th, s)) for d in DEV for th in ("pi4", "pi2") for s in STEPS]
p3 = [(d, n, s, r(d, n, "pi4", s) >= 1 - 1 / math.sqrt(2), C[(d, n, "pi4", s)]["reads"] == "READS")
      for d in DEV for n in (33, 81) for s in STEPS]
o1 = [x for x in p1 if abs(x[3]) > 0.05]
o2 = [x for x in p2 if abs(x[3]) > 0.05]
k3 = sum(x[3] == x[4] for x in p3)
print(f"1 angle: {'held' if not o1 else 'FAILED'} ({20 - len(o1)} of 20 within 0.05; largest {max(abs(x[3]) for x in p1):.3f})")
print(f"2 size: {'held' if not o2 else 'FAILED'} ({20 - len(o2)} of 20 within 0.05; largest {max(abs(x[3]) for x in p2):.3f})")
print(f"3 line: {'held' if k3 >= 18 else 'FAILED'} ({k3} of 20)")
for d in DEV:
    L, y = zip(*[(4 * s, math.log(r(d, n, th, s))) for n in (33, 81) for th in ("pi4", "pi2") for s in STEPS])
    sl, ic = np.polyfit(L, y, 1)
    print(f"beside: {d} lambda {-1 / sl:.0f} CZ layers, A {math.exp(ic):.3f}")
