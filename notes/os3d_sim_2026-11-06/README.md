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

## Noise, t = 1-3 and the FakeFez model (workplace, 2026-11-06 06:20 CET; home's 06l item 1; not declared, not a device result)

400 trajectories each; `sim3d.py` with the FakeFez remap fix (`review_06l.md`, finding 1). R = MSE(v3) / MSE(SABRE),
read with the draft's thresholds (HELPS <= 0.8, HURTS >= 1.25). SABRE: seed 0 only. BEATS: MSE below the better of
all 0 / all 1 (0.092, 0.335, 0.482 at t 1, 2, 3). M_exact 0.697, 0.425, 0.321. Idle errors are in neither model.

Uniform model (`uniform_4x2x2_t1_v3sabre.log`, `uniform_4x2x2_t23.log`):

| t | arm | CZ (layers) | retention | MSE | READS | AGREES | BEATS | R |
|---|---|---|---|---|---|---|---|---|
| 1 | v3 fold | 116 (33) | 0.903 | 0.0048 | yes | no (-0.068) | yes | 0.72 HELPS |
| 1 | SABRE | 136 (73) | 0.886 | 0.0067 | yes | no (-0.079) | yes | |
| 2 | v1 | 1168 (316) | 0.526 | 0.0435 | yes | no | yes | |
| 2 | v2 rows | 656 (165) | 0.630 | 0.0269 | yes | no | yes | |
| 2 | v3 fold | 232 (64) | 0.879 | 0.0033 | yes | no (-0.051) | yes | 0.76 HELPS |
| 2 | SABRE | 269 (107) | 0.851 | 0.0044 | yes | no (-0.063) | yes | |
| 3 | v1 | 1752 (474) | 0.375 | 0.0567 | yes | no | yes | |
| 3 | v2 rows | 984 (247) | 0.477 | 0.0406 | yes | no | yes | |
| 3 | v3 fold | 348 (95) | 0.826 | 0.0056 | yes | no (-0.056) | yes | 0.75 HELPS |
| 3 | SABRE | 456 (158) | 0.789 | 0.0075 | yes | no (-0.068) | yes | |

FakeFez model, placement on the 11-05 record as it is (`fakefez_4x2x2_t123_v3sabre.log`):

| t | v3 fold: retention, MSE | SABRE: retention, MSE | R |
|---|---|---|---|
| 1 | 0.909, 0.0043 | 0.577, 0.1852 (BEATS no) | 0.02 |
| 2 | 0.892, 0.0030 (AGREES yes, -0.046) | 0.278, 0.1464 (READS no) | 0.02 |
| 3 | 0.818, 0.0073 | 0.316, 0.0924 (READS no) | 0.08 |

**This SABRE collapse is a model mismatch, not a property of SABRE** (`diag_fakefez.py`, `diag_fakefez_t1.log`):
SABRE's route uses coupler 106-107 twelve times; the FakeFez snapshot (an older public calibration) has CZ error 1.0
there, while the 11-05 record does not mark it failed. v3's worst coupler in the snapshot is 0.010. Rule then fixed
(06:06 CET, before the run): add the snapshot's dead elements (CZ or readout error >= 0.5: 7 couplers, no qubit) to
the record's failed marks for both arms (`--mark-fakefez-dead`):

| t | v3 fold: CZ (layers), retention, MSE | SABRE: CZ (layers), retention, MSE | R |
|---|---|---|---|
| 1 | 116 (33), 0.909, 0.0043 | 139 (56), 0.892, 0.0074 | 0.58 HELPS |
| 2 | 232 (64), 0.892, 0.0030 (AGREES yes) | 269 (109), 0.859, 0.0052 | 0.59 HELPS |
| 3 | 348 (95), 0.818, 0.0073 | 441 (194), 0.842, 0.0058 | 1.27 HURTS |

Reading: v3 reads at least as well as SABRE seed 0 in five of six model-and-depth cells (R 0.58-0.76) and worse in
one (FakeFez marked, t 3, R 1.27, at the HURTS edge; the trajectory noise of MSE at 400 trajectories was not measured, so
this cell may fall either side of 1.25). Neither arm AGREES except v3 at t 2 under FakeFez (by 0.004). Every arm
READS and BEATS once dead elements are marked. The unmarked FakeFez run shows the larger point for a device test: one
bad coupler that the record does not mark can decide the comparison, for either arm.
