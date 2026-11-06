# Exploratory (owner 2026-11-06 04:32 CET; not declared): what a "3D OS" would cost on heavy-hex

Home started it while the workplace was paused; the workplace continues (handover `職場へ_2026-11-06h`).
Script `os3d_study.py` (coupling graph of ibm_fez 2026-11-05 only; no calibration number), rows `os3d_rows.json`.
Kicked Ising on a cubic lattice (P5 rules in 3D), t = 2, theta 0.8.

| lattice | qubits | edges | ideal CZ | SABRE CZ (layers) | naive formula CZ (layers) | formula check |
|---|---|---|---|---|---|---|
| 2D 3x3 | 9 | 12 | 24 | 70 (41) | 264 (70) | 2e-16 |
| 2D 4x4 | 16 | 24 | 48 | 170 (70) | 816 (128) | 2e-16 |
| 3D 2x2x2 | 8 | 12 | 24 | 78 (49) | 216 (68) | 1e-16 |
| 3D 3x3x2 | 18 | 33 | 66 | 291 (102) | 1050 (144) | 2e-16 |
| 3D 3x3x3 | 27 | 54 | 108 | 570 (164) | 2322 (186) | (not run) |

- Even the search (SABRE, level 3) needs 3-5 times the ideal CZ count for 3D (square 2D: about 3 times): heavy-hex
  has degree 3 and no 4-cycles, so a cube or a square cell never sits on it without SWAPs.
- The naive formula (odd-even transposition network on a chain, all pairs) is correct (noiseless check to 1e-16)
  but costs 3-4 times SABRE in CZ; in CZ layers it is closer (1.1-1.8 times) because the network is parallel.
- With the measured decay per CZ layer (0.001-0.005), 160-190 layers keep roughly 0.4-0.85 of the signal at t = 2:
  readable only very shallow.
- Not yet: a formula embedding that uses the structure (a brick-wall sublattice of heavy-hex for each layer and a
  fixed SWAP pattern for the missing bonds and the layer couplings), which could approach SABRE without search.

## Structured formula embedding, first version (`rowpass.py`, home, 2026-11-06 ~05:00 CET)

Grid rows on heavy-hex rows (horizontal bonds native); vertical bonds through the bridge qubit
(SWAP, RZZ, SWAP = 7 CZ) while every row runs the same odd-even transposition rounds, ending on a full reversal or
the identity. Fixed rules, no search. t = 2, theta 0.8; noiseless check against the lattice's own statevector.

| lattice | ideal CZ | SABRE CZ (layers) | rowpass CZ (layers) | naive formula CZ (layers) | rowpass check |
|---|---|---|---|---|---|
| 2D 3x3 | 24 | 70 (41) | 228 (76) | 264 (70) | 3e-16 |
| 2D 4x3 | 34 | - | 380 (120) | - | 1e-16 |
| 2D 4x4 | 48 | 170 (70) | 528 (120) | 816 (128) | 2e-16 |

- Correct, better than the naive network in CZ (0.65-0.86 of it), but still about 3 times SABRE in CZ and 1.7 times in
  layers: with one bridge column per row pair inside a 4-column window, every column must travel to it, and the
  row swaps dominate.
- A 3D lattice adds z-bonds between grid rows M apart (several bridge hops each), so the gap to SABRE can only grow.
- Next, if continued: block-local rounds (one bridge per 4 columns, wider lattices) to see whether the cost per site
  stops growing with L. Home's view: on IBM's planar heavy-hex a 3D OS does not pay; keep it for devices with richer
  connectivity.

## Block-local variant (`blockpass.py`): constant depth per step

Rounds inside each block of 4 columns (every block holds a bridge column for both kinds of row pair); a step ends
on the identity (multiple of 8 rounds). Noiseless check: 8x2 and 4x3 within 3e-16. t = 2, theta 0.8.

| lattice | ideal CZ | SABRE CZ (layers) | blockpass CZ (layers) | CZ ratio |
|---|---|---|---|---|
| 2D 4x3 | 34 | 101 (42) | 380 (120) | 3.76 |
| 2D 8x3 | 74 | 268 (96) | 772 (128) | 2.88 |
| 2D 12x3 | 114 | 476 (131) | 1164 (136) | 2.45 |
| 2D 16x3 | 154 | 723 (226) | 1556 (144) | 2.15 |
| 2D 8x4 | 104 | 504 (164) | 1072 (128) | 2.13 |

- The formula keeps the CZ layers per step constant (about 64) as the lattice widens; SABRE's layers grow
  (96 -> 226 from 8x3 to 16x3). From 12x3 on the formula is as shallow or shallower than SABRE (16x3: 144 against
  226 layers; 8x4: 128 against 164), while using about twice as many CZ.
- Since the measured loss is per CZ layer (the daily record's decay), depth may matter more than the CZ count; which
  one wins on a device is not known from this (CZ count also adds error). A device A/B would decide.
- For a true 3D lattice the z-bonds still cost several bridge hops; not built.

## Prototype `grid3d.py`: the whole 3D pipeline (home, 2026-11-06 ~05:40 CET)

Every lattice row (y, z) on one heavy-hex row; x-bonds native; bonds between adjacent heavy-hex rows through the
bridge in block-local passes; lattice rows that must bond but are apart are brought together by an odd-even sort
of the rows' contents (exchange passes through the bridges). Fixed rules, no search. t = 2, theta 0.8.

| lattice | ideal CZ | SABRE CZ (layers) | grid3d CZ (layers) | passes | check |
|---|---|---|---|---|---|
| 4x2x1 | 20 | 55 (32) | 232 (106) | 2 | 3e-16 |
| 4x2x2 | 56 | 248 (109) | 1672 (398) | 8 | 2e-16 |
| 4x3x2 | 92 | 477 (153) | 4264 (690) | 14 | (too large) |
| 8x2x2 | 120 | 568 (190) | 3360 (408) | 8 | (too large) |
| 4x2x3 | 92 | 451 (130) | 4192 (717) | 14 | (too large) |

- The pipeline works end to end and is correct where it can be checked (4x2x2, 19 qubits: 2e-16).
- It is not competitive: 6-9 times SABRE's CZ and 3.6-5.5 times its layers. Every pass moves every row (to keep one
  column order for the native x-bonds), and every exchange of two rows costs 9 CZ per site.
- Possible savings (not built): per-row column orders (only the rows of a job move), fusing an exchange with the
  bond that follows it, an interleave that needs fewer exchanges. Even halving the cost leaves it 3-4 times SABRE.
- Home's conclusion: a 3D OS on IBM's planar heavy-hex does not pay with fixed rules; the 2D block-local embedding
  (`blockpass.py`) is the one result worth a device test.
