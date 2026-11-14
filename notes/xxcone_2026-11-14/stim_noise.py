"""Desk check (no device): does plain local noise reproduce the light-cone gap? The recorded compiled circuits at
theta = pi/2 (Clifford: every rz a multiple of pi/2) run in stim with a uniform local noise model, no device data:
DEPOLARIZE2(p2) after each CZ, DEPOLARIZE1(p1) after each sx and x, X_ERROR(pm) before each measurement.
r = sum z e / sum e^2 by block (far 0-10, mid 11-21, near 22-32 of the N = 33 chain) and the gap r(33) - r(81).

usage: python notes/xxcone_2026-11-14/stim_noise.py RESULTS_DIR [p2 p1 pm shots]
  RESULTS_DIR holds ibm_marrakesh_n33/runs and ibm_marrakesh_n81/runs (e.g. results/xxcone-2026-11-14)
"""
import json
import math
import os
import sys

import numpy as np
import stim
from qiskit import qpy

HALF = math.pi / 2
BLOCKS = {"far": range(0, 11), "mid": range(11, 22), "near": range(22, 33)}


def to_stim(c, p2, p1, pm):
    s = stim.Circuit()
    idx = {q: c.find_bit(q).index for q in c.qubits}
    meas = []
    for ins in c.data:
        n, qs = ins.operation.name, [idx[q] for q in ins.qubits]
        if n == "rz":
            k = round(float(ins.operation.params[0]) / HALF) % 4
            assert abs(float(ins.operation.params[0]) / HALF - round(float(ins.operation.params[0]) / HALF)) < 1e-9
            if k:
                s.append({1: "S", 2: "Z", 3: "S_DAG"}[k], qs)
        elif n == "sx":
            s.append("SQRT_X", qs)
            if p1: s.append("DEPOLARIZE1", qs, p1)
        elif n == "x":
            s.append("X", qs)
            if p1: s.append("DEPOLARIZE1", qs, p1)
        elif n == "cz":
            s.append("CZ", qs)
            if p2: s.append("DEPOLARIZE2", qs, p2)
        elif n == "measure":
            meas.append(qs[0])
        elif n in ("barrier", "delay"):
            continue
        else:
            raise SystemExit(f"gate {n}")
    if pm: s.append("X_ERROR", meas, pm)
    s.append("M", meas)
    return s, meas


def z_by_label(runs, tag, p2, p1, pm, shots):
    (c,) = qpy.load(open(os.path.join(runs, f"p2d_{tag}.qpy"), "rb"))
    labels = json.load(open(os.path.join(runs, f"p2d_{tag}.json")))["labels"]
    s, meas = to_stim(c, p2, p1, pm)
    ideal = 1 - 2 * to_stim(c, 0, 0, 0)[0].compile_sampler().sample(1)[0].astype(float)
    smp = 1 - 2 * s.compile_sampler(seed=1114).sample(shots).astype(float)
    z = dict(zip(meas, smp.mean(axis=0)))
    e = dict(zip(meas, ideal))
    return np.array([z[q] for q in labels]), np.array([e[q] for q in labels])


def main(res, p2=0.003, p1=0.0003, pm=0.015, shots=20000):
    r = lambda z, e: float(np.dot(z, e) / np.dot(e, e))
    out = {}
    print(f"local noise: p2 {p2}, p1 {p1}, readout {pm}; {shots} shots; theta pi/2")
    for s in (2, 4, 8, 12, 16):
        z33, e33 = z_by_label(os.path.join(res, "ibm_marrakesh_n33", "runs"), f"N33_th1571_s{s:02d}", p2, p1, pm, shots)
        z81, e81 = z_by_label(os.path.join(res, "ibm_marrakesh_n81", "runs"), f"N81_th1571_s{s:02d}", p2, p1, pm, shots)
        row = {b: r(z33[list(i)], e33[list(i)]) - r(z81[list(i)], e81[list(i)]) for b, i in BLOCKS.items()}
        out[s] = dict(gap=row, r33=r(z33, e33), r81=r(z81, e81))
        print(f"  {4 * s:2d} layers: r33 {out[s]['r33']:.3f} r81 {out[s]['r81']:.3f} | gap far {row['far']:+.3f} "
              f"mid {row['mid']:+.3f} near {row['near']:+.3f}")
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], *(float(x) for x in a[1:4]), *(int(x) for x in a[4:5]))
