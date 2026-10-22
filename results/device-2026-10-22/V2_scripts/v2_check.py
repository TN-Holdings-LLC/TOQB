"""Workplace V2 (2026-10-22): an independent equality check of the Rust ring template (psfbind ring.rs via
toqb.ringport) against the Python (psf_ai_compile ring_template on psf_compile c61), written at the workplace, not
home's script. Own devices, own fault injection, own seeds. Also the binding (psfbind_angles) against
RingTemplate.angles, bit for bit (sign of zero included).

usage: python v2_check.py AI_FILE OUT_JSON
"""
import copy
import ctypes
import importlib.util
import json
import math
import struct
import sys
import time

import numpy as np

import psf_compile as pc

AI_FILE, OUT = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("ai_under_test", AI_FILE)
ai = importlib.util.module_from_spec(spec)
sys.modules["ai_under_test"] = ai
spec.loader.exec_module(ai)

from toqb import ringport as RP  # noqa: E402
from toqb import rustbind as RB  # noqa: E402
from toqb import task_loop as TL  # noqa: E402
from qiskit_ibm_runtime import fake_provider as fp  # noqa: E402

PY_BUILD = getattr(ai, "model_template", None) or ai.ring_template
DEVICES = ["FakeAachen", "FakeTorino", "FakeFez", "FakeKingston", "FakeMarrakesh"]
LAYERS = [1, 2, 3, 8, 16]
N = 10
CASES_PER_DEVICE = 12   # fault patterns per device (pattern 0: none)
SEED0 = 7700            # workplace seeds (not home's)


def bits(x):
    return struct.pack("<d", float(x))


def inject(target, rng, k):
    """Workplace fault scheme: k = 0 none; else failed qubits (sx and readout error 0.9), failed couplers (cz error 1.0,
    sometimes one direction only), duration changes on a few couplers, and sometimes an sx without a duration."""
    t = copy.deepcopy(target)
    if k == 0:
        return t, {}
    nq = t.num_qubits
    info = {}
    fq = sorted(rng.choice(nq, size=int(rng.integers(0, 5)), replace=False).tolist())
    for q in fq:
        for name in ("sx", "measure"):
            if name in t.operation_names and (q,) in t[name] and t[name][(q,)] is not None:
                t[name][(q,)].error = 0.9
    info["failed_qubits"] = fq
    cz = [qa for qa in t["cz"] if qa is not None]
    pairs = sorted({(min(a), max(a)) for a in cz})
    fc = [pairs[i] for i in rng.choice(len(pairs), size=int(rng.integers(0, 6)), replace=False)]
    for a, b in fc:
        one_dir = rng.random() < 0.3
        for qa in ((a, b),) if one_dir else ((a, b), (b, a)):
            if qa in t["cz"] and t["cz"][qa] is not None:
                t["cz"][qa].error = 1.0 if rng.random() < 0.5 else 0.6
    info["failed_couplers"] = [list(p) for p in fc]
    dc = [pairs[i] for i in rng.choice(len(pairs), size=int(rng.integers(0, 8)), replace=False)]
    for a, b in dc:
        for qa in ((a, b), (b, a)):
            if qa in t["cz"] and t["cz"][qa] is not None and t["cz"][qa].duration is not None:
                t["cz"][qa].duration = t["cz"][qa].duration * (1.5 if rng.random() < 0.5 else 0.75)
    info["duration_changed"] = [list(p) for p in dc]
    if rng.random() < 0.2:
        q = int(rng.integers(0, nq))
        if (q,) in t["sx"] and t["sx"][(q,)] is not None:
            t["sx"][(q,)].duration = None
            info["sx_without_duration"] = q
    return t, info


def model(L, seed):
    rng = np.random.default_rng(seed)
    th = rng.uniform(-np.pi, np.pi, TL.n_params(N, L))
    x = rng.uniform(-1, 1, N)
    return TL.model_circuit(TL.angle_list(th, x, N, L, 1.5707963267948966), N, L)


def strict_fixed(a, b):
    """Fixed angles compared by their bits (catches -0.0 against 0.0, which compare() cannot see)."""
    out = []
    for k, (x, y) in enumerate(zip(a.circuit.data, b.circuit.data)):
        for px, py in zip(x.operation.params, y.operation.params):
            if not getattr(px, "parameters", None) and not getattr(py, "parameters", None):
                if bits(px) != bits(py):
                    out.append((k, x.operation.name, repr(float(px)), repr(float(py))))
    for ra, rb in zip(a.var_runs, b.var_runs):
        for fa, fb in zip(ra, rb):
            if len(fa) == 4:
                for u, v in zip(fa, fb):
                    if bits(complex(u).real) != bits(complex(v).real) or bits(complex(u).imag) != bits(complex(v).imag):
                        out.append(("factor", repr(complex(u)), repr(complex(v))))
    return out


_KIND = {"rz": 1, "ry": 2, "rx": 3}


def rust_angles(tpl, values):
    lib = RB.cdll()
    f = lib.psfbind_angles
    f.restype = ctypes.c_int
    starts, kinds, idx, fixed = [0], [], [], []
    for run in tpl.var_runs:
        for fac in run:
            if len(fac) == 3:
                kinds.append(_KIND[fac[2]])
                idx.append(int(fac[1]))
                fixed += [0.0] * 8
            else:
                kinds.append(0)
                idx.append(0)
                fixed += [v for z in fac for v in (complex(z).real, complex(z).imag)]
        starts.append(len(kinds))
    nr = len(tpl.var_runs)
    S = (ctypes.c_size_t * len(starts))(*starts)
    K = (ctypes.c_uint8 * max(1, len(kinds)))(*kinds)
    I = (ctypes.c_size_t * max(1, len(idx)))(*idx)
    F = (ctypes.c_double * max(1, len(fixed)))(*fixed)
    V = (ctypes.c_double * len(values))(*values)
    O = (ctypes.c_double * (3 * nr))()
    f.argtypes = [ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int,
                  ctypes.c_size_t, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p]
    rc = f(nr, S, K, I, F, int(bool(tpl.use_rx)), 1, len(values), V, O)
    assert rc == 0
    return list(O)


rows = []
summary = dict(cases=0, both_built=0, identical_tol0=0, strict_bit_diffs=0, out_of_scope=0, oos_expected=0,
               refused=0, both_none=0, other=0, binding_points=0, binding_bit_diffs=0, binding_max_abs=0.0)
t0 = time.time()
for di, dname in enumerate(DEVICES):
    base = getattr(fp, dname)().target
    for k in range(CASES_PER_DEVICE):
        rng = np.random.default_rng(SEED0 + 100 * di + k)
        tgt, info = inject(base, rng, k)
        for L in LAYERS:
            qc = model(L, SEED0 + 1000 * di + 10 * k + L)
            summary["cases"] += 1
            row = dict(device=dname, pattern=k, L=L, faults=info)
            # the Python's placement route, for the out-of-scope expectation
            lat = pc._chain_lattice(tgt, 0.5)
            how = None
            if lat is not None:
                K_, kadj, fadj, snake = lat
                line, how = pc._chain_place(N, K_, fadj, snake)
                if line is None:
                    line, how2 = pc._chain_place(N, K_, kadj, snake)
                    how = f"fadj none, kadj {how2}"
            row["python_route"] = how
            try:
                py = PY_BUILD(qc, tgt)
                row["python"] = "built" if py is not None else "none"
            except Exception as exc:  # noqa: BLE001
                py = None
                row["python"] = f"error {type(exc).__name__}: {exc}"
            try:
                rs = RP.ring_template(qc, tgt, ai)
                row["rust"] = "built" if rs is not None else "none"
            except RP.OutOfScope as exc:
                rs = None
                row["rust"] = "out_of_scope"
            except RP.Refused as exc:
                rs = None
                row["rust"] = f"refused: {exc}"
            if row["rust"] == "built" and row["python"] == "built":
                summary["both_built"] += 1
                d = RP.compare(py, rs, tol=0.0)
                row["diffs"] = d
                summary["identical_tol0"] += int(d == [])
                sd = strict_fixed(py, rs)
                row["strict_bit_diffs"] = sd[:5]
                summary["strict_bit_diffs"] += int(bool(sd))
                row["schedule_rust"] = getattr(rs, "rust_schedule", None)
                nvals = len(py.var_kinds)
                vrng = np.random.default_rng(SEED0 + 5 + summary["cases"])
                for _ in range(4):
                    vals = [float(v) for v in vrng.uniform(-np.pi, np.pi, nvals)]
                    if vrng.random() < 0.5:  # exact zeros and pi multiples too
                        for j in vrng.choice(nvals, size=max(1, nvals // 5), replace=False):
                            vals[j] = float(vrng.choice([0.0, -0.0, math.pi, -math.pi, math.pi / 2]))
                    pa = py.angles(vals)
                    ra = rust_angles(py, vals)
                    summary["binding_points"] += 1
                    nb = sum(bits(u) != bits(v) for u, v in zip(pa, ra))
                    summary["binding_bit_diffs"] += int(nb > 0)
                    summary["binding_max_abs"] = max(summary["binding_max_abs"],
                                                     max(abs(u - v) for u, v in zip(pa, ra)))
            elif row["rust"] == "out_of_scope":
                summary["out_of_scope"] += 1
                summary["oos_expected"] += int(how != "snake")
            elif row["rust"].startswith("refused"):
                summary["refused"] += 1
            elif row["rust"] == "none" and row["python"] == "none":
                summary["both_none"] += 1
            else:
                summary["other"] += 1
            rows.append(row)
    print(dname, dict(summary), round(time.time() - t0), "s", flush=True)

json.dump(dict(summary=summary, rows=rows, ai=ai.AI_COMPILE_VERSION, pc=pc.VERSION), open(OUT, "w"), indent=1,
          default=str)
print("SUMMARY", json.dumps(summary))
