"""Trajectories, second engine: the same noise models as `toqb.traj`, with every channel split into parts that can be
drawn cheaply, so that a step is one or two passes over the batch of state vectors (a GPU's way of working).

TOQB's noise (`task_loop.NoisyDevice._model`, `s2r.StandIn._model`) is, after each sx or x: (the stand-in only) a
coherent over-rotation RX; a depolarizing error p; thermal relaxation (T1, T2) over the gate's duration; after each
cz: a two-qubit depolarizing error and thermal relaxation on both qubits; thermal relaxation on every delay; a readout
error at each measurement. Here:

- **Depolarizing** is a Pauli drawn with probabilities (1 - 3p/4, p/4, p/4, p/4) (two qubits: 1 - 15p/16 and p/16
  for each of the 15 others), independent of the state.
- **Thermal relaxation** is amplitude damping gamma = 1 - exp(-t/T1) followed by phase damping, a Z with probability
  (1 - exp(-t (1/T2 - 1/(2 T1)))) / 2 (equal to Aer's channel; checked to 1e-16). The Z is independent of the state and
  is drawn with the depolarizing Pauli (Z commutes with amplitude damping's operators up to a sign, a global phase of
  the trajectory). Amplitude damping needs the trajectory's P(qubit = 1): one reduction, then one pass that applies the
  jump |0><1| (probability gamma P1) or the no-jump diag(1, sqrt(1 - gamma)), normalised.
- **rz** are gathered per wire into the next sx or x as `traj.skeleton` does (exact: what they cross is diagonal or a
  channel covariant under Z rotations, up to a global phase per trajectory); a gate's matrix per trajectory is
  Pauli x Z x RX_over x G x RZ(angle of its circuit). cz and the stand-in's crosstalk rzz are diagonal and applied in
  place, in time order.

All random numbers of a batch are drawn on the host (numpy, the given seed) before it runs, so a batch is reproducible
on numpy or cupy up to rounding. `toqb.check_traj2` compares it with the density-matrix engines.
"""
import math
import os

import numpy as np

_SX = np.array([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]]) / 2
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_PAULI = np.array([np.eye(2), [[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]], dtype=complex)
_ZMUL = [3, 2, 1, 0]  # Z * P for P = I, X, Y, Z, up to a phase: Z, Y, X, I


def get_xp(name=None):
    name = name or os.environ.get("TOQB_XP", "numpy")
    if name == "cupy":
        import cupy
        return cupy
    return np


def _rx(t):
    c, s = math.cos(t / 2), math.sin(t / 2)
    return np.array([[c, -1j * s], [-1j * s, c]])


def _thermal(T1, T2, t):
    """(gamma, pz) of thermal relaxation over t (T2 already capped at 2 T1)."""
    if t <= 0:
        return 0.0, 0.0
    g = 1 - math.exp(-t / T1)
    pz = (1 - math.exp(-t * (1 / T2 - 1 / (2 * T1)))) / 2
    return g, max(pz, 0.0)


class Plan:
    """One circuit structure: steps, phase slots, measurements (see `plan`)."""

    def __init__(self, n, steps, meas, slot_keys, offset, act):
        self.n, self.steps, self.meas = n, steps, meas
        self.slot_keys, self.offset, self.act = slot_keys, np.asarray(offset, dtype=float), act
        self.index = {k: i for i, k in enumerate(slot_keys)}

    def angles(self, c):
        """Slot angles of compiled circuit `c` (as `traj.Skeleton.angles`)."""
        pos = {q: k for k, q in enumerate(self.act)}
        bit = {b: i for i, b in enumerate(c.qubits)}
        acc, cnt = {}, {}
        out = np.empty(len(self.slot_keys))
        for ins in c.data:
            name = ins.operation.name
            if name == "rz":
                w = pos[bit[ins.qubits[0]]]
                acc[w] = acc.get(w, 0.0) + float(ins.operation.params[0])
            elif name in ("sx", "x"):
                w = pos[bit[ins.qubits[0]]]
                k = cnt.get(w, 0)
                cnt[w] = k + 1
                out[self.index[(w, k)]] = acc.pop(w, 0.0)
        return out + self.offset


def _active(c):
    return tuple(sorted({c.find_bit(q).index for i in c.data if i.operation.name not in ("delay", "barrier")
                         for q in i.qubits}))


def plan(c, r, target, over=0.0):
    """The Plan of compiled circuit `c`'s structure on `target`'s noise (TOQB's model; `over`: the stand-in's
    over-rotation), from `r`: the circuit Aer runs for it (scheduled, compacted to c's active qubits, crosstalk and
    relaxation added), whose operations give the order, the delays and the crosstalk."""
    act = _active(c)
    T1 = [target.qubit_properties[q].t1 for q in act]
    T2 = [min(target.qubit_properties[q].t2, 2 * target.qubit_properties[q].t1) for q in act]
    dt = target.dt
    g2 = next(g for g in ("cz", "ecr", "cx") if g in target.operation_names)
    if g2 != "cz":
        raise ValueError("traj2: CZ devices only")
    # the representative's own slot sums (for the offsets r adds: crosstalk rz)
    pos_c = {q: k for k, q in enumerate(act)}
    bit = {b: i for i, b in enumerate(c.qubits)}
    base, a_c, n_c = {}, {}, {}
    for ins in c.data:
        name = ins.operation.name
        if name == "rz":
            w = pos_c[bit[ins.qubits[0]]]
            a_c[w] = a_c.get(w, 0.0) + float(ins.operation.params[0])
        elif name in ("sx", "x"):
            w = pos_c[bit[ins.qubits[0]]]
            k = n_c.get(w, 0)
            n_c[w] = k + 1
            base[(w, k)] = a_c.pop(w, 0.0)
    steps, meas, keys, offset = [], [], [], []
    acc, cnt = {}, {}
    for ins in r.data:
        op = ins.operation
        name = op.name
        qs = tuple(r.find_bit(q).index for q in ins.qubits)
        if name in ("barrier", "quantum_channel"):
            continue  # relaxation is taken from the delay itself
        if name == "delay":
            q = qs[0]
            t = float(op.params[0]) * (dt if op.unit == "dt" else {"s": 1, "us": 1e-6, "ns": 1e-9}.get(op.unit, 1.0))
            g, pz = _thermal(T1[q], T2[q], t)
            if g > 0 or pz > 0:
                steps.append(("relax", q, g, pz))
            continue
        if name == "rz":
            acc[qs[0]] = acc.get(qs[0], 0.0) + float(op.params[0])
            continue
        if name == "measure":
            q, cb = qs[0], r.find_bit(ins.clbits[0]).index
            e = min(max(target["measure"][(act[q],)].error or 0.0, 0.0), 0.5)
            meas.append((q, cb, e, e))
            continue
        if name in ("sx", "x"):
            q = qs[0]
            kk = cnt.get(q, 0)
            cnt[q] = kk + 1
            keys.append((q, kk))
            offset.append(acc.pop(q, 0.0) - base[(q, kk)])
            p = target[name][(act[q],)]
            G = (_SX if name == "sx" else _X)
            if over:
                G = _rx(over * (math.pi / 2 if name == "sx" else math.pi)) @ G
            dep = min(max(p.error or 0.0, 0.0), 0.5)
            g, pz = _thermal(T1[q], T2[q], p.duration)
            steps.append(("g1", q, len(keys) - 1, G, dep, g, pz))
            continue
        if name == "cz":
            a, b = qs
            p = target["cz"][(act[a], act[b])]
            dep = min(max(p.error or 0.0, 0.0), 0.75)
            ga, pza = _thermal(T1[a], T2[a], p.duration)
            gb, pzb = _thermal(T1[b], T2[b], p.duration)
            steps.append(("cz", a, b, dep, ga, pza, gb, pzb))
            continue
        if name == "rzz":
            th = float(op.params[0])
            steps.append(("zz", qs[0], qs[1], th))
            continue
        raise ValueError(f"traj2: unsupported operation {name}")
    return Plan(r.num_qubits, steps, meas, keys, offset, act)


class Engine:
    """Batches of trajectories of one Plan (circuits x T) on numpy or cupy, complex64 by default."""

    def __init__(self, xp=None, dtype=None):
        self.xp = xp or get_xp()
        self.dtype = getattr(self.xp, dtype or os.environ.get("TOQB_TRAJ_DTYPE", "complex64"))
        self.rdtype = self.xp.float32 if self.dtype == self.xp.complex64 else self.xp.float64

    # -- passes (in place on views (B, 2^q, 2, rest); on cupy each is one fused kernel)
    def _view1(self, psi, n, q):
        B = psi.shape[0]
        return psi.reshape(B, 2 ** q, 2, 2 ** (n - q - 1))

    def _kernels(self):
        if getattr(self, "_k", None) is None:
            xp = self.xp
            if xp is np or os.environ.get("TOQB_TRAJ_KERNELS", "1") == "0":
                self._k = False
            else:
                self._k = dict(
                    mat=xp.ElementwiseKernel(
                        "T a0, T a1, T m00, T m01, T m10, T m11", "T b0, T b1",
                        "T x = a0, y = a1; b0 = m00 * x + m01 * y; b1 = m10 * x + m11 * y;", "toqb_mat1"),
                    pauli=xp.ElementwiseKernel(
                        "T a0, T a1, int8 k", "T b0, T b1",
                        "T x = a0, y = a1; if (k == 1) { b0 = y; b1 = x; } "
                        "else if (k == 2) { b0 = T(y.imag(), -y.real()); b1 = T(-x.imag(), x.real()); } "
                        "else if (k == 3) { b0 = x; b1 = -y; } else { b0 = x; b1 = y; }", "toqb_pauli"),
                    ad=xp.ElementwiseKernel(
                        "T a0, T a1, R p1, R u, R g", "T b0, T b1",
                        "T x = a0, y = a1; "
                        "if (u < g * p1) { b0 = y * (R(1) / sqrt(max(p1, R(1e-30)))); b1 = T(0, 0); } "
                        "else { R inj = R(1) / sqrt(max(R(1) - g * p1, R(1e-30))); "
                        "b0 = x * inj; b1 = y * (sqrt(R(1) - g) * inj); }", "toqb_ad"),
                    norm=xp.ReductionKernel(
                        f"{np.dtype(self.dtype).name} a", f"{np.dtype(self.rdtype).name} y",
                        "a.real() * a.real() + a.imag() * a.imag()", "a + b", "y = a", "0", "toqb_norm2"))
        return self._k

    def _mat1(self, psi, n, q, M):
        """M: (B, 2, 2) per trajectory, in place."""
        v = self._view1(psi, n, q)
        a0, a1 = v[:, :, 0, :], v[:, :, 1, :]
        m = M.reshape(-1, 2, 2, 1, 1)
        k = self._kernels()
        if k:
            k["mat"](a0, a1, m[:, 0, 0], m[:, 0, 1], m[:, 1, 0], m[:, 1, 1], a0, a1)
        else:
            n0 = m[:, 0, 0] * a0 + m[:, 0, 1] * a1
            n1 = m[:, 1, 0] * a0 + m[:, 1, 1] * a1
            a0[...] = n0
            a1[...] = n1

    def _pauli(self, psi, n, q, kk):
        """A Pauli per trajectory (kk: int8 (B,), 0 I, 1 X, 2 Y, 3 Z), in place."""
        v = self._view1(psi, n, q)
        a0, a1 = v[:, :, 0, :], v[:, :, 1, :]
        k = self._kernels()
        kb = kk.reshape(-1, 1, 1)
        if k:
            k["pauli"](a0, a1, kb, a0, a1)
        elif bool((kk != 0).any()):
            self._mat1(psi, n, q, self.xp.asarray(_PAULI, dtype=self.dtype)[kk.astype(int)])

    def _p1(self, psi, n, q):
        v = self._view1(psi, n, q)
        a1 = v[:, :, 1, :]
        k = self._kernels()
        if k:
            return k["norm"](a1, axis=(1, 2))
        return (a1.real ** 2 + a1.imag ** 2).sum(axis=(1, 2))

    def _amp_damp(self, psi, n, q, g, u):
        """Amplitude damping gamma on qubit q, the jump drawn with uniforms u (B,), in place."""
        xp = self.xp
        if g <= 0:
            return
        p1 = self._p1(psi, n, q)
        v = self._view1(psi, n, q)
        a0, a1 = v[:, :, 0, :], v[:, :, 1, :]
        sh = (-1, 1, 1)
        k = self._kernels()
        if k:
            k["ad"](a0, a1, p1.reshape(sh), u.reshape(sh), self.rdtype(g), a0, a1)
            return
        jump = u < g * p1
        inj = 1 / xp.sqrt(xp.maximum(1 - g * p1, 1e-30))
        M = xp.zeros((psi.shape[0], 2, 2), dtype=self.dtype)
        M[:, 0, 0] = xp.where(jump, 0, inj)
        M[:, 1, 1] = xp.where(jump, 0, math.sqrt(1 - g) * inj)
        M[:, 0, 1] = xp.where(jump, 1 / xp.sqrt(xp.maximum(p1, 1e-30)), 0)
        self._mat1(psi, n, q, M)

    def _diag2(self, psi, n, a, b, f):
        """A diagonal on qubits a, b given as a device array f (1, 1, 2, 1, 2, 1) in (lower, higher) order, in place."""
        B = psi.shape[0]
        lo, hi = min(a, b), max(a, b)
        v = psi.reshape(B, 2 ** lo, 2, 2 ** (hi - lo - 1), 2, 2 ** (n - hi - 1))
        v *= f

    def _dev(self, d, a, b):
        dd = np.asarray(d, dtype=complex).reshape(2, 2)
        if a > b:
            dd = dd.T
        return self.xp.asarray(dd, dtype=self.dtype).reshape(1, 1, 2, 1, 2, 1)

    # -- a batch
    def run(self, pl, A, T, seed):
        """Final states of T trajectories of each circuit (rows of A, slot angles) of Plan `pl`: (len(A) * T, 2^n).
        Every random number and every per-trajectory matrix is drawn and built on the host first, in one pass over
        the steps, and sent to the device at once; the device then runs one or two kernels per step."""
        xp = self.xp
        n = pl.n
        P = A.shape[0]
        B = P * T
        rng = np.random.default_rng(seed)
        circ = np.repeat(np.arange(P), T)
        zmul = np.array(_ZMUL, dtype=np.int8)
        mats, paulis, unif, ops = [], [], [], []
        for st in pl.steps:
            kind = st[0]
            if kind == "g1":
                _, q, slot, G, dep, g, pz = st
                a = A[:, slot]
                rz = np.zeros((P, 2, 2), dtype=complex)
                rz[:, 0, 0] = np.exp(-0.5j * a)
                rz[:, 1, 1] = np.exp(0.5j * a)
                GR = G[None, :, :] @ rz
                pk = (rng.choice(4, size=B, p=[1 - 3 * dep / 4, dep / 4, dep / 4, dep / 4]) if dep > 0
                      else np.zeros(B, dtype=int)).astype(np.int8)
                if pz > 0:
                    pk = np.where(rng.random(B) < pz, zmul[pk], pk)
                ops.append(("m", q, len(mats)))
                mats.append(_PAULI[pk] @ GR[circ])
                if g > 0:
                    ops.append(("ad", q, g, len(unif)))
                    unif.append(rng.random(B))
            elif kind == "cz":
                _, a, b, dep, ga, pza, gb, pzb = st
                ops.append(("d", a, b, "cz"))
                k = (rng.choice(16, size=B, p=[1 - 15 * dep / 16] + [dep / 16] * 15) if dep > 0
                     else np.zeros(B, dtype=int))
                pa, pb = (k // 4).astype(np.int8), (k % 4).astype(np.int8)
                if pza > 0:
                    pa = np.where(rng.random(B) < pza, zmul[pa], pa)
                if pzb > 0:
                    pb = np.where(rng.random(B) < pzb, zmul[pb], pb)
                ops.append(("p", a, len(paulis)))
                paulis.append(pa)
                ops.append(("p", b, len(paulis)))
                paulis.append(pb)
                for qq, gg in ((a, ga), (b, gb)):
                    if gg > 0:
                        ops.append(("ad", qq, gg, len(unif)))
                        unif.append(rng.random(B))
            elif kind == "zz":
                _, a, b, th = st
                e0, e1 = np.exp(-0.5j * th), np.exp(0.5j * th)
                ops.append(("d", a, b, (e0, e1, e1, e0)))
            elif kind == "relax":
                _, q, g, pz = st
                if pz > 0:
                    ops.append(("p", q, len(paulis)))
                    paulis.append(np.where(rng.random(B) < pz, 3, 0).astype(np.int8))
                if g > 0:
                    ops.append(("ad", q, g, len(unif)))
                    unif.append(rng.random(B))
        Md = xp.asarray(np.stack(mats) if mats else np.zeros((0, B, 2, 2)), dtype=self.dtype)
        Pd = xp.asarray(np.stack(paulis) if paulis else np.zeros((0, B)), dtype=xp.int8)
        Ud = xp.asarray(np.stack(unif) if unif else np.zeros((0, B)), dtype=self.rdtype)
        diag = {}
        psi = xp.zeros((B, 2 ** n), dtype=self.dtype)
        psi[:, 0] = 1.0
        for op in ops:
            kind = op[0]
            if kind == "m":
                self._mat1(psi, n, op[1], Md[op[2]])
            elif kind == "p":
                self._pauli(psi, n, op[1], Pd[op[2]])
            elif kind == "ad":
                self._amp_damp(psi, n, op[1], op[2], Ud[op[3]])
            else:
                _, a, b, d = op
                key = (a, b, d if isinstance(d, str) else tuple(np.round(d, 12)))
                f = diag.get(key)
                if f is None:
                    f = diag[key] = self._dev((1, 1, 1, -1) if d == "cz" else d, a, b)
                self._diag2(psi, n, a, b, f)
        return psi, rng

    def _chunks(self, P, T, n):
        """(circuits per chunk, trajectories per chunk) so that a batch stays within TOQB_TRAJ_MEM_GB (default 2) of
        state vectors and temporaries (about six copies)."""
        mem = float(os.environ.get("TOQB_TRAJ_MEM_GB", "2")) * 1e9
        per = np.dtype(np.complex64 if self.dtype == self.xp.complex64 else np.complex128).itemsize * 6 * 2 ** n
        amps = max(int(mem // per), 1)
        if T <= amps:
            return max(min(P, amps // T), 1), T
        return 1, amps

    def _p1_batches(self, pl, A, T, seed):
        """P(clbit 0's qubit = 1) of every trajectory, (len(A), T) numpy, run in chunks (each its own seed)."""
        q = next(m for m in pl.meas if m[1] == 0)[0]
        P = A.shape[0]
        cp, ct = self._chunks(P, T, pl.n)
        out = np.empty((P, T))
        k = 0
        for i in range(0, P, cp):
            for j in range(0, T, ct):
                t = min(ct, T - j)
                psi, _ = self.run(pl, A[i:i + cp], t, seed * 1009 + k)
                k += 1
                p1 = self._p1(psi, pl.n, q)
                p1 = np.asarray(p1.get() if hasattr(p1, "get") else p1, dtype=float)
                out[i:i + cp, j:j + t] = p1.reshape(-1, t)
                del psi
        return out

    def z_mean(self, pl, A, T, seed):
        """Per circuit, the mean over T trajectories of <Z> on clbit 0's qubit, readout included."""
        _, _, p01, p10 = next(m for m in pl.meas if m[1] == 0)
        z = (1 - 2 * self._p1_batches(pl, A, T, seed)).mean(axis=1)
        return (1 - p01 - p10) * z + (p10 - p01)

    def z_shots(self, pl, A, shots, seed):
        """Per circuit, <Z> on clbit 0 from `shots` shots (one trajectory each, outcome and readout drawn)."""
        _, _, p01, p10 = next(m for m in pl.meas if m[1] == 0)
        p1 = self._p1_batches(pl, A, shots, seed)
        rng = np.random.default_rng(seed + 1)
        v = rng.random(p1.shape) < p1
        flip = rng.random(p1.shape)
        v = np.where(v, flip >= p10, flip < p01)
        return 1 - 2 * v.mean(axis=1)
