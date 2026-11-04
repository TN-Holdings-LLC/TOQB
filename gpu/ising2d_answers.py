"""Exact <Z_q> of P6 (psf_os/ising2d.py, the Qedma tutorial's patch) from each qubit's causal cone, on one GPU for cones
of up to 33 qubits. The gates are psf_os.ising2d.ops on the cone (the same list the device circuit uses), applied by
gpu/du_answers.py's state-vector classes; <Z_q> = <X_q> after a Hadamard on q.

usage (pod): python gpu/ising2d_answers.py OUT.json --ts 6,7,8,9 [--backend cupy|numpy] [--precision single|double]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import du_answers as DA  # noqa: E402

from psf_os import ising2d as I  # noqa: E402

H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)


def _u(name, angle):
    if name == "h":
        return H
    c, s = np.cos(angle / 2), np.sin(angle / 2)
    if name == "rz":
        return np.diag([c - 1j * s, c + 1j * s])
    if name == "rx":
        return np.array([[c, -1j * s], [-1j * s, c]])
    raise ValueError(name)


def z_cone(q, t, backend="numpy", precision="double", max_qubits=33, tx=I.THETA_X):
    cq, cl = I.cone(q, t)
    if len(cq) > max_qubits:
        return None, len(cq)
    idx = {p: k for k, p in enumerate(cq)}
    sv = (DA.CupySV if backend == "cupy" else DA.NumpySV)(len(cq), np.complex64 if precision == "single" else np.complex128)
    for op in I.ops(cq, cl, t, tx=tx):
        if op[0] == "cz":
            sv.cz(idx[op[1]], idx[op[2]])
        else:
            sv.one(idx[op[2]], _u(op[0], op[1]))
    sv.one(idx[q], H)
    z = sv.x(idx[q])
    del sv
    if backend == "cupy":
        import cupy as cp
        cp.get_default_memory_pool().free_all_blocks()
    return z, len(cq)


def run(ts, backend, precision, max_qubits=33, only=None, log=None, tx=I.THETA_X):
    out = {}
    for t in ts:
        t0, zs, cs = time.time(), [], []
        for q in I.QUBITS:
            if only is not None and q not in only:
                zs.append(None)
                cs.append(None)
                continue
            z, m = z_cone(q, t, backend, precision, max_qubits, tx)
            zs.append(z)
            cs.append(m)
        out[str(t)] = dict(z=zs, cone=cs, seconds=round(time.time() - t0, 1))
        if log:
            done = [z for z in zs if z is not None]
            log(f"t {t}: {len(done)} of {len(zs)} qubits, M over them {np.mean(done):+.6f}, {time.time() - t0:.0f} s")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--ts", default="6,7,8,9")
    ap.add_argument("--backend", default="cupy")
    ap.add_argument("--precision", default="single")
    a = ap.parse_args()
    res = run([int(x) for x in a.ts.split(",")], a.backend, a.precision, log=lambda s: print(s, flush=True))
    json.dump(res, open(a.out, "w"))
