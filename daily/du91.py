"""Task X (home, 2026-11-06; DRAFT, not declared): IBM's dual-unitary kicked Ising experiment (arXiv 2411.00765) at
its widths, N = 51, 71, 91, as a user would write it, placed by psf-os by translation only.

Chains on Heron r2 labels. A Heron r2 lattice is 8 rows of 16 qubits (20 r + c) joined by bridges 20 r + 16 + k at
column 3 + 4k (r even) or 1 + 4k (r odd). A snake runs along a row, crosses a bridge, runs back along the next row,
and so on. A shape is (first row parity, turn column on even gaps, turn column on odd gaps, where the first row
starts); its chain of N sites is the first N labels of the snake. The shapes are tried in the fixed order SHAPES, and
for each shape lattice2d.place tries its translation copies in lattice2d's fixed order; the first copy of the first
shape that qualifies is used (no search: the list and its order are fixed before any device record is read).

Circuits: gpu/practice_circuits.p4 (SI Eq. S5) with J = b = pi/4 on the chain's labels; h in H_VALUES, t in T_STEPS.
Answers at the dual-unitary point: <X_t> = cos(2h)^t on the light-cone site t, 0 elsewhere, for t <= (N - 1) / 2
(psf_os.dual.exact).
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gpu"))
import practice_circuits as PC  # noqa: E402

PI4 = np.pi / 4
WIDTHS = (51, 71, 91)
H_VALUES = (0.0, 0.05, 0.1, 0.15)
T_STEPS = (4, 8, 12, 16, 20, 24)

# (name, first row r0 (0 or 1), even-gap turn column, odd-gap turn column, start column of the first row)
SHAPES = [
    ("S1", 0, 15, 1, 0),    # rows 0.., full width: 16 + 16 per row after (15 cols + bridge)
    ("S2", 1, 15, 1, 0),    # the same pattern starting on an odd row (gaps' parity swapped)
    ("S3", 0, 11, 1, 1),    # narrower: columns 1-11 (copies at dcol 0 and 4: columns 5-15)
    ("S4", 0, 3, 13, 15),   # columns 3-13, the first row from column 15
]


def bridge(r, col):
    """Label of the bridge between row r and r + 1 at column col (None if there is none)."""
    k = (col - 3) // 4 if r % 2 == 0 else (col - 1) // 4
    ok = (col - 3) % 4 == 0 if r % 2 == 0 else (col - 1) % 4 == 0
    return 20 * r + 16 + k if ok and 0 <= k <= 3 else None


def snake(n, shape, rows=8):
    """The first n labels of a shape's snake (raises if it does not fit in the lattice)."""
    _, r0, e_turn, o_turn, start = shape if len(shape) == 5 else (None, *shape)
    out = []
    r, col = r0, start
    while True:
        turn = e_turn if r % 2 == 0 else o_turn
        step = 1 if turn >= col else -1
        for c in range(col, turn + step, step):
            out.append(20 * r + c)
            if len(out) == n:
                return out
        if r + 1 >= rows:
            raise ValueError(f"shape {shape} holds only {len(out)} sites")
        b = bridge(r, turn)
        if b is None:
            raise ValueError(f"no bridge at row {r}, column {turn}")
        out.append(b)
        if len(out) == n:
            return out
        r += 1
        nxt = o_turn if r % 2 else e_turn  # the next row runs from the bridge's column to its own turn column
        col = turn
        if nxt == turn:
            raise ValueError("a row would have no length")


def edges(chain):
    return [tuple(sorted(e)) for e in zip(chain, chain[1:])]


def place(dev, n, shapes=SHAPES):
    """(shape name, drow, dcol, mapping, passed over) of the first shape (in order) with a qualifying copy, or None and
    the reasons. Uses psf_os.lattice2d only."""
    from psf_os import lattice2d as L
    reasons = []
    for sh in shapes:
        try:
            ch = snake(n, sh)
        except ValueError as e:
            reasons.append(dict(shape=sh[0], why=str(e)))
            continue
        try:
            dr, dc, m, passed = L.place(dev, edges(ch), ch)
            return dict(shape=sh[0], drow=dr, dcol=dc, chain=[m[q] for q in ch], passed_over=reasons + [
                dict(shape=sh[0], copies_passed=passed)])
        except RuntimeError as e:
            reasons.append(dict(shape=sh[0], why=str(e)[:300]))
    return dict(shape=None, passed_over=reasons)


def circuit(n, h, t, shape=SHAPES[0]):
    """The user's circuit (practice_circuits.p4 on the shape's chain), J = b = pi/4."""
    return PC.p4(t, PI4, chain=snake(n, shape), h=h)


def exact(n, t, h):
    from psf_os import dual
    return dual.exact(n, t, h)


def cz_count(n, t):
    """CZs after psf-os's rzz_exact: (n - 1) / 2 Bell CX + 2 per gate x (n - 1) / 2 gates per layer x t."""
    return (n - 1) // 2 + 2 * ((n - 1) // 2) * t
