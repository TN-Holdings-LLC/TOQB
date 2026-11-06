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
