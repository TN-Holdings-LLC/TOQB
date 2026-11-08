"""Rule A (2026-11-08, VS Claude): merge line operations across step boundaries.

On top of gpu/heis3d.py _line_build (read only, imported). Every line operation is written (L, e, k, s): U(k dt) on
line positions (e, e + 1) of both lines, followed by a swap when s (U -> k 1 s 0, SWAP.U -> k 1 s 1, SWAP -> k 0 s 1).
Rewrite (fixed, no search): when the next operation that touches position e or e + 1 (a line operation on e - 1, e or
e + 1, or a y-bond at a bridge on e or e + 1) is again a line operation on the same e, the two are one:
    (L, e, k1, s1) (L, e, k2, s2) -> (L, e, k1 + k2, s1 xor s2)
Exact: the two act on the same two sites (a swap does not change which two sites sit on e, e + 1), everything in
between acts on other qubits and commutes, U(k1 dt) U(k2 dt) = U((k1 + k2) dt), and SWAP commutes with U. One
two-qubit block, at most 3 CZ, instead of two. (L, e, 0, 0) is the identity and is dropped. The bond log is unchanged
(it keeps every bond), so the exact answer is unchanged. Repeated until nothing changes.
"""
import numpy as np
import heis3d as H


def to_L(out):
    res = []
    for op in out:
        if op[0] == "U":
            res.append(("L", op[1], 1, 0))
        elif op[0] == "SWAP.U":
            res.append(("L", op[1], 1, 1))
        elif op[0] == "SWAP":
            res.append(("L", op[1], 0, 1))
        else:
            res.append(op)
    return res


def touches(op, e):
    """does op touch line position e or e + 1"""
    if op[0] == "L":
        return op[1] in (e - 1, e, e + 1)
    return op[1] in (e, e + 1)          # y / yy at bridge position op[1]


def merge(ops):
    ops = list(ops)
    changed = True
    while changed:
        changed = False
        for i, op in enumerate(ops):
            if op[0] != "L":
                continue
            e = op[1]
            j = next((j for j in range(i + 1, len(ops)) if touches(ops[j], e)), None)
            if j is not None and ops[j][0] == "L" and ops[j][1] == e:
                k, s = op[2] + ops[j][2], op[3] ^ ops[j][3]
                del ops[j]
                if k == 0 and s == 0:
                    del ops[i]
                else:
                    ops[i] = ("L", e, k, s)
                changed = True
                break
    return ops


def circuit(ops, start, A, B, bridge, n_qubits, dt, delta):
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import UnitaryGate
    from psf_os import grid3d as G
    qc = QuantumCircuit(n_qubits)
    for y, line in ((0, A), (1, B)):
        for p in range(8):
            x, z = start[p] % 4, start[p] // 4
            if (x + y + z) % 2 == 1:
                qc.x(line[p])
    for op in ops:
        if op[0] in ("y", "yy"):
            k = 1 if op[0] == "y" else op[2]
            a, b, q = A[op[1]], bridge[op[1]], B[op[1]]
            qc.cx(a, b); qc.cx(b, a)
            qc.append(UnitaryGate(H.bond_unitary(k * dt, delta), label=f"heis_x{k}"), [b, q])
            qc.cx(b, a); qc.cx(a, b)
        else:
            _, e, k, s = op
            for line in (A, B):
                if k == 0:
                    qc.swap(line[e], line[e + 1])
                else:
                    m = H.bond_unitary(k * dt, delta)
                    if s:
                        m = H.SWAP @ m
                    qc.append(UnitaryGate(m, label=f"heis_x{k}" + ("_swap" if s else "")), [line[e], line[e + 1]])
    return qc


def physical_line_merged(dev, t, dt, delta=1.0, avoid=()):
    """As heis3d.physical_line (same placement), with rule A applied."""
    qc0, placed, used, log, where = H.physical_line(dev, t, dt, delta, avoid=avoid)
    r0, c0, br = where["r0"], where["c0"], tuple(where["bridges"])
    adj = {}
    for a, b in dev.couplers:
        adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
    from psf_os import grid3d as G
    bl = {c - c0: b for b, c in G.bridges(adj, r0, 2).get(0, []) if 0 <= c - c0 < 8}
    A = [20 * r0 + c0 + p for p in range(8)]
    B = [20 * (r0 + 1) + c0 + p for p in range(8)]
    out, start, end, log2 = H._line_build(A, B, bl, br, t, dt, delta, merge=True)
    assert log2 == log
    ops = merge(to_L(out))
    qc = circuit(ops, start, A, B, bl, qc0.num_qubits, dt, delta)
    return qc, placed, used, log, dict(where, rule_a=True), ops
