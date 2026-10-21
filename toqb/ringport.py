"""The PSF ring template built in Rust (2026-10-21): psf_ai_compile a22's `model_template` for a ring classifier that
does not embed in the device -- reading, schedules N2 and item 31, placement on the device's snake, fixed blocks,
runs, and the choice between the schedules -- ported to PSF-Zero's `rust/psfbind` (`ring.rs`, C ABI through ctypes).

    device_json(target)   every entry of the Target (name, qubits, error, duration)
    input_json(qc)        the input circuit (name, qubits, clbits, rotation angle, other single-qubit matrices)
    blocks_json(ai)       the fixed CZ / SWAP blocks as a22 decomposes them (`_block_ops`: Qiskit's
                          TwoQubitBasisDecomposer, checked to 1e-12 there): constants handed to the builder
    build(...)            the Rust answer as a dict: status "built" (with the template), "none" (the Python's None),
                          "refused" (a case not ported, with its reason: the caller builds with the Python) or
                          "out_of_scope" (owner, 2026-10-21: a placement that would need VF2's search; no fallback)
    ring_template(...)    a psf_ai_compile.RingTemplate from the Rust answer (the same class, so binding, the fast path
                          and QPY export are unchanged), None, or raises Refused
    compare(a, b)         the differences between two RingTemplates (gate list, fixed angles, runs, layout, values)

The arm uses it only when asked (`TOQB_RUST_TEMPLATE=1`: Rust, the Python for a refused case; `=check`: Rust, and the
Python's template built beside it must be identical or the run stops). In both, a placement that would need VF2's
search raises OutOfScope (the owner's rule of 2026-10-21, formula only): the device is not used for PSF.
"""
from __future__ import annotations

import ctypes
import itertools
import json

from toqb import rustbind as RB


class Refused(Exception):
    pass


class OutOfScope(Exception):
    """The owner's rule of 2026-10-21 (formula only): no snake piece of the device holds the ring, so a placement
    would need VF2's search. The template is not built and nothing falls back to the Python (which would search)."""


class Mismatch(Exception):
    pass


def _f(x):
    return None if x is None else float(x)


def device_json(target):
    names = sorted(target.operation_names)
    entries = []
    for name in names:
        for qargs, props in target[name].items():
            err = getattr(props, "error", None) if props is not None else None
            dur = getattr(props, "duration", None) if props is not None else None
            entries.append([name, None if qargs is None else [int(q) for q in qargs], _f(err), _f(dur)])
    return {"num_qubits": int(target.num_qubits), "names": names, "entries": entries}


def input_json(qc):
    ops = []
    for ins in qc.data:
        op = ins.operation
        qs = [qc.find_bit(q).index for q in ins.qubits]
        cs = [qc.find_bit(c).index for c in ins.clbits]
        angle = mat = None
        if len(qs) == 1 and op.name not in ("measure", "barrier"):
            parameterised = getattr(op, "is_parameterized", lambda: False)()
            if op.name in ("rz", "ry", "rx"):
                if not parameterised:
                    angle = float(op.params[0])
            elif not parameterised:
                m = op.to_matrix()
                mat = [float(v) for z in (m[0][0], m[0][1], m[1][0], m[1][1]) for v in (complex(z).real,
                                                                                      complex(z).imag)]
        ops.append([op.name, qs, cs, angle, mat])
    return {"num_qubits": qc.num_qubits, "ops": ops}


_BLOCKS = {}


def blocks_json(ai, max_len=4):
    """Every sequence of cz / swap up to `max_len`, decomposed by a22's own `_block_ops` (cached per module)."""
    key = (id(ai), max_len)
    if key not in _BLOCKS:
        out = []
        for m in range(1, max_len + 1):
            for kinds in itertools.product(("cz", "swap"), repeat=m):
                try:
                    seq = ai._block_ops(tuple(kinds))
                except RuntimeError:
                    continue
                ops = []
                for op in seq:
                    if op[0] == "cz":
                        ops.append(["cz"])
                    else:
                        M = op[2]
                        ops.append(["1q", int(op[1]), [float(v) for z in (M[0, 0], M[0, 1], M[1, 0], M[1, 1])
                                                       for v in (complex(z).real, complex(z).imag)]])
                out.append([list(kinds), ops])
        _BLOCKS[key] = out
    return _BLOCKS[key]


_LIB = []


def _lib():
    if not _LIB:
        lib = RB.cdll()
        f = lib.psfbind_ring_template
        f.restype = ctypes.c_void_p
        f.argtypes = [ctypes.c_char_p]
        lib.psfbind_free.argtypes = [ctypes.c_void_p]
        lib.psfbind_free.restype = None
        _LIB.append(lib)
    return _LIB[0]


def build(qc, target, ai, max_error=0.5, schedule=None):
    """The Rust builder's answer (a dict)."""
    req = {"device": device_json(target), "input": input_json(qc), "blocks": blocks_json(ai),
           "max_error": float(max_error)}
    if schedule is not None:
        req["schedule"] = schedule
    lib = _lib()
    p = lib.psfbind_ring_template(json.dumps(req).encode())
    try:
        return json.loads(ctypes.string_at(p).decode())
    finally:
        lib.psfbind_free(p)


def ring_template(qc, target, ai, max_error=0.5, schedule=None):
    """A RingTemplate from Rust (None as the Python's None); Refused for a case not ported; OutOfScope for a placement
    that would need VF2's search (never built, by the owner's rule)."""
    ans = build(qc, target, ai, max_error, schedule)
    if ans["status"] == "out_of_scope":
        raise OutOfScope(ans["reason"])
    if ans["status"] == "refused":
        raise Refused(ans["reason"])
    if ans["status"] == "none":
        return None
    t = ans["template"]
    from qiskit import QuantumCircuit
    from qiskit.circuit import ParameterVector
    N = int(t["num_qubits"])
    pv = ParameterVector("psf_t", 3 * int(t["nvar"]))
    out = QuantumCircuit(N, name=qc.name)
    for cr in qc.cregs:
        out.add_register(cr)
    for name, qs, cs, p in t["ops"]:
        qs = [int(q) for q in qs]
        if name == "cz":
            out.cz(qs[0], qs[1])
        elif name == "measure":
            out.measure(qs[0], int(cs[0]))
        elif name == "sx":
            out.sx(qs[0])
        elif name in ("rz", "rx"):
            getattr(out, name)(pv[int(p["p"])] if isinstance(p, dict) else float(p), qs[0])
        else:
            raise Refused(f"unknown operation {name!r} in the Rust template")
    var_runs = []
    for run in t["var_runs"]:
        factors = []
        for f in run:
            if len(f) == 8:
                factors.append(tuple(complex(f[2 * i], f[2 * i + 1]) for i in range(4)))
            else:
                factors.append(("v", int(f[0]), f[1]))
        var_runs.append(factors)
    var_kinds = [(int(k), nm) for k, nm in t["var_kinds"]]
    tpl = ai.RingTemplate(ai._structure_sig(qc), out, var_runs, list(pv), bool(t["use_rx"]),
                          [int(q) for q in t["layout"]], var_kinds)
    tpl.rust_schedule = t["schedule"]
    tpl.rust_candidates = ans.get("candidates", [])
    return tpl


def compare(a, b, tol=1e-12):
    """Differences between RingTemplates `a` and `b` (empty: identical; fixed angles and fixed factors within `tol`)."""
    diffs = []
    if type(a).__name__ != type(b).__name__:
        return [f"types {type(a).__name__} / {type(b).__name__}"]
    if list(a.layout) != list(b.layout):
        diffs.append(f"layout {a.layout} / {b.layout}")
    if bool(a.use_rx) != bool(b.use_rx):
        diffs.append("use_rx")
    if [tuple(v) for v in a.var_kinds] != [tuple(v) for v in b.var_kinds]:
        diffs.append("var_kinds")
    ca, cb = a.circuit, b.circuit
    if ca.num_qubits != cb.num_qubits or ca.num_clbits != cb.num_clbits:
        diffs.append("circuit sizes")
    if len(ca.data) != len(cb.data):
        diffs.append(f"gate count {len(ca.data)} / {len(cb.data)}")
    worst = 0.0
    for k, (x, y) in enumerate(zip(ca.data, cb.data)):
        qx = [ca.find_bit(q).index for q in x.qubits]
        qy = [cb.find_bit(q).index for q in y.qubits]
        cx = [ca.find_bit(c).index for c in x.clbits]
        cy = [cb.find_bit(c).index for c in y.clbits]
        if x.operation.name != y.operation.name or qx != qy or cx != cy:
            diffs.append(f"gate {k}: {x.operation.name}{qx}{cx} / {y.operation.name}{qy}{cy}")
            continue
        for px, py in zip(x.operation.params, y.operation.params):
            fx = not hasattr(px, "parameters") or not px.parameters
            fy = not hasattr(py, "parameters") or not py.parameters
            if fx != fy:
                diffs.append(f"gate {k}: fixed / parameter")
            elif fx:
                worst = max(worst, abs(float(px) - float(py)))
            elif str(px) != str(py):
                diffs.append(f"gate {k}: {px} / {py}")
    if worst > tol:
        diffs.append(f"fixed angles differ by {worst:.3e}")
    if len(a.var_runs) != len(b.var_runs):
        diffs.append("number of runs")
    fw = 0.0
    for ra, rb in zip(a.var_runs, b.var_runs):
        if len(ra) != len(rb):
            diffs.append("run length")
            continue
        for fa, fb in zip(ra, rb):
            if (len(fa) == 3) != (len(fb) == 3):
                diffs.append("factor kind")
            elif len(fa) == 3:
                if tuple(fa[1:]) != tuple(fb[1:]):
                    diffs.append(f"factor {fa} / {fb}")
            else:
                fw = max(fw, max(abs(complex(u) - complex(v)) for u, v in zip(fa, fb)))
    if fw > tol:
        diffs.append(f"fixed factors differ by {fw:.3e}")
    compare.last = dict(fixed_angles=worst, fixed_factors=fw)
    return diffs


compare.last = {}
