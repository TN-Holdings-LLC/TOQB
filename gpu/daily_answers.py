"""Exact answers of the daily pool (daily/pool.py) by statevector, on one GPU with 80 GB or more. No approximation (no
SPD, no MPS) and no randomness.

The gates are read from the user's circuit itself (pool.circuit: its Qiskit instruction list; no second copy of the
circuit). The readout is read from the circuit too: every measured qubit in Z, or in X when the circuit ends with H on
every measured qubit (F3), in which case those H are taken off and <X> is read from the state.

  full: P32 and C33. The whole patch's state (2^32 or 2^33 amplitudes) evolved once to the largest t of a group of
        problems with the same family and parameters; the circuit of each smaller t must be a prefix of the largest
        one's (checked), and the values are read at every t asked for.
  cone: B42 and B72. For each qubit q, the backward light cone of its observable: the instructions in reverse order,
        keeping a gate when its support overlaps the cone's and it does not commute with the observable (a diagonal
        gate commutes on the qubits whose part of the observable is still diagonal), then dropping the diagonal gates
        that act only on qubits still in |0>; repeated to a fixed point. A cone of more than 33 qubits is not computed:
        the problem fails (no other t is used to fill it).

Backends: gpu/du_answers.py's NumpySV / CupySV with a diagonal two-qubit phase for RZZ and a Z reduction added.
Qubit k of a cone or patch is index bit k (labels ascending; C33: chain order).

usage (pod): python gpu/daily_answers.py OUT.json [--ids D01,D02,...] [--backend cupy|numpy] [--precision single|double]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import du_answers as DA  # noqa: E402

from daily import pool as P  # noqa: E402

DIAGONAL = ("rz", "rzz", "cz", "z", "s", "sdg", "t", "tdg", "p")  # by name: RX(0) is still treated as non-diagonal
FULL, CONE = ("P32", "C33"), ("B42", "B72")
MAX_QUBITS = 33


def program(qc):
    """(ops, readout, basis): ops = [(name, labels, param)] in time order without measurements; readout = the measured
    labels in clbit order; basis "Z", or "X" when the circuit ends with H on every measured qubit (those H removed)."""
    from qiskit.quantum_info import Operator
    ops, meas = [], {}
    for ins in qc.data:
        name = ins.operation.name
        qs = tuple(qc.find_bit(q).index for q in ins.qubits)
        if name == "barrier":
            continue
        if name == "measure":
            meas[qc.find_bit(ins.clbits[0]).index] = qs[0]
            continue
        if set(qs) & set(meas.values()):
            raise ValueError(f"{name} on {qs} after a measurement")
        if name == "rzz":
            ops.append(("rzz", qs, float(ins.operation.params[0])))
        elif name == "cz":
            ops.append(("cz", qs, None))
        elif name == "cx":
            ops += [("h", (qs[1],), _H), ("cz", qs, None), ("h", (qs[1],), _H)]
        elif len(qs) == 1:
            ops.append((name, qs, np.asarray(Operator(ins.operation).data, dtype=complex)))
        else:
            raise ValueError(f"unexpected {name} on {qs}")
    readout = [meas[k] for k in sorted(meas)]
    n = len(readout)
    tail = ops[len(ops) - n:] if n else []
    if n and all(o[0] == "h" for o in tail) and sorted(o[1][0] for o in tail) == sorted(readout):
        return ops[:len(ops) - n], readout, "X"
    return ops, readout, "Z"


_H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)

_CUDA_EXTRA = r"""
#include <cupy/complex.cuh>
typedef complex<REAL> C;
extern "C" __global__ void rzz(C* psi, long long size, int a, int b, C same, C diff) {
  for (long long i = blockIdx.x * (long long)blockDim.x + threadIdx.x; i < size; i += (long long)blockDim.x * gridDim.x) {
    psi[i] = psi[i] * ((((i >> a) ^ (i >> b)) & 1) ? diff : same);
  }
}
extern "C" __global__ void zred(const C* psi, long long size, int k, double* out) {
  __shared__ double s[256];
  double acc = 0.0;
  for (long long i = blockIdx.x * (long long)blockDim.x + threadIdx.x; i < size; i += (long long)blockDim.x * gridDim.x) {
    C a = psi[i];
    double p = (double)a.real() * (double)a.real() + (double)a.imag() * (double)a.imag();
    acc += ((i >> k) & 1) ? -p : p;
  }
  s[threadIdx.x] = acc;
  __syncthreads();
  for (int w = blockDim.x / 2; w > 0; w >>= 1) {
    if (threadIdx.x < w) s[threadIdx.x] += s[threadIdx.x + w];
    __syncthreads();
  }
  if (threadIdx.x == 0) out[blockIdx.x] = s[0];
}
"""


class NumpyDaily(DA.NumpySV):
    def rzz(self, a, b, theta):
        idx = np.arange(2 ** self.N)
        par = ((idx >> a) ^ (idx >> b)) & 1
        self.psi *= np.where(par == 1, np.exp(0.5j * theta), np.exp(-0.5j * theta)).astype(self.psi.dtype)

    def z(self, n):
        v = self._v(n)
        return float(np.vdot(v[:, 0, :], v[:, 0, :]).real - np.vdot(v[:, 1, :], v[:, 1, :]).real)


class CupyDaily(DA.CupySV):
    def __init__(self, N, dtype):
        super().__init__(N, dtype)
        cp = self.cp
        real = "float" if dtype == np.complex64 else "double"
        mod = cp.RawModule(code=_CUDA_EXTRA.replace("REAL", real), options=("-std=c++17",))
        self.k_rzz, self.k_z = mod.get_function("rzz"), mod.get_function("zred")

    def rzz(self, a, b, theta):
        same, diff = self.dtype(np.exp(-0.5j * theta)), self.dtype(np.exp(0.5j * theta))
        self._launch(self.k_rzz, (self.psi, np.int64(2 ** self.N), np.int32(a), np.int32(b), same, diff))

    def z(self, n):
        self._launch(self.k_z, (self.psi, np.int64(2 ** self.N), np.int32(n), self.part))
        return float(self.part.sum())


def _sv(n, backend, precision):
    return (CupyDaily if backend == "cupy" else NumpyDaily)(n, np.complex64 if precision == "single" else np.complex128)


def _free_pool(backend):
    """Give the GPU memory back once the caller has dropped every reference to its state."""
    if backend == "cupy":
        import cupy as cp
        cp.get_default_memory_pool().free_all_blocks()


def apply(sv, op, idx):
    name, qs, p = op
    if name == "rzz":
        sv.rzz(idx[qs[0]], idx[qs[1]], p)
    elif name == "cz":
        sv.cz(idx[qs[0]], idx[qs[1]])
    else:
        sv.one(idx[qs[0]], p)


def full(circuits, backend="numpy", precision="double", log=None):
    """{t: {label: value}} for circuits = {t: QuantumCircuit} of one family and parameters on one patch (whole state).
    Also {"norm": {t: norm}, "seconds": ...}."""
    ts = sorted(circuits)
    progs = {t: program(circuits[t]) for t in ts}
    ops, readout, basis = progs[ts[-1]]
    cut = {}
    for t in ts:
        o, r, b = progs[t]
        if r != readout or b != basis or not _same(o, ops[:len(o)]):
            raise RuntimeError(f"the circuit at t = {t} is not a prefix of the one at t = {ts[-1]}")
        cut.setdefault(len(o), []).append(t)
    labels = sorted({q for o in ops for q in o[1]} | set(readout))
    if len(labels) > MAX_QUBITS:
        raise RuntimeError(f"{len(labels)} qubits: too many for the whole state")
    order = readout if set(readout) == set(labels) else labels  # C33: chain order; P32: ascending
    idx = {q: k for k, q in enumerate(order)}
    sv = _sv(len(labels), backend, precision)
    out, norms, t0 = {}, {}, time.time()
    read = (lambda q: sv.x(idx[q])) if basis == "X" else (lambda q: sv.z(idx[q]))
    for k in range(len(ops) + 1):
        for t in cut.get(k, []):
            out[t] = {q: read(q) for q in readout}
            norms[t] = sv.norm()
            if log:
                log(f"  t {t}: M {np.mean(list(out[t].values())):+.6f} norm {norms[t]:.8f} {time.time() - t0:.0f} s")
        if k < len(ops):
            apply(sv, ops[k], idx)
    del sv, read
    _free_pool(backend)
    return dict(values=out, norm=norms, basis=basis, seconds=round(time.time() - t0, 1))


def _same(a, b):
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x[0] != y[0] or x[1] != y[1]:
            return False
        if isinstance(x[2], np.ndarray) or isinstance(y[2], np.ndarray):
            if not np.array_equal(x[2], y[2]):
                return False
        elif x[2] != y[2]:
            return False
    return True


def cone_ops(ops, q):
    """(cone labels, kept ops) of <Z_q> after ops from |0...0>: the backward light cone, then the diagonal gates on
    qubits still in |0> dropped, repeated until nothing changes."""
    keep = list(ops)
    while True:
        S, D, back = {q}, {q}, []
        for op in reversed(keep):
            qs = set(op[1])
            if not qs & S:
                continue
            diag = op[0] in DIAGONAL
            if diag and (qs & S) <= D:
                continue
            back.append(op)
            if diag:
                D |= qs - S
            else:
                D -= qs
            S |= qs
        back.reverse()
        fresh, fwd = set(S), []
        for op in back:
            qs = set(op[1])
            if op[0] in DIAGONAL and qs <= fresh:
                continue
            if op[0] not in DIAGONAL:
                fresh -= qs
            fwd.append(op)
        if len(fwd) == len(keep):
            return sorted({x for o in fwd for x in o[1]} | {q}), fwd
        keep = fwd


def cone_sizes(qc):
    ops, readout, basis = program(qc)
    return {q: len(cone_ops(ops + ([("h", (q,), _H)] if basis == "X" else []), q)[0]) for q in readout}


def cones(qc, backend="numpy", precision="double", only=None, max_qubits=MAX_QUBITS, log=None):
    """{"values": {label: value or None}, "cone": {label: size}} of one circuit, each qubit from its own cone."""
    ops, readout, basis = program(qc)
    vals, sizes, t0 = {}, {}, time.time()
    for q in readout:
        o = ops + ([("h", (q,), _H)] if basis == "X" else [])
        cq, co = cone_ops(o, q)
        sizes[q] = len(cq)
        if (only is not None and q not in only) or len(cq) > max_qubits:
            vals[q] = None
            continue
        idx = {p: k for k, p in enumerate(cq)}
        sv = _sv(len(cq), backend, precision)
        for op in co:
            apply(sv, op, idx)
        vals[q] = sv.z(idx[q])
        del sv
        _free_pool(backend)
    if log:
        done = [v for v in vals.values() if v is not None]
        log(f"  {len(done)} of {len(vals)} qubits, largest cone {max(sizes.values())}, "
            f"M over them {np.mean(done) if done else float('nan'):+.6f}, {time.time() - t0:.0f} s")
    return dict(values=vals, cone=sizes, basis=basis, seconds=round(time.time() - t0, 1))


def groups(ids):
    """[(family, patch, params, [ids])] in the pool's order of first appearance: problems sharing an evolution."""
    out = []
    for pid in ids:
        _, fam, pa, par, t, _, _ = P.entry(pid)
        for g in out:
            if g[0] == fam and g[1] == pa and g[2] == par:
                g[3].append(pid)
                break
        else:
            out.append((fam, pa, par, [pid]))
    return out


def solve(ids, backend="cupy", precision="single", extra_ts=(), log=None):
    """{pid: {"values": {label: value}, "failed": bool, ...}} and {(family, patch, params text): {t: values}} for the
    extra t of the full-state groups (for the checks)."""
    res, extra = {}, {}
    for fam, pa, par, pids in groups(ids):
        if log:
            log(f"{fam} {pa} {P.params_text(par)}: {' '.join(pids)}")
        if pa in FULL:
            ts = sorted({P.entry(p)[4] for p in pids} | set(extra_ts))
            r = full({t: P.circuit(fam, pa, par, t) for t in ts}, backend, precision, log=log)
            for p in pids:
                t = P.entry(p)[4]
                res[p] = dict(values=r["values"][t], failed=False, norm=r["norm"][t], method="full",
                              seconds=r["seconds"])
            extra[(fam, pa, P.params_text(par))] = r["values"]
        else:
            for p in pids:
                t = P.entry(p)[4]
                if log:
                    log(f" {p} t {t}")
                r = cones(P.circuit(fam, pa, par, t), backend, precision, log=log)
                res[p] = dict(values=r["values"], failed=any(v is None for v in r["values"].values()),
                              cone=r["cone"], method="cone", seconds=r["seconds"])
    return res, extra


def summary(values):
    v = np.array([x for x in values.values() if x is not None])
    return dict(n=int(len(v)), M=float(np.mean(v)), abs_min=float(np.min(np.abs(v))), abs_max=float(np.max(np.abs(v))))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--ids", default=",".join(e[0] for e in P.POOL) + ",FX-B")
    ap.add_argument("--backend", default="cupy")
    ap.add_argument("--precision", default="single")
    a = ap.parse_args()
    res, _ = solve(a.ids.split(","), a.backend, a.precision, log=lambda s: print(s, flush=True))
    json.dump({p: dict(r, values={str(q): v for q, v in r["values"].items()}) for p, r in res.items()}, open(a.out, "w"))
