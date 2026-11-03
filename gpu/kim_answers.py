"""Exact <Z_q> of P5's lattice circuit (psf_os/kim.py) from each qubit's causal cone, on one GPU, for cones of up to
33 qubits (stage C, t = 6-8). The gates are psf_os.kim.ops on the cone (the same list the device circuit and the CPU
answers use), applied by gpu/du_answers.py's state-vector classes; <Z_q> = <X_q> after a Hadamard on q.

usage (pod): python gpu/kim_answers.py LATTICE.json OUT.json [--backend cupy|numpy] [--precision single|double]
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

from psf_os import kim as K  # noqa: E402

H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)


def _u(name, angle):
    c, s = np.cos(angle / 2), np.sin(angle / 2)
    if name == "rz":
        return np.diag([c - 1j * s, c + 1j * s])
    if name == "rx":
        return np.array([[c, -1j * s], [-1j * s, c]])
    raise ValueError(name)


def z_cone(qubits, edges, q, theta, t, backend="numpy", precision="double", max_qubits=33):
    cq, ce = K.cone(qubits, edges, q, t)
    if len(cq) > max_qubits:
        return None, len(cq)
    idx = {p: k for k, p in enumerate(cq)}
    dtype = np.complex64 if precision == "single" else np.complex128
    sv = (DA.CupySV if backend == "cupy" else DA.NumpySV)(len(cq), dtype)
    for op in K.ops(cq, ce, theta, t):
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


def run(lat, thetas, ts, backend, precision, max_qubits=33, only=None, log=None):
    """{theta: {t: {"z": [value or None per lattice qubit], "cone": [...], "seconds": ...}}}."""
    qubits, edges = lat["qubits"], [tuple(e) for e in lat["edges"]]
    out = {}
    for th in thetas:
        out[f"{th:.6f}"] = {}
        for t in ts:
            t0, zs, cs = time.time(), [], []
            for q in qubits:
                if only is not None and q not in only:
                    zs.append(None)
                    cs.append(None)
                    continue
                z, m = z_cone(qubits, edges, q, th, t, backend, precision, max_qubits)
                zs.append(z)
                cs.append(m)
            out[f"{th:.6f}"][str(t)] = dict(z=zs, cone=cs, seconds=round(time.time() - t0, 1))
            if log:
                done = [z for z in zs if z is not None]
                log(f"theta {th} t {t}: {len(done)} qubits answered, M over them {np.mean(done):+.6f}, "
                    f"{time.time() - t0:.0f} s")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("lattice")
    ap.add_argument("out")
    ap.add_argument("--backend", default="cupy")
    ap.add_argument("--precision", default="single")
    a = ap.parse_args()
    lat = json.load(open(a.lattice))
    res = run(lat, lat["thetas"], lat["ts"], a.backend, a.precision, lat["max_qubits"], log=lambda s: print(s, flush=True))
    json.dump(res, open(a.out, "w"))
