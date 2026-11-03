"""Exact answers of P4's chain (psf_os/dual.py) away from the dual-unitary point, by statevector, for chains too long
for a laptop (N = 33: 2^33 amplitudes, 64 GB in single precision; one 80 GB GPU).

The gates are read from psf_os.dual.chain_circuit itself (no second copy of the circuit): the preparation is
chain_circuit(N, 0), and layer k is the part chain_circuit(N, k + 1) adds to chain_circuit(N, k) (checked: the
instruction lists compose exactly). <X_n> for every site is read after every layer from the state itself
(2 Re sum conj(psi_i0) psi_i1 over the pairs of index bit n), so one evolution gives every t.

Backends: numpy (any size that fits; the tests) and cupy (raw CUDA kernels working in place: a one-qubit gate, CZ and
the X reduction need no second state-sized array). Qubit k is index bit k (Qiskit's order).

usage (pod): python gpu/du_answers.py OUT.json --N 33 --t-max 16 --h 0.15 --kicks 0.6853981634,0.5853981634
             [--precision single|double] [--backend cupy|numpy]
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np


def instructions(N, t_max, h, kick):
    """[prep, layer 1, ..., layer t_max]: lists of (name, qubits, 2x2 matrix or None), read from dual.chain_circuit."""
    from qiskit.quantum_info import Operator
    from psf_os import dual as DU

    def sig(c):
        return [(i.operation.name, tuple(c.find_bit(q).index for q in i.qubits), tuple(float(p) for p in i.operation.params))
                for i in c.data]
    full = [sig(DU.chain_circuit(N, t, h, kick, measure=False)) for t in range(t_max + 1)]
    for t in range(1, t_max + 1):
        if full[t][:len(full[t - 1])] != full[t - 1]:
            raise RuntimeError(f"chain_circuit(t = {t}) does not extend chain_circuit(t = {t - 1})")
    qc = DU.chain_circuit(N, t_max, h, kick, measure=False)
    ops = []
    for i in qc.data:
        q = tuple(qc.find_bit(x).index for x in i.qubits)
        if i.operation.name == "cz":
            ops.append(("cz", q, None))
        elif len(q) == 1:
            ops.append((i.operation.name, q, np.asarray(Operator(i.operation).data, dtype=complex)))
        else:
            raise RuntimeError(f"unexpected {i.operation.name} on {q}")
    cuts = [len(f) for f in full]
    return [ops[0:cuts[0]]] + [ops[cuts[t - 1]:cuts[t]] for t in range(1, t_max + 1)]


class NumpySV:
    def __init__(self, N, dtype):
        self.N = N
        self.psi = np.zeros(2 ** N, dtype=dtype)
        self.psi[0] = 1

    def _v(self, k):
        return self.psi.reshape(2 ** (self.N - k - 1), 2, 2 ** k)

    def one(self, k, U):
        v = self._v(k)
        a0, a1 = v[:, 0, :].copy(), v[:, 1, :].copy()
        v[:, 0, :] = U[0, 0] * a0 + U[0, 1] * a1
        v[:, 1, :] = U[1, 0] * a0 + U[1, 1] * a1

    def cz(self, a, b):
        idx = np.arange(2 ** self.N)
        self.psi[((idx >> a) & 1) & ((idx >> b) & 1) == 1] *= -1

    def x(self, n):
        v = self._v(n)
        return float(2 * np.real(np.vdot(v[:, 0, :], v[:, 1, :])))

    def norm(self):
        return float(np.vdot(self.psi, self.psi).real)


_CUDA = r"""
#include <cupy/complex.cuh>
typedef complex<REAL> C;
extern "C" __global__ void one(C* psi, long long half, int k, C u00, C u01, C u10, C u11) {
  for (long long j = blockIdx.x * (long long)blockDim.x + threadIdx.x; j < half; j += (long long)blockDim.x * gridDim.x) {
    long long lo = j & ((1LL << k) - 1);
    long long i0 = ((j >> k) << (k + 1)) | lo;
    long long i1 = i0 | (1LL << k);
    C a0 = psi[i0], a1 = psi[i1];
    psi[i0] = u00 * a0 + u01 * a1;
    psi[i1] = u10 * a0 + u11 * a1;
  }
}
extern "C" __global__ void cz(C* psi, long long size, int a, int b) {
  for (long long i = blockIdx.x * (long long)blockDim.x + threadIdx.x; i < size; i += (long long)blockDim.x * gridDim.x) {
    if (((i >> a) & 1) && ((i >> b) & 1)) psi[i] = -psi[i];
  }
}
extern "C" __global__ void xred(const C* psi, long long half, int k, double* out) {
  __shared__ double s[256];
  double acc = 0.0;
  for (long long j = blockIdx.x * (long long)blockDim.x + threadIdx.x; j < half; j += (long long)blockDim.x * gridDim.x) {
    long long lo = j & ((1LL << k) - 1);
    long long i0 = ((j >> k) << (k + 1)) | lo;
    long long i1 = i0 | (1LL << k);
    C a0 = psi[i0], a1 = psi[i1];
    acc += 2.0 * ((double)a0.real() * (double)a1.real() + (double)a0.imag() * (double)a1.imag());
  }
  s[threadIdx.x] = acc;
  __syncthreads();
  for (int w = blockDim.x / 2; w > 0; w >>= 1) {
    if (threadIdx.x < w) s[threadIdx.x] += s[threadIdx.x + w];
    __syncthreads();
  }
  if (threadIdx.x == 0) out[blockIdx.x] = s[0];
}
extern "C" __global__ void nred(const C* psi, long long size, double* out) {
  __shared__ double s[256];
  double acc = 0.0;
  for (long long i = blockIdx.x * (long long)blockDim.x + threadIdx.x; i < size; i += (long long)blockDim.x * gridDim.x) {
    C a = psi[i];
    acc += (double)a.real() * (double)a.real() + (double)a.imag() * (double)a.imag();
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


class CupySV:
    BLOCKS, THREADS = 4096, 256

    def __init__(self, N, dtype):
        import cupy as cp
        self.cp, self.N = cp, N
        real = "float" if dtype == np.complex64 else "double"
        mod = cp.RawModule(code=_CUDA.replace("REAL", real), options=("-std=c++17",))
        self.k_one, self.k_cz = mod.get_function("one"), mod.get_function("cz")
        self.k_x, self.k_n = mod.get_function("xred"), mod.get_function("nred")
        self.dtype = dtype
        self.psi = cp.zeros(2 ** N, dtype=dtype)
        self.psi[0] = 1
        self.part = cp.zeros(self.BLOCKS, dtype=cp.float64)

    def _launch(self, f, args):
        f((self.BLOCKS,), (self.THREADS,), args)

    def one(self, k, U):
        c = [self.dtype(U[r, s]) for r in (0, 1) for s in (0, 1)]
        self._launch(self.k_one, (self.psi, np.int64(2 ** (self.N - 1)), np.int32(k), *c))

    def cz(self, a, b):
        self._launch(self.k_cz, (self.psi, np.int64(2 ** self.N), np.int32(a), np.int32(b)))

    def x(self, n):
        self._launch(self.k_x, (self.psi, np.int64(2 ** (self.N - 1)), np.int32(n), self.part))
        return float(self.part.sum())

    def norm(self):
        self._launch(self.k_n, (self.psi, np.int64(2 ** self.N), self.part))
        return float(self.part.sum())


def run(N, t_max, h, kick, backend="numpy", precision="double", log=None):
    """{"x": [[<X_n> for n] for t = 0..t_max], "norm": [...], "seconds": ...}."""
    dtype = np.complex64 if precision == "single" else np.complex128
    sv = (CupySV if backend == "cupy" else NumpySV)(N, dtype)
    layers = instructions(N, t_max, h, kick)
    xs, norms, t0 = [], [], time.time()
    for t, ops in enumerate(layers):
        for name, q, U in ops:
            if name == "cz":
                sv.cz(*q)
            else:
                sv.one(q[0], U)
        xs.append([sv.x(n) for n in range(N)])
        norms.append(sv.norm())
        if log:
            log(f"N {N} h {h} kick {kick:.10f} t {t}: <X_t> {xs[-1][t] if t < N else float('nan'):+.6f} "
                f"norm {norms[-1]:.8f} {time.time() - t0:.0f} s")
    return dict(N=N, t_max=t_max, h=h, kick=kick, backend=backend, precision=precision, x=xs, norm=norms,
                seconds=round(time.time() - t0, 1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--t-max", type=int, required=True)
    ap.add_argument("--h", type=float, required=True)
    ap.add_argument("--kicks", required=True, help="comma-separated b values")
    ap.add_argument("--precision", default="single")
    ap.add_argument("--backend", default="cupy")
    a = ap.parse_args()
    res = [run(a.N, a.t_max, a.h, float(k), a.backend, a.precision, log=lambda s: print(s, flush=True))
           for k in a.kicks.split(",")]
    json.dump(res, open(a.out, "w"))
