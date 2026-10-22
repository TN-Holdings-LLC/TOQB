"""Copied unchanged from the workplace prototype P1 (2026-10-22, ring_zip.py, SHA-256 in its SHA256SUMS.txt) for the
report-only comparison of 2026-10-22 (gpu/zip_compare.sh); not part of any pre-registered run.

Prototype (workplace, 2026-10-22): the "zipper" schedule for a CZ ring classifier folded onto a line -- one more
candidate for psf_ai_compile a22's ring template (item 35), chosen by the same fixed rule (item 84's `_better`:
duration, then two-qubit count). Formula only: a fixed schedule for every even n >= 4, no search, no calibration
beyond what `_better` already reads.

Why. One layer of the ring needs each of its n CZ edges once, with both qubits adjacent on the device's line. N2 and
item 31 bring edges together with plain SWAPs (3 CZ each): item 31 uses 6 SWAPs at n = 10, 28 CZ per layer. A SWAP
done right after a CZ on the same pair is locally an iSWAP and costs 2 CZ in all (the template's block rule already
merges such a pair). The zipper places the ring so that the two end SWAPs coincide with ring edges:

    start (position -> ring index): 0, 1, 2, n-1, n-2, 3, 4, n-3, n-4, 5, ...   (pairs from the two arcs, alternating)

    round A  CZ on positions (1,2), (3,4), ..., (n-3, n-2)                     n/2 - 1 ring edges
    round B  CZ + SWAP on positions (0,1) and (n-2, n-1)                        2 ring edges, 2 CZ each
    round C  SWAP on positions (2,3), (4,5), ..., (n-4, n-3)                    n/2 - 2 SWAPs
    round D  CZ on positions (1,2), (3,4), ..., (n-3, n-2)                     n/2 - 1 ring edges

    CZ per layer: n + 2 + 3 (n/2 - 2) = 5n/2 - 4   (n = 10: 21, against item 31's 28 and N2's 65)

Odd layers run the rounds backwards (as N2), which undoes the permutation; round B is split from round A so that,
backwards, each end SWAP is still followed directly by its CZ (and merged).

Evidence that it is the least (analysis, not used at compile time): an exhaustive search over schedules from every
layout of least total ring length (`bound.py`) gives 6, 11 and 16 CZ per layer for n = 4, 6, 8, which is 5n/2 - 4;
n = 10 was too large for that search in 10 minutes. Starts of larger total length were not searched.
"""
from __future__ import annotations


def ring_rounds_zip(n):
    """(start order: ring index at each line position, rounds [(CZ pairs of ring indices, SWAPs (p, p + 1))])."""
    if n < 4 or n % 2:
        raise RuntimeError("zipper: n must be even and >= 4")
    top = list(range(1, n))          # 1, 2, ...      (one arc from ring index 0)
    bot = list(range(n - 1, 0, -1))  # n-1, n-2, ...  (the other arc)
    order, used, t, b, from_top = [0], {0}, 0, 0, True
    while len(order) < n:
        src = top if from_top else bot
        k = 0
        while k < 2 and len(order) < n:
            i = t if from_top else b
            while src[i] in used:
                i += 1
            order.append(src[i])
            used.add(src[i])
            if from_top:
                t = i + 1
            else:
                b = i + 1
            k += 1
        from_top = not from_top
    occ = list(order)
    edges = {(min(i, (i + 1) % n), max(i, (i + 1) % n)) for i in range(n)}

    def take(p):
        a, b_ = occ[p], occ[p + 1]
        e = (min(a, b_), max(a, b_))
        if e not in edges:
            raise RuntimeError(f"zipper: positions ({p}, {p + 1}) hold {a}, {b_}, not a ring edge")
        edges.discard(e)
        return (a, b_)

    rounds = []
    odd = list(range(1, n - 2, 2))
    rounds.append(([take(p) for p in odd], []))                       # A
    ends = [0, n - 2]
    czb = [take(p) for p in ends]
    rounds.append((czb, [(p, p + 1) for p in ends]))                  # B
    for p in ends:
        occ[p], occ[p + 1] = occ[p + 1], occ[p]
    mid = [(p, p + 1) for p in range(2, n - 3, 2)]
    if mid:
        rounds.append(([], mid))                                      # C
        for p, p1 in mid:
            occ[p], occ[p1] = occ[p1], occ[p]
    rounds.append(([take(p) for p in odd], []))                       # D
    if edges:
        raise RuntimeError(f"zipper: edges left {sorted(edges)}")
    return order, rounds


def ring_template_z(ai, pc, qc, target, basis_gates=None, seed=0):
    """a22's `ring_template` with the zipper as a third candidate: N2, item 31, zipper, in that order; item 84's
    `_better` (an operation not offered or error >= 1 loses, then duration, then two-qubit count; a full tie keeps
    the earlier). Returns (template, label) or (None, None)."""
    best, bc, lab = None, None, None
    for name, fn in (("n2", None), ("q4", ai.ring_rounds_q4), ("zip", ring_rounds_zip)):
        try:
            t = ai._ring_template_one(qc, target, basis_gates, seed, fn)
        except RuntimeError:
            t = None
        if t is None:
            continue
        c = t.bind(qc)
        if best is None or pc._better(c, bc, target):
            best, bc, lab = t, c, name
    return best, lab


def model_template_z(ai, pc, qc, target, basis_gates=None, seed=0, max_error=0.5):
    """a22's `model_template` (item 43) with `ring_template_z` for a ring that does not embed; otherwise a22's."""
    if ai._ring_embeds(qc, target, max_error) or ai._ring_read_path(qc) is None:
        return ai.model_template(qc, target, basis_gates, seed, max_error)
    return ring_template_z(ai, pc, qc, target, basis_gates, seed)[0]
