"""Sparse Pauli dynamics prototype (Heisenberg picture, coefficient truncation delta) for <Z_q> of P5's lattice circuit.
Validated on 3 November against the exact cone answers: theta 0.8, t = 5: max error 0.017 (delta 1e-3), 0.0033 (1e-4);
t = 8: 0.065 (1e-3), 0.013 (1e-4, 760k terms, 13 s per qubit in Python). Too slow in Python for t = 20."""
import json, math, sys, time
import numpy as np

def make(edges, theta):
    nb = {}
    for a, b in edges:
        nb.setdefault(a, []).append(b); nb.setdefault(b, []).append(a)
    return dict(edges=[tuple(e) for e in edges], c=math.cos(theta), s=math.sin(theta))

def rx_layer(terms, c, s, delta):
    out = {}
    for (x, z), w in terms.items():
        # qubits where the term is Z or Y (z bit set): each splits in two
        zs = z
        branches = [(x, z, w)]
        q = 0
        while zs:
            if zs & 1:
                bit = 1 << q
                nb = []
                for (bx, bz, bw) in branches:
                    if bx & bit:   # Y -> c Y - s Z
                        a1, a2 = (bx, bz, bw * c), (bx ^ bit, bz, -bw * s)
                    else:          # Z -> c Z + s Y
                        a1, a2 = (bx, bz, bw * c), (bx | bit, bz, bw * s)
                    if abs(a1[2]) >= delta: nb.append(a1)
                    if abs(a2[2]) >= delta: nb.append(a2)
                branches = nb
                if not branches: break
            zs >>= 1; q += 1
        for bx, bz, bw in branches:
            k = (bx, bz); out[k] = out.get(k, 0.0) + bw
    return {k: v for k, v in out.items() if abs(v) >= delta}

def zz_layer(terms, edges):
    out = {}
    for (x, z), w in terms.items():
        for a, b in edges:
            xa, xb = (x >> a) & 1, (x >> b) & 1
            if xa ^ xb:
                q = a if xa else b
                w = w if not (z >> q) & 1 else -w   # X -> Y Z (+1), Y -> -X Z (-1)
                z ^= (1 << a) | (1 << b)
        out[(x, z)] = out.get((x, z), 0.0) + w
    return out

def z_expect(q, edges, theta, t, delta, cap=None):
    terms = {(0, 1 << q): 1.0}
    c, s = math.cos(theta), math.sin(theta)
    peak = 1
    for step in range(t, 0, -1):
        terms = rx_layer(terms, c, s, delta)
        if step > 1:
            terms = zz_layer(terms, edges)
        peak = max(peak, len(terms))
        if cap and len(terms) > cap:
            return None, peak
    return sum(w for (x, z), w in terms.items() if x == 0), peak
