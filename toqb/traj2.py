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

    # -- passes
    def _view1(self, psi, n, q):
        B = psi.shape[0]
        return psi.reshape(B, 2 ** q, 2, 2 ** (n - q - 1))

    def _apply1(self, psi, n, q, M):
        """M: (B, 2, 2) per trajectory."""
        xp = self.xp
        v = self._view1(psi, n, q)
        a0, a1 = v[:, :, 0, :], v[:, :, 1, :]
        m = M.reshape(-1, 2, 2, 1, 1)
        n0 = m[:, 0, 0] * a0 + m[:, 0, 1] * a1
        n1 = m[:, 1, 0] * a0 + m[:, 1, 1] * a1
        return xp.stack([n0, n1], axis=2).reshape(psi.shape)

    def _p1(self, psi, n, q):
        v = self._view1(psi, n, q)
        a1 = v[:, :, 1, :]
        return (a1.real ** 2 + a1.imag ** 2).sum(axis=(1, 2))

    def _amp_damp(self, psi, n, q, g, u):
        """Amplitude damping gamma on qubit q, the jump drawn with uniforms u (B,)."""
        xp = self.xp
        if g <= 0:
            return psi
        p1 = self._p1(psi, n, q)
        jump = u < g * p1
        s = math.sqrt(1 - g)
        nj = xp.sqrt(xp.maximum(1 - g * p1, 1e-30))
        jn = xp.sqrt(xp.maximum(p1, 1e-30))
        B = psi.shape[0]
        M = xp.zeros((B, 2, 2), dtype=self.dtype)
        M[:, 0, 0] = xp.where(jump, 0, 1 / nj)
        M[:, 1, 1] = xp.where(jump, 0, s / nj)
        M[:, 0, 1] = xp.where(jump, 1 / jn, 0)
        return self._apply1(psi, n, q, M)

    def _diag2(self, psi, n, a, b, d):
        """A fixed diagonal (d00, d01, d10, d11) on qubits a < b or b < a (big-endian: qubit 0 first)."""
        xp = self.xp
        B = psi.shape[0]
        lo, hi = min(a, b), max(a, b)
        v = psi.reshape(B, 2 ** lo, 2, 2 ** (hi - lo - 1), 2, 2 ** (n - hi - 1))
        dd = np.asarray(d, dtype=complex).reshape(2, 2)
        if a > b:
            dd = dd.T
        f = xp.asarray(dd, dtype=self.dtype).reshape(1, 1, 2, 1, 2, 1)
        return (v * f).reshape(psi.shape)

    # -- a batch
    def run(self, pl, A, T, seed):
        """Final states of T trajectories of each circuit (rows of A, slot angles) of Plan `pl`: (len(A) * T, 2^n)."""
        xp = self.xp
        n = pl.n
        P = A.shape[0]
        B = P * T
        rng = np.random.default_rng(seed)
        psi = xp.zeros((B, 2 ** n), dtype=self.dtype)
        psi[:, 0] = 1.0
        circ = np.repeat(np.arange(P), T)
        for st in pl.steps:
            kind = st[0]
            if kind == "g1":
                _, q, slot, G, dep, g, pz = st
                # per circuit G RZ(angle); per trajectory a Pauli from the depolarizing and the phase damping
                a = A[:, slot]
                rz = np.zeros((P, 2, 2), dtype=complex)
                rz[:, 0, 0] = np.exp(-0.5j * a)
                rz[:, 1, 1] = np.exp(0.5j * a)
                GR = G[None, :, :] @ rz  # (P, 2, 2)
                pk = rng.choice(4, size=B, p=[1 - 3 * dep / 4, dep / 4, dep / 4, dep / 4]) if dep > 0 \
                    else np.zeros(B, dtype=int)
                if pz > 0:
                    zf = rng.random(B) < pz
                    pk = np.where(zf, np.array(_ZMUL)[pk], pk)
                M = _PAULI[pk] @ GR[circ]
                psi = self._apply1(psi, n, q, xp.asarray(M, dtype=self.dtype))
                psi = self._amp_damp(psi, n, q, g, xp.asarray(rng.random(B), dtype=self.rdtype))
            elif kind == "cz":
                _, a, b, dep, ga, pza, gb, pzb = st
                psi = self._diag2(psi, n, a, b, (1, 1, 1, -1))
                if dep > 0:
                    k = rng.choice(16, size=B, p=[1 - 15 * dep / 16] + [dep / 16] * 15)
                else:
                    k = np.zeros(B, dtype=int)
                pa, pb = k // 4, k % 4
                if pza > 0:
                    pa = np.where(rng.random(B) < pza, np.array(_ZMUL)[pa], pa)
                if pzb > 0:
                    pb = np.where(rng.random(B) < pzb, np.array(_ZMUL)[pb], pb)
                if (pa != 0).any():
                    psi = self._apply1(psi, n, a, xp.asarray(_PAULI[pa], dtype=self.dtype))
                if (pb != 0).any():
                    psi = self._apply1(psi, n, b, xp.asarray(_PAULI[pb], dtype=self.dtype))
                psi = self._amp_damp(psi, n, a, ga, xp.asarray(rng.random(B), dtype=self.rdtype))
                psi = self._amp_damp(psi, n, b, gb, xp.asarray(rng.random(B), dtype=self.rdtype))
            elif kind == "zz":
                _, a, b, th = st
                e0, e1 = np.exp(-0.5j * th), np.exp(0.5j * th)
                psi = self._diag2(psi, n, a, b, (e0, e1, e1, e0))
            elif kind == "relax":
                _, q, g, pz = st
                if pz > 0:
                    zf = rng.random(B) < pz
                    if zf.any():
                        psi = self._apply1(psi, n, q, xp.asarray(_PAULI[np.where(zf, 3, 0)], dtype=self.dtype))
                psi = self._amp_damp(psi, n, q, g, xp.asarray(rng.random(B), dtype=self.rdtype))
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
