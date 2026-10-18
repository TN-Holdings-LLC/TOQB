"""A trajectory engine for TOQB's noise models: the same noisy circuits, state vectors instead of density matrices.

TOQB's two exact engines keep a density matrix: Aer's (`task_loop.NoisyDevice`, `s2r.StandIn`) and `fast_noise`'s.
Its size is 4^n: at 10-14 active qubits a circuit takes seconds to minutes, or does not fit in memory. This engine
runs the same noisy circuit as quantum trajectories (Monte Carlo wave functions): each trajectory is a state vector
(2^n), and every noise channel is applied by drawing one of its Kraus operators with its probability for that state.
The average over trajectories of any quantity equals the density-matrix value; one trajectory per shot gives counts
with exactly Aer's distribution (an unbiased sampler of the same channel), not Aer's random stream.

- **The same noisy circuit.** `program_from_aer(r, nm)` reads the circuit Aer would run (`r`: scheduled, compacted,
  relaxation on delays, crosstalk if any) and its NoiseModel (`nm`): every gate's error from the model's local errors,
  every channel in the circuit, every readout error. So the simulator's model (`NoisyDevice`) and the stand-in's
  (`StandIn`) are run unchanged.
- **Fused.** Gates without an error (rz, rzz crosstalk, ...) are kept pending per qubit and multiplied into the next
  operation on that qubit; a gate's error absorbs the gate (each Kraus operator K becomes K U). A Kraus set is reduced
  to its minimal rank (at most 4 on one qubit, 16 on two). A circuit becomes one Kraus draw per noisy gate.
- **Batched, on numpy or cupy.** All trajectories of a circuit, or of several circuits with the same structure, are
  evolved together as one array (`xp`: numpy, or cupy on a GPU when TOQB_XP=cupy). TOQB_TRAJ_DTYPE: complex128 by
  default; complex64 halves memory and time on a GPU (check_traj passes with either). Random numbers come from numpy's
  generator with the given seed, so a run is reproducible on either backend up to floating-point rounding.

Two outputs per circuit:
- `z_traj(...)`: the mean over T trajectories of each trajectory's exact <Z> on clbit 0's qubit, times readout's
  (1 - p01 - p10) and shifted by (p10 - p01) -- an unbiased estimate of the noisy <Z>, with less variance than shots;
- `counts(...)`: one trajectory per shot, its outcome drawn from |psi|^2, then readout errors drawn: counts with
  Aer's distribution.

`toqb.check_traj` compares both with the density-matrix engines.
"""
import math
import os

import numpy as np


def get_xp(name=None):
    name = name or os.environ.get("TOQB_XP", "numpy")
    if name == "cupy":
        import cupy
        return cupy
    return np


def _be(mat, k):
    """A matrix from Qiskit's little-endian order over (q0, q1, ...) to big-endian over the same list."""
    t = np.asarray(mat, dtype=complex).reshape((2,) * (2 * k))
    perm = list(range(k - 1, -1, -1)) + list(range(2 * k - 1, k - 1, -1))
    return t.transpose(perm).reshape(2 ** k, 2 ** k)


def _kraus_min(channel, k):
    """Minimal-rank Kraus operators (big-endian) of a channel (a QuantumError or any Qiskit channel), heaviest first."""
    from qiskit.quantum_info import Choi, Kraus
    Ks = [_be(K, k) for K in Kraus(Choi(channel)).data]
    return sorted(Ks, key=lambda K: -float(np.real(np.trace(K.conj().T @ K))))


class Program:
    """A noisy circuit as a list of steps on n qubits (big-endian, qubit 0 first):
    ("u", qs, U) a unitary; ("k", qs, [K...]) a channel; and the measurements [(qubit, clbit, p01, p10)]."""

    def __init__(self, n, steps, meas, num_clbits):
        self.n, self.steps, self.meas, self.num_clbits = n, steps, meas, num_clbits

    def structure(self):
        return (self.n, tuple((s[0], s[1], len(s[2]) if s[0] == "k" else 0) for s in self.steps), tuple(self.meas))


_KRAUS = {}  # (id of the noise model, key) -> heaviest-first Kraus operators; a model is kept per active set by its owner
_SX = np.array([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]]) / 2
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_CZ = np.diag([1, 1, 1, -1]).astype(complex)


def _gate(op, k):
    """A gate's big-endian matrix, in closed form for the device's gates."""
    name = op.name
    if name == "rz":
        t = float(op.params[0])
        return np.diag([np.exp(-0.5j * t), np.exp(0.5j * t)])
    if name == "sx":
        return _SX
    if name == "x":
        return _X
    if name == "cz":
        return _CZ
    if name == "rzz":
        t = float(op.params[0])
        return np.diag(np.exp(-0.5j * t * np.array([1, -1, -1, 1])))
    from qiskit.quantum_info import Operator
    return _be(Operator(op).data, k)


def program_from_aer(r, nm):
    """The Program of the circuit `r` as Aer runs it under the NoiseModel `nm`."""
    n = r.num_qubits
    pend = {}  # qubit -> pending big-endian 2x2 unitary
    steps = []
    meas = []
    local = nm._local_quantum_errors
    ro = nm._local_readout_errors
    last_delay = {}
    tag = id(nm)

    def take(qs):
        """The pending unitaries of qs as one operator on qs (identity where none), and clear them."""
        U = np.eye(1, dtype=complex)
        for q in qs:
            U = np.kron(U, pend.pop(q, np.eye(2, dtype=complex)))
        return U

    def kraus(key, make):
        hit = _KRAUS.get((tag, key))
        if hit is None:
            hit = _KRAUS[(tag, key)] = make()
        return hit

    for ins in r.data:
        op = ins.operation
        name = op.name
        qs = tuple(r.find_bit(q).index for q in ins.qubits)
        if name == "barrier":
            continue
        if name == "delay":
            last_delay[qs[0]] = (float(op.params[0]), op.unit)
            continue
        if name == "measure":
            q, c = qs[0], r.find_bit(ins.clbits[0]).index
            if q in pend:
                steps.append(("u", (q,), pend.pop(q)))
            e = ro.get((q,))
            p = np.asarray(e.probabilities) if e is not None else np.eye(2)
            meas.append((q, c, float(p[0][1]), float(p[1][0])))
            continue
        k = len(qs)
        if name == "quantum_channel":
            d = last_delay.pop(qs[0], None) if k == 1 else None
            key = ("relax", qs, d) if d is not None else None
            Ks0 = kraus(key, lambda: _kraus_min(op._quantum_error, k)) if key else _kraus_min(op._quantum_error, k)
            P = take(qs)
            Ks = [K @ P for K in Ks0]
        else:
            err = local.get(name, {}).get(qs)
            U = _gate(op, k)
            if err is None:
                if k == 1:
                    q = qs[0]
                    pend[q] = U @ pend.get(q, np.eye(2, dtype=complex))
                else:
                    steps.append(("u", qs, U @ take(qs)))
                continue
            G = U @ take(qs)
            Ks = [K @ G for K in kraus(("err", name, qs), lambda: _kraus_min(err, k))]
        steps.append(("u", qs, Ks[0]) if len(Ks) == 1 else ("k", qs, Ks))
    for q in sorted(pend):
        steps.append(("u", (q,), pend[q]))
    return Program(n, steps, meas, r.num_clbits)


class Engine:
    """Evolves Programs as batches of trajectories on `xp` (numpy or cupy)."""

    def __init__(self, xp=None, dtype=None):
        self.xp = xp or get_xp()
        self.dtype = getattr(self.xp, dtype or os.environ.get("TOQB_TRAJ_DTYPE", "complex128"))

    def _apply(self, psi, n, qs, U):
        """psi: (B, 2, ..., 2); U: (2^k, 2^k) or (B, 2^k, 2^k) on qubits qs."""
        xp = self.xp
        k = len(qs)
        axes = [1 + q for q in qs]
        moved = xp.moveaxis(psi, axes, list(range(-k, 0)))
        sh = moved.shape
        flat = moved.reshape(sh[0], -1, 2 ** k)
        if U.ndim == 2:
            out = flat @ U.T
        else:
            out = xp.matmul(flat, xp.swapaxes(U, 1, 2))
        return xp.moveaxis(out.reshape(sh), list(range(-k, 0)), axes)

    def evolve(self, programs, T, rng):
        """Final states of T trajectories of each program (all of one structure): array (len * T, 2, ..., 2)."""
        xp = self.xp
        p0 = programs[0]
        n = p0.n
        P = len(programs)
        B = P * T
        psi = xp.zeros((B,) + (2,) * n, dtype=self.dtype)
        psi[(slice(None),) + (0,) * n] = 1.0
        for j, st in enumerate(p0.steps):
            kind, qs = st[0], st[1]
            if kind == "u":
                if P == 1:
                    U = xp.asarray(st[2], dtype=self.dtype)
                else:
                    U = xp.asarray(np.repeat(np.stack([p.steps[j][2] for p in programs]), T, axis=0), dtype=self.dtype)
                psi = self._apply(psi, n, qs, U)
                continue
            r = len(st[2])
            u = xp.asarray(rng.random(B))
            Ks = [xp.asarray(st[2][i], dtype=self.dtype) if P == 1 else
                  xp.asarray(np.repeat(np.stack([p.steps[j][2][i] for p in programs]), T, axis=0), dtype=self.dtype)
                  for i in range(r)]
            # the Kraus operators are in decreasing weight: most trajectories take the first; the others are carried
            # to the next operator only as a subset (rem)
            acc = xp.zeros(B)
            rem = xp.arange(B)
            sub = psi
            for i in range(r):
                K = Ks[i] if P == 1 else Ks[i][rem]
                phi = self._apply(sub, n, qs, K)
                w = (xp.abs(phi.reshape(phi.shape[0], -1)) ** 2).sum(axis=1)
                acc[rem] += w
                pick = (acc[rem] >= u[rem]) if i < r - 1 else xp.ones(rem.shape[0], dtype=bool)
                if bool(pick.any()):
                    norm = xp.sqrt(xp.maximum(w[pick], 1e-300)).reshape((-1,) + (1,) * n)
                    psi[rem[pick]] = phi[pick] / norm
                keep = ~pick
                if not bool(keep.any()):
                    break
                rem = rem[keep]
                sub = sub[keep]
        return psi

    def z_traj(self, programs, T, seed):
        """Per program, the mean over T trajectories of <Z> on clbit 0's qubit, readout included (numpy array)."""
        xp = self.xp
        rng = np.random.default_rng(seed)
        psi = self.evolve(programs, T, rng)
        p0 = programs[0]
        n = p0.n
        q, _, p01, p10 = next(m for m in p0.meas if m[1] == 0)
        prob = xp.abs(psi) ** 2
        p1 = xp.moveaxis(prob, 1 + q, -1).reshape(len(programs) * T, -1, 2).sum(axis=1)[:, 1]
        z = 1 - 2 * p1
        z = z.reshape(len(programs), T).mean(axis=1)
        z = (1 - p01 - p10) * z + (p10 - p01)
        return np.asarray(z.get() if hasattr(z, "get") else z)

    def counts(self, programs, shots, seed):
        """Per program, Qiskit-style counts of `shots` shots (one trajectory each)."""
        xp = self.xp
        rng = np.random.default_rng(seed)
        psi = self.evolve(programs, shots, rng)
        p0 = programs[0]
        n = p0.n
        B = psi.shape[0]
        prob = (xp.abs(psi) ** 2).reshape(B, -1)
        cum = xp.cumsum(prob, axis=1)
        u = xp.asarray(rng.random(B)) * cum[:, -1]
        idx = (cum < u[:, None]).sum(axis=1)
        idx = np.asarray(idx.get() if hasattr(idx, "get") else idx)
        flips = rng.random((B, len(p0.meas)))
        out = []
        for pi in range(len(programs)):
            cnt = {}
            for s in range(shots):
                b = pi * shots + s
                bits = ["0"] * p0.num_clbits
                for mi, (q, c, p01, p10) in enumerate(p0.meas):
                    v = (int(idx[b]) >> (n - 1 - q)) & 1
                    if v == 0 and flips[b, mi] < p01:
                        v = 1
                    elif v == 1 and flips[b, mi] < p10:
                        v = 0
                    bits[p0.num_clbits - 1 - c] = str(v)
                key = "".join(bits)
                cnt[key] = cnt.get(key, 0) + 1
            out.append(cnt)
        return out
