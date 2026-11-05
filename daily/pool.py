"""The daily problem pool of 2026-11-05 (task T): D01-D32 in a fixed order and the two candidates for the fixed problem
(FX-A, FX-B), as data; the patches; and each problem's circuit, written as a user would, in plain Qiskit on Heron r2
labels (no psf-os code), ready for `psf-os run2d`.

Patches (edges: every lattice edge inside the patch, from the Heron r2 construction only, the rule of
notes/s1_2026-11-05/s1_analyse.heron_r2_edges; no calibration data):
  P32  P6's patch (psf_os.ising2d.QUBITS, 35 qubits) without 3, 11, 49: 32 qubits, 32 edges;
  B42  rows 0-2, columns 0-11 and the bridges between them (16, 17, 18, 36, 37, 38): 42 qubits, 45 edges;
  B72  rows 0-4, columns 0-11 and the bridges between them (3 per gap): 72 qubits, 79 edges;
  B102 rows 0-6, columns 0-11 and the bridges between them (3 per gap): 102 qubits, 113 edges (the scale problems);
  C33  P4's chain (gpu/practice_circuits.CHAIN: 0..15, 19, 35..20), N = 33.
Families (|0...0> in, no randomness):
  F1 (P6's form): each step RX(theta_x) then RZ(theta_z = 0.1) on every qubit (ascending), then RZZ(theta_zz) on every
     edge (ascending; the RZZs commute, so the order does not change the answer); Z readout.
  F2 (P5's rule): each step RZZ(-pi/2) on every edge, then RX(theta) on every qubit; Z readout.
  F3 (P4's chain): gpu/practice_circuits.p4(t, b, h=h), J = pi/4; X readout (H, then Z).
CZ layers: the ideal two-qubit depth (RZZ(+-pi/2) is one CZ, any other angle two; one step on the heavy-hex edges is
three layers; one brickwork layer of F3 two). Grades: G1 <= 16 layers, G2 17-28, G3 29-40, G4 > 40.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gpu"))
import practice_circuits as PC  # noqa: E402

PI4 = np.pi / 4
THETA_Z = 0.1
P32 = [4, 5, 6, 7, 8, 9, 10, 16, 17, 18, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 36, 37, 38, 41, 42, 43, 44, 45, 46,
       47, 48]
P6_DROPPED = (3, 11, 49)  # P32 = P6's 35 qubits without these

# (ID, family, patch, parameters, t, CZ layers, grade): the table of the task, in its order
POOL = [
    ("D01", "F3", "C33", dict(h=0.15, b=PI4 - 0.3), 8, 16, "G1"),
    ("D02", "F1", "P32", dict(theta_x=0.53, theta_zz=1.0), 4, 24, "G2"),
    ("D03", "F2", "B72", dict(theta=0.8), 4, 12, "G1"),
    ("D04", "F1", "P32", dict(theta_x=0.8, theta_zz=-np.pi / 2), 6, 18, "G2"),
    ("D05", "F3", "C33", dict(h=0.3, b=PI4 - 0.15), 10, 20, "G2"),
    ("D06", "F1", "P32", dict(theta_x=0.8, theta_zz=1.0), 5, 30, "G3"),
    ("D07", "F2", "B42", dict(theta=0.7), 5, 15, "G1"),
    ("D08", "F2", "P32", dict(theta=1.0), 8, 24, "G2"),
    ("D09", "F1", "P32", dict(theta_x=1.0, theta_zz=0.6), 3, 18, "G2"),
    ("D10", "F3", "C33", dict(h=0.05, b=PI4 - 0.2), 12, 24, "G2"),
    ("D11", "F1", "P32", dict(theta_x=0.53, theta_zz=-np.pi / 2), 12, 36, "G3"),
    ("D12", "F2", "B72", dict(theta=0.4), 6, 18, "G2"),
    ("D13", "F1", "P32", dict(theta_x=0.53, theta_zz=1.0), 2, 12, "G1"),
    ("D14", "F2", "P32", dict(theta=0.8), 10, 30, "G3"),
    ("D15", "F3", "C33", dict(h=0.15, b=PI4 - 0.3), 14, 28, "G2"),
    ("D16", "F1", "P32", dict(theta_x=0.3, theta_zz=1.0), 7, 42, "G4"),
    ("D17", "F2", "B72", dict(theta=0.6), 3, 9, "G1"),
    ("D18", "F1", "P32", dict(theta_x=0.3, theta_zz=1.0), 4, 24, "G2"),
    ("D19", "F2", "B72", dict(theta=0.8), 6, 18, "G2"),
    ("D20", "F3", "C33", dict(h=0.3, b=PI4 - 0.15), 16, 32, "G3"),
    ("D21", "F1", "P32", dict(theta_x=0.53, theta_zz=-np.pi / 2), 4, 12, "G1"),
    ("D22", "F1", "P32", dict(theta_x=0.8, theta_zz=-np.pi / 2), 10, 30, "G3"),
    ("D23", "F2", "B42", dict(theta=0.9), 6, 18, "G2"),
    ("D24", "F1", "P32", dict(theta_x=0.53, theta_zz=1.0), 8, 48, "G4"),
    ("D25", "F2", "B72", dict(theta=1.0), 5, 15, "G1"),
    ("D26", "F1", "P32", dict(theta_x=0.8, theta_zz=1.0), 3, 18, "G2"),
    ("D27", "F3", "C33", dict(h=0.15, b=PI4 - 0.3), 20, 40, "G3"),
    ("D28", "F2", "B72", dict(theta=1.2), 6, 18, "G2"),
    ("D29", "F1", "P32", dict(theta_x=0.53, theta_zz=-np.pi / 2), 8, 24, "G2"),
    ("D30", "F2", "P32", dict(theta=0.6), 14, 42, "G4"),
    ("D31", "F1", "P32", dict(theta_x=0.53, theta_zz=1.0), 6, 36, "G3"),
    ("D32", "F3", "C33", dict(h=0.05, b=PI4 - 0.2), 24, 48, "G4"),
]
# candidates for the fixed problem (counted apart; the owner decides). FX-A's answer was sealed on 2026-11-04
# (results/bank-2026-11-04/pod/du_bank/answers.json) and is only checked against (K4), not made again.
FIXED = [
    ("FX-A", "F3", "C33", dict(h=0.15, b=PI4 - 0.3), 12, 24, "G2"),
    ("FX-B", "F2", "B72", dict(theta=0.8), 5, 15, "G1"),
]
# the scale problems of the addendum (2026-11-05 02:30 CET), counted apart from POOL; answers from the light cones
SCALE = [
    ("S01", "F2", "B102", dict(theta=0.8), 4, 12, "G1"),
    ("S02", "F2", "B102", dict(theta=1.0), 5, 15, "G1"),
    ("S03", "F1", "B102", dict(theta_x=0.53, theta_zz=1.0), 3, 18, "G2"),
    ("S04", "F2", "B102", dict(theta=0.8), 6, 18, "G2"),
    ("S05", "F2", "B102", dict(theta=1.2), 6, 18, "G2"),
    ("S06", "F1", "B102", dict(theta_x=0.53, theta_zz=1.0), 5, 30, "G3"),
]
# the hard problems (owner, 2026-11-06: "at least three, hard, problems whose solution would surprise", for Friday to
# Sunday; counted apart from POOL and SCALE). All three use the Qedma tutorial's angles (theta_x 0.53, theta_z 0.1,
# theta_zz 1.0; F1, two CZ per RZZ) at sizes or depths beyond what was run so far; answers exact (light cones <= 31 qubits
# for B72 / B102 at t 6; the whole 2^32 state for P32 at t 9).
#   H01: 72 qubits, 948 CZ, t 6 (the tutorial's form on twice its patch);
#   H02: 102 qubits, 1356 CZ, t 6 (more CZs than the 151-qubit practice circuit of 11-04, 1328);
#   H03: 32 qubits, t 9: the tutorial's deepest step (54 ideal CZ layers), where raw P6 missed by -0.08 to -0.21 on 11-04.
HARD = [
    ("H01", "F1", "B72", dict(theta_x=0.53, theta_zz=1.0), 6, 36, "G3"),
    ("H02", "F1", "B102", dict(theta_x=0.53, theta_zz=1.0), 6, 36, "G3"),
    ("H03", "F1", "P32", dict(theta_x=0.53, theta_zz=1.0), 9, 54, "G4"),
]
FXA_SEALED = ("results/bank-2026-11-04/pod/du_bank/answers.json", "h0.15_b0.485398")
READOUT = {"F1": "Z", "F2": "Z", "F3": "X"}


def entry(pid):
    for e in POOL + FIXED + SCALE + HARD:
        if e[0] == pid:
            return e
    raise KeyError(pid)


def heron_r2_edges():
    """Coupling graph of a Heron r2 lattice from its construction (8 rows of 16, bridges 20r+16+k at column 3+4k for
    even r, 1+4k for odd r). Geometry only; no calibration data."""
    E = set()
    for r in range(8):
        for c in range(15):
            E.add((20 * r + c, 20 * r + c + 1))
    for r in range(7):
        for k in range(4):
            b = 20 * r + 16 + k
            col = 3 + 4 * k if r % 2 == 0 else 1 + 4 * k
            E.add(tuple(sorted((20 * r + col, b))))
            E.add(tuple(sorted((b, 20 * (r + 1) + col))))
    return E


def _block(rows, cols):
    """Row qubits of rows x cols and every bridge both of whose row neighbours are among them."""
    qs = {20 * r + c for r in rows for c in cols}
    adj = {}
    for a, b in heron_r2_edges():
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    bridges = {q for q in adj if q % 20 >= 16 and adj[q] <= qs}
    return sorted(qs | bridges)


def patch(name):
    """(qubits, edges): qubits ascending (C33: in chain order), edges ascending pairs (C33: consecutive sites)."""
    if name == "C33":
        return list(PC.CHAIN), [tuple(sorted(e)) for e in zip(PC.CHAIN, PC.CHAIN[1:])]
    if name == "P32":
        qs = list(P32)
    elif name == "B42":
        qs = _block(range(3), range(12))
    elif name == "B72":
        qs = _block(range(5), range(12))
    elif name == "B102":
        qs = _block(range(7), range(12))
    else:
        raise KeyError(name)
    s = set(qs)
    return qs, sorted(e for e in heron_r2_edges() if e[0] in s and e[1] in s)


def f1(t, theta_x, theta_zz, qubits, edges, theta_z=THETA_Z):
    from qiskit import QuantumCircuit
    qs, es = sorted(qubits), sorted(tuple(sorted(e)) for e in edges)
    qc = QuantumCircuit(max(qs) + 1, len(qs))
    for _ in range(t):
        for q in qs:
            qc.rx(theta_x, q)
            qc.rz(theta_z, q)
        for a, c in es:
            qc.rzz(theta_zz, a, c)
    for k, q in enumerate(qs):
        qc.measure(q, k)
    return qc


def f2(t, theta, qubits, edges):
    from qiskit import QuantumCircuit
    qs, es = sorted(qubits), sorted(tuple(sorted(e)) for e in edges)
    qc = QuantumCircuit(max(qs) + 1, len(qs))
    for _ in range(t):
        for a, c in es:
            qc.rzz(-np.pi / 2, a, c)
        for q in qs:
            qc.rx(theta, q)
    for k, q in enumerate(qs):
        qc.measure(q, k)
    return qc


def circuit(family, patch_name, params, t, chain=None):
    """The user's circuit with its final measurements. `chain` (F3 only) replaces the chain's labels (the checks use
    shorter chains)."""
    if family == "F3":
        return PC.p4(t, params["b"], chain=list(chain or PC.CHAIN), h=params["h"])
    qs, es = patch(patch_name)
    if family == "F1":
        return f1(t, params["theta_x"], params["theta_zz"], qs, es)
    if family == "F2":
        return f2(t, params["theta"], qs, es)
    raise KeyError(family)


def problem_circuit(pid):
    _, fam, pa, par, t, _, _ = entry(pid)
    return circuit(fam, pa, par, t)


def cz_layers(family, params, t):
    if family == "F1":
        return 3 * t * (1 if abs(abs(params["theta_zz"]) - np.pi / 2) < 1e-12 else 2)
    if family == "F2":
        return 3 * t
    return 2 * t


def cz_ideal(family, patch_name, params, t):
    """CZ count of the ideal circuit (C33: the brickwork's two CZ per gate and the Bell pairs' CX not counted)."""
    if family == "F3":
        raise ValueError("not defined for F3 here")
    return len(patch(patch_name)[1]) * cz_layers(family, params, t) // 3


def grade(layers):
    return "G1" if layers <= 16 else "G2" if layers <= 28 else "G3" if layers <= 40 else "G4"


def params_text(params):
    """The parameters as the table writes them (b as pi/4 - x)."""
    out = []
    for k, v in params.items():
        if k == "b":
            out.append(f"b pi/4-{PI4 - v:.2f}")
        elif abs(abs(v) - np.pi / 2) < 1e-12:
            out.append(f"{k} {'-' if v < 0 else ''}pi/2")
        else:
            out.append(f"{k} {v:g}")
    return ", ".join(out)
