"""TOQB's noise model on CUDA-Q: a `toqb.traj2` Plan as a CUDA-Q kernel with inline noise (X22's engine factor).

The Plan already lists, in time order, every operation and channel traj2 applies; this module emits the same list as
one CUDA-Q kernel per circuit structure, with the structure's phase slots as the kernel's argument (list[float]):

- ("g1", q, slot, G, dep, g, pz): rz(slot angle) on q, then G (sx or x, with the stand-in's over-rotation) as a u3,
  then DepolarizationChannel(3 dep / 4), PhaseFlipChannel(pz), AmplitudeDampingChannel(g). traj2 draws a Pauli with
  probabilities (1 - 3 dep / 4, dep / 4, dep / 4, dep / 4), which is CUDA-Q's depolarization with p = 3 dep / 4; phase
  and amplitude damping commute as channels (their Kraus operators differ only by signs), so the order is immaterial.
- ("cz", a, b, dep, ga, pza, gb, pzb): cz, Depolarization2(15 dep / 16) (traj2: identity 1 - 15 dep / 16, each of
  the 15 other Paulis dep / 16), then phase flip and amplitude damping on each qubit.
- ("zz", a, b, th): RZZ(th) = cx(a, b) rz(th, b) cx(a, b), noiseless (static crosstalk).
- ("relax", q, g, pz): idle relaxation, phase flip and amplitude damping.
- measurement of clbit 0's qubit; the readout error is applied to <Z> as in traj2:
  z -> (1 - p01 - p10) z + (p10 - p01).

Each shot of `cudaq.sample` under a noise model is one trajectory on the "nvidia" target, so <Z> from T shots is the
trajectory estimate with one shot per trajectory (traj2 uses the exact P(1) of each trajectory instead: same mean,
slightly larger variance here). `check_cudaq` tests this engine against traj2 before any use.
"""
import cmath
import math

import numpy as np


def u3_params(G):
    """(theta, phi, lam) with G = exp(i alpha) U3(theta, phi, lam), U3 as in OpenQASM:
    [[cos t/2, -e^{i lam} sin t/2], [e^{i phi} sin t/2, e^{i (phi + lam)} cos t/2]]."""
    G = np.asarray(G, dtype=complex)
    a, b = abs(G[0, 0]), abs(G[1, 0])
    theta = 2 * math.atan2(b, a)
    if a > 1e-12:
        alpha = cmath.phase(G[0, 0])
        phi = cmath.phase(G[1, 0]) - alpha if b > 1e-12 else 0.0
        lam = (cmath.phase(-G[0, 1]) - alpha) if b > 1e-12 else cmath.phase(G[1, 1]) - alpha - phi
    else:  # theta = pi: only the off-diagonal entries
        lam = 0.0
        alpha = cmath.phase(-G[0, 1])
        phi = cmath.phase(G[1, 0]) - alpha
    return float(theta), float(phi), float(lam)


def u3_matrix(theta, phi, lam):
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    return np.array([[c, -cmath.exp(1j * lam) * s], [cmath.exp(1j * phi) * s, cmath.exp(1j * (phi + lam)) * c]])


class CudaqEngine:
    """Kernels of traj2 Plans on CUDA-Q (built once per Plan), <Z> of clbit 0 by trajectories."""

    def __init__(self, target="nvidia", options=None):
        import cudaq
        self.cudaq = cudaq
        if options:
            cudaq.set_target(target, **options)
        else:
            cudaq.set_target(target)
        self.target = target
        self.noise = cudaq.NoiseModel()
        self._kernels = {}

    def kernel(self, pl):
        hit = self._kernels.get(id(pl))
        if hit is not None:
            return hit
        cq = self.cudaq
        kernel, ang = cq.make_kernel(list)
        q = kernel.qalloc(pl.n)
        n_noise = 0

        def noise(ch, p, *qs):
            nonlocal n_noise
            if p > 0:
                kernel.apply_noise(ch, float(min(p, 1.0)), *[q[i] for i in qs])
                n_noise += 1
        for st in pl.steps:
            kind = st[0]
            if kind == "g1":
                _, k, slot, G, dep, g, pz = st
                kernel.rz(ang[slot], q[k])
                kernel.u3(*u3_params(G), q[k])
                noise(cq.DepolarizationChannel, 0.75 * dep, k)
                noise(cq.PhaseFlipChannel, pz, k)
                noise(cq.AmplitudeDampingChannel, g, k)
            elif kind == "cz":
                _, a, b, dep, ga, pza, gb, pzb = st
                kernel.cz(q[a], q[b])
                noise(cq.Depolarization2, 15 * dep / 16, a, b)
                noise(cq.PhaseFlipChannel, pza, a)
                noise(cq.AmplitudeDampingChannel, ga, a)
                noise(cq.PhaseFlipChannel, pzb, b)
                noise(cq.AmplitudeDampingChannel, gb, b)
            elif kind == "zz":
                _, a, b, th = st
                kernel.cx(q[a], q[b])
                kernel.rz(float(th), q[b])
                kernel.cx(q[a], q[b])
            elif kind == "relax":
                _, k, g, pz = st
                noise(cq.PhaseFlipChannel, pz, k)
                noise(cq.AmplitudeDampingChannel, g, k)
            else:
                raise ValueError(f"cudaq_engine: unknown step {kind}")
        q0, _, p01, p10 = next(m for m in pl.meas if m[1] == 0)
        kernel.mz(q[q0])
        hit = self._kernels[id(pl)] = (kernel, p01, p10, n_noise)
        return hit

    def z_mean(self, pl, A, T, seed):
        """Per row of A (slot angles), <Z> on clbit 0 from T trajectories (one shot each), readout included."""
        kernel, p01, p10, _ = self.kernel(pl)
        self.cudaq.set_random_seed(int(seed) % (2 ** 31))
        out = np.empty(len(A))
        for i, a in enumerate(np.asarray(A, dtype=float)):
            res = self.cudaq.sample(kernel, [float(x) for x in a], shots_count=int(T), noise_model=self.noise)
            p1 = res.probability("1")
            out[i] = (1 - p01 - p10) * (1 - 2 * p1) + (p10 - p01)
        return out

    def u3_selftest(self, k=6, seed=0):
        """Largest deviation (up to a global phase) between CUDA-Q's u3 and u3_matrix, over k random unitaries:
        both columns, from |0> and from x|0>."""
        cq = self.cudaq
        rng = np.random.default_rng(seed)
        worst = 0.0
        for _ in range(k):
            th, ph, la = rng.uniform(0, 2 * np.pi, 3)
            U = u3_matrix(th, ph, la)
            cols = []
            for flip in (0, 1):
                kern = cq.make_kernel()
                qq = kern.qalloc(1)
                if flip:
                    kern.x(qq[0])
                kern.u3(float(th), float(ph), float(la), qq[0])
                cols.append(np.array(cq.get_state(kern)).reshape(-1)[:2])
            V = np.stack(cols, axis=1)
            j = np.unravel_index(np.argmax(abs(U)), U.shape)
            V = V * (U[j] / V[j]) / abs(U[j] / V[j])
            worst = max(worst, float(np.abs(V - U).max()))
        return worst
