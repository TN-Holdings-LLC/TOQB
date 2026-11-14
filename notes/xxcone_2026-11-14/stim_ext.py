"""Desk illustration (no device data enters the model): the same stim run as stim_noise.py, with the CZ error tripled
on couplers that touch a qubit of the N = 81 chain beyond position 32 (the extension). Not fitted to anything: it
shows when, by the circuit's own spreading, a qubit of the shared block starts to feel worse elements beyond it.
usage: python notes/xxcone_2026-11-14/stim_ext.py RESULTS_DIR"""
import json
import os
import sys

import numpy as np
import stim
from qiskit import qpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stim_noise as SN  # noqa: E402

P2, P1, PM, BOOST, SHOTS = 0.003, 0.0003, 0.015, 3.0, 20000


def build(c, ext):
    s = stim.Circuit()
    idx = {q: c.find_bit(q).index for q in c.qubits}
    meas = []
    for ins in c.data:
        n, qs = ins.operation.name, [idx[q] for q in ins.qubits]
        if n == "rz":
            k = round(float(ins.operation.params[0]) / SN.HALF) % 4
            if k:
                s.append({1: "S", 2: "Z", 3: "S_DAG"}[k], qs)
        elif n in ("sx", "x"):
            s.append("SQRT_X" if n == "sx" else "X", qs)
            s.append("DEPOLARIZE1", qs, P1)
        elif n == "cz":
            s.append("CZ", qs)
            s.append("DEPOLARIZE2", qs, P2 * (BOOST if set(qs) & ext else 1))
        elif n == "measure":
            meas.append(qs[0])
    s.append("X_ERROR", meas, PM)
    s.append("M", meas)
    return s, meas


def main(res):
    ext = set(json.load(open(os.path.join(res, "ibm_marrakesh_n81", "build.json")))["chains"]["81"]["labels"][33:])
    r = lambda z, e: float(np.dot(z, e) / np.dot(e, e))
    print(f"CZ error {P2}, x{BOOST} on couplers touching the extension (qubits {len(ext)}); theta pi/2")
    for st in (2, 4, 8, 12, 16):
        zz = {}
        for n in (33, 81):
            runs = os.path.join(res, f"ibm_marrakesh_n{n}", "runs")
            tag = f"N{n}_th1571_s{st:02d}"
            (c,) = qpy.load(open(os.path.join(runs, f"p2d_{tag}.qpy"), "rb"))
            labels = json.load(open(os.path.join(runs, f"p2d_{tag}.json")))["labels"]
            s, meas = build(c, ext)
            ideal = 1 - 2 * SN.to_stim(c, 0, 0, 0)[0].compile_sampler().sample(1)[0].astype(float)
            smp = 1 - 2 * s.compile_sampler(seed=1114).sample(SHOTS).astype(float)
            z, e = dict(zip(meas, smp.mean(axis=0))), dict(zip(meas, ideal))
            zz[n] = (np.array([z[q] for q in labels]), np.array([e[q] for q in labels]))
        g = {b: r(zz[33][0][list(i)], zz[33][1][list(i)]) - r(zz[81][0][list(i)], zz[81][1][list(i)]) for b, i in SN.BLOCKS.items()}
        print(f"  {4 * st:2d} layers: gap far {g['far']:+.3f} mid {g['mid']:+.3f} near {g['near']:+.3f}")


if __name__ == "__main__":
    main(sys.argv[1])
