# 3D prototype in a simulator: defects found and fixed (2026-11-06 05:30 CET; home; not declared, not a device result)

## Defects of v1 (psf-os 521ac5b) and the fixes (psf-os grid3d v2/v3)

| Defect in v1 | Fix |
|---|---|
| RZZ(-pi/2) compiled as 2 CZ (grid3d skipped `rzz_exact`) | `rzz_exact` in build (as user2d) |
| bridge bond SWAP-RZZ-SWAP = 7 CZ | bridges are \|0> between uses: CX-RZZ-CX = 3 CZ; exchange 9 -> 7 |
| every pass returned to the identity (12 swaps per block and row) | 6-swap pass ending reversed (v2 "rows") |
| the 2x2 (y,z) ring on 4 heavy-hex rows in a line forced exchange passes | folded layout for L = 4 (v3 "fold"): rows y, blocks z, odd blocks mirrored; z-bonds native across the block boundary; one fixed schedule per step |
| refused on any failed element | first translation (row offset, column offset step 4) in a fixed order that avoids failed elements |
| mirror recompiled at level 1 lost 2 CZ in the reversed half | mirror built from the compiled U (translation-only pass) |

## Compile only (fez 2026-11-05 record; `cost3d.py`, `cost_fez_2026-11-05.json`): CZ (CZ layers)

| size, t | v1 | v2 rows | v3 fold | SABRE best of 5 seeds |
|---|---|---|---|---|
| 4x2x2, 1 | 584 (158) | 328 (83) | **116 (33)** | 127 (59) |
| 4x2x2, 2 | 1168 (316) | 656 (165) | **232 (64)** | 269 (107) |
| 4x3x2, 1 | 944 (158) | 504 (83) | **246 (40)** | 247 (111) |
| 4x2x3, 2 | 3544 (750) | 2256 (401) | **476 (68)** | 539 (185) |
| 4x3x3, 2 | refused | refused | **762 (77)** | 918 (239) |
| 4x6x2, 2 | refused | refused | **1056 (86)** | 1355 (249) |
| 4x3x4, 2 | refused | refused | **1032 (80)** | 1492 (319) |
| 8x2x2, 2 | 2352 (324) | 1324 (169) | (L = 4 only) | **678 (193)** |

L = 4: v3 fewer CZ than the best SABRE seed at every size (0 to 31 %) and 2 to 4 times fewer CZ layers.
L = 8: v2 is still about 2 times SABRE (open).

## Correctness

- no noise, statevector, <= 24 sites: placed = exact to 4e-16 (fold and rows).
- theta = pi/2, stabilizer: every stabilizer of the lattice state holds on the placed sites and every bridge is back
  in |0>, all sizes above up to 48 sites, t = 1..3.

## Noise (`sim3d.py`; uniform model p2 = 0.005 per CZ, p1 = 0.0002, readout 0.015; mean of 400 trajectories of
exact <Z>; `uniform_4x2x2_t1.log`)

| 4x2x2 t1 (M_exact 0.697) | CZ | retention | MSE | READS | AGREES (0.05) |
|---|---|---|---|---|---|
| v1 | 584 | 0.68 | 0.050 | yes | no |
| v2 rows | 328 | 0.72 | 0.038 | yes | no |
| v3 fold | 116 | **0.90** | **0.005** | yes | no |
| SABRE | 136 | 0.89 | 0.007 | yes | no |

t = 2, 3 and the FakeFez model were not run yet (2 CPUs here).
