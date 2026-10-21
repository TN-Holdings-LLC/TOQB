"""The fast path of the PSF template arm (2026-10-21): the model's parameters straight to the simulator's slot angles,
with the template's closed-form binding in Rust (PSF-Zero's `rust/psfbind`, C ABI through ctypes).

The usual path builds, per point, the model as a Qiskit circuit, checks its structure, reads its angles, binds the
template (`psf_ai_compile.RingTemplate.angles`), assigns them into a Qiskit circuit, and the simulator reads the slot
angles back from that circuit (`traj2` skeleton). Here, for the one structure every point of the model shares:

    values = gather(angle_list(theta, x))            the input's rz / ry angles in the template's order (a fixed index)
    params = psfbind_angles(template runs, values)   RingTemplate.angles, in Rust, for a whole batch
    slots  = params @ M.T + b                        the skeleton's slot angles: affine in the template's parameters

`gather`, M and b are read once from the slow path itself (probing with distinct values and unit vectors), not
written by hand. `check(...)` compares the two paths on given points; nothing here changes the slow path, and a run
uses this path only when it asks for it. Only RingTemplate (psf_ai_compile item 35) is supported; any other template
raises Unsupported.
"""
from __future__ import annotations

import ctypes
import glob
import os

import numpy as np

from toqb import task_loop as TL


class Unsupported(Exception):
    pass


def cdll():
    """PSF-Zero's built rust/psfbind ($PSF_BIND_LIB, or under $PSF_ZERO_REPO)."""
    path = os.environ.get("PSF_BIND_LIB")
    if not path:
        repo = os.environ.get("PSF_ZERO_REPO", "")
        rel = os.path.join(repo, "rust", "psfbind", "target", "release")
        # the shared library only: cargo also writes libpsfbind.d and libpsfbind.rlib next to it
        hits = [h for ext in ("so", "dylib") for h in glob.glob(os.path.join(rel, "libpsfbind." + ext))]
        hits += glob.glob(os.path.join(rel, "psfbind.dll"))
        if not hits:
            raise Unsupported("libpsfbind not found: build rust/psfbind (cargo build --release) or set PSF_BIND_LIB")
        path = hits[0]
    return ctypes.CDLL(path)


def _lib():
    lib = cdll()
    f = lib.psfbind_angles
    f.restype = ctypes.c_int
    P = np.ctypeslib.ndpointer
    f.argtypes = [ctypes.c_size_t, P(np.uintp, flags="C"), P(np.uint8, flags="C"), P(np.uintp, flags="C"),
                  P(np.float64, flags="C"), ctypes.c_int, ctypes.c_size_t, ctypes.c_size_t,
                  P(np.float64, flags="C"), P(np.float64, flags="C")]
    return f


_KIND = {"rz": 1, "ry": 2, "rx": 3}


class FastPSF:
    """The fast path for one Runner (`toqb.s2r2.Runner`) whose arm is a PSF template arm, for its task's model."""

    def __init__(self, R):
        self.R = R
        t = R.task
        self.n, self.L, self.enc = t["n"], t["layers"], t["enc"]
        d = TL.n_params(self.n, self.L)
        # one compile on the slow path builds the template and the skeletons
        th0, x0 = np.zeros(d), np.zeros(self.n)
        c0 = R.compile(th0, x0)
        loop_arm = R.arm.arm
        sig = None
        qc0 = TL.model_circuit(TL.angle_list(th0, x0, self.n, self.L, self.enc), self.n, self.L)
        sig = loop_arm.ai._structure_sig(qc0)
        tpl = loop_arm._cache.get(sig)
        if tpl is None or not hasattr(tpl, "var_runs") or not hasattr(tpl, "values_of"):
            raise Unsupported(f"the template is not a RingTemplate ({type(tpl).__name__})")
        self.tpl = tpl
        # gather: the template's values from angle_list's order (probe with distinct numbers)
        m = len(TL.angle_list(th0, x0, self.n, self.L, self.enc))
        probe = TL.model_circuit(list(np.arange(m, dtype=float) + 0.25), self.n, self.L)
        vals = tpl.values_of(probe)
        self.gather = np.array([int(round(v - 0.25)) for v in vals], dtype=np.intp)
        if not np.allclose(np.arange(m, dtype=float)[self.gather] + 0.25, vals):
            raise Unsupported("the template's values are not a gather of angle_list")
        # the runs for Rust
        kinds, idx, fixed, start = [], [], [], [0]
        for factors in tpl.var_runs:
            for f in factors:
                if len(f) == 3:
                    kinds.append(_KIND[f[2]])
                    idx.append(int(f[1]))
                    fixed += [0.0] * 8
                else:
                    kinds.append(0)
                    idx.append(0)
                    fixed += [v for z in f for v in (complex(z).real, complex(z).imag)]
            start.append(len(kinds))
        self.n_runs = len(tpl.var_runs)
        self.start = np.array(start, dtype=np.uintp)
        self.kinds = np.array(kinds, dtype=np.uint8)
        self.idx = np.array(idx, dtype=np.uintp)
        self.fixed = np.array(fixed, dtype=np.float64)
        self.use_rx = int(bool(tpl.use_rx))
        self.n_values = len(tpl.var_kinds)
        self._f = _lib()
        # the skeletons and the affine maps params -> slot angles (probe the slow path's own binding)
        self.maps = {}
        n_par = 3 * self.n_runs
        for model in ("sim", "dev"):
            key, sk = R._skel(model, c0)
            b = sk.angles(tpl.circuit.assign_parameters(np.zeros(n_par)))
            M = np.empty((len(b), n_par))
            for j in range(n_par):
                e = np.zeros(n_par)
                e[j] = 1.0
                M[:, j] = sk.angles(tpl.circuit.assign_parameters(e)) - b
            self.maps[model] = (key, sk, M, b)

    def params(self, thetas, xs):
        """The template's parameters (RingTemplate.angles) for points (theta_i, x_i), computed in Rust."""
        V = np.array([np.asarray(TL.angle_list(th, x, self.n, self.L, self.enc), float)[self.gather]
                      for th, x in zip(thetas, xs)], dtype=np.float64)
        V = np.ascontiguousarray(V)
        out = np.empty((len(V), 3 * self.n_runs), dtype=np.float64)
        rc = self._f(self.n_runs, self.start, self.kinds, self.idx, self.fixed, self.use_rx, len(V), self.n_values,
                     V, out)
        if rc != 0:
            raise Unsupported(f"psfbind_angles returned {rc}")
        return out

    def slots(self, model, thetas, xs):
        key, sk, M, b = self.maps[model]
        return self.params(thetas, xs) @ M.T + b

    def z(self, model, thetas, xs, T, seed, shots=False, crn=False):
        """As Runner.z for the circuits of these points (one structure: the group seed is `seed`)."""
        key, sk, M, b = self.maps[model]
        A = self.slots(model, thetas, xs)
        if shots:
            return self.R.eng.z_shots(sk, A, T, seed)
        return self.R.eng.z_mean(sk, A, T, seed, crn=crn)

    def check(self, model, thetas, xs):
        """Largest difference (mod 2 pi) between this path's slot angles and the slow path's, over the points."""
        key, sk, _, _ = self.maps[model]
        fast = self.slots(model, thetas, xs)
        slow = np.array([sk.angles(self.R.compile(th, x)) for th, x in zip(thetas, xs)])
        d = np.abs(np.angle(np.exp(1j * (fast - slow))))
        return float(d.max())
