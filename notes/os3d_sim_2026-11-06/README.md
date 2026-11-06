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
one (FakeFez marked, t 3, R 1.27, at the HURTS edge; see the seed check below: the verdict does not move with the trajectory seed). Neither arm AGREES except v3 at t 2 under FakeFez (by 0.004). Every arm
READS and BEATS once dead elements are marked. The unmarked FakeFez run shows the larger point for a device test: one
bad coupler that the record does not mark can decide the comparison, for either arm.

## Trajectory spread of the FakeFez t 3 cell (workplace, 2026-11-06 06:52 CET; home's 06m item 3)

Rule written before the runs (`seeds_t3/run.sh`, 06:32 CET): FakeFez with the snapshot's dead couplers marked,
4x2x2 t 3, v3 and SABRE seed 0, 400 trajectories, Aer seeds 1-5 (`--sim-seed`; 06c used 11); no seed dropped. Only
the trajectory noise changes; the placements, the routing (`seed_transpiler = 0`) and the model are the same.

| Aer seed | MSE v3 | MSE SABRE | R |
|---|---|---|---|
| 1 | 0.00737 | 0.00567 | 1.300 |
| 2 | 0.00735 | 0.00571 | 1.287 |
| 3 | 0.00739 | 0.00570 | 1.297 |
| 4 | 0.00743 | 0.00571 | 1.301 |
| 5 | 0.00739 | 0.00567 | 1.303 |
| 11 (06c) | 0.00731 | 0.00575 | 1.270 |

R 1.270-1.303 (mean 1.293, sd 0.012 over the six): HURTS in every seed. The trajectory noise is about 0.01 in R,
small against the distance to 1.25; the MSE here is mostly the systematic loss per site, not the sampling of
trajectories. So under this model SABRE seed 0 reads t 3 better than v3, and the open question is the model, not the
sampling: the FakeFez snapshot is an older public calibration, and the device on the day will differ. A possible
reason (not tested): v3's worst read qubit has readout error 0.046 in the snapshot (qubit 41), SABRE's 0.023
(`diag_fakefez_t1.log`); a per-site breakdown would show it.

> **Correction, 2026-11-06 (workplace review 06o): BEATS above used the guesses <Z> = +1 / -1 (0.092 / 0.335 / 0.482).
> The declared score (`practice_score.judge`) uses <Z> = 0 / +1: 0.092 / 0.184 / 0.124 at t 1 / 2 / 3. Every BEATS
> verdict in the tables above is the same under both (the largest MSE there, 0.185 at t 1, fails both; 0.146 and
> 0.092 at t 2 / 3 pass both).**

## The price of the third dimension (simulator, owner 13:52 CET; `dim_cost.py`, `dim_cost_uniform.json`)

16 sites, the same step, uniform model, marrakesh record of 11-06. 3D: 4x2x2 (28 edges), v3 fold. 2D: a 16-site
patch of the device's own lattice (16 edges), psf-os run2d.

| t | 3D CZ (layers) | 2D CZ (layers) | 3D retention | 2D retention | 3D MSE / msq | 2D MSE / msq |
|---|---|---|---|---|---|---|
| 1 | 116 (33) | 16 (12) | 0.903 | 0.959 | 0.0048 / 0.485 | 0.0009 / 0.485 |
| 2 | 232 (64) | 32 (24) | 0.879 | 0.940 | 0.0033 / 0.184 | 0.0018 / 0.464 |
| 3 | 348 (95) | 48 (36) | 0.826 | 0.922 | 0.0056 / 0.124 | 0.0023 / 0.340 |

The third dimension costs 4.1 CZ per lattice edge against 1 (7.3 times the CZ for 1.75 times the edges), 2.6-2.8
times the layers, and 6-10 points of retention at t 1-3 in this model. (A first run of this script had the 2D exact
values in the wrong site order; corrected before any number was used.)

## v3.1 and the in-job probe (2026-11-06 evening; psf-os 32e83d6, 711d150; TOQB db0b59c)

- v3.1: every x-bond rides on the swap of its two columns (SWAP . RZZ(-pi/2) = Z Z, H(b), CX(b,a), CX(a,b), H(a), S S;
  2 CX). 4x2x2 t 1-3: CZ 116/232/348 -> 108/216/324, layers 33/64/95 -> 28/55/82; 4x3x2 and 4x2x3 save 5 % CZ and
  9-17 % layers; exact to 2e-15 (statevector) and by stabilizers at 24 sites.
- Probe records from |0> and, new, from |1> (a fast-relaxing qubit reads +1 in the |0> floor and drifts up from -1
  in the |1> floor; test with a planted relaxing qubit).
- `gpu/os3d_v31_build.py`: one job with the probes of 4 candidates, every candidate's arm, the 2D patch and the
  sentinel (57 circuits, 66.6 s on the 11-06 marrakesh record); `gpu/os3d_v31_score.py` judges the probe's choice.

## Replay of the 11-06 faults (run on the home PC by the VS Code Claude, WSL CPU, 15:46-16:15 CET; `replay_home_2026-11-06/`)

Job: the v3.1 job built on the 11-06 marrakesh record (4 candidates with |0> floor, |1> floor and X echo probes;
TOQB 5475828, psf-os 55167cf). Fault model stated in `replay_1106.py` (resembles 11-06, not read from a calibration):
uniform depolarizing everywhere; q29 amplitude damping 0.04 per 1-qubit gate; coupler 48-49 depolarizing 0.05.
Probe rule "best" (owner's "white of white").

| | chosen | candidate 0 (touches q29, q38, q49) | chosen arm MSE t1 / t2 / t3 | candidate 0 MSE t1 / t2 / t3 |
|---|---|---|---|---|
| no faults | 0 | nothing marked | 0.0037 / 0.0020 / 0.0041 (retention 0.92 / 0.91 / 0.86) | (the same arm) |
| faults | **2** | **q29 and q49 marked** (|1> floor max -0.10 at q29, |0> floor min 0.54) | **0.0037 / 0.0020 / 0.0041** (retention 0.92 / 0.91 / 0.86) | 0.0085 / 0.0080 / 0.0138 (retention 0.88 / 0.85 / 0.80) |

The probes marked exactly the two qubits that decided the device run of 11-06 and moved the arm to a candidate that
reads as on a clean device: 2.3 / 4.0 / 3.4 times lower MSE than staying at candidate 0. The 2D patch in the same
job: MSE 0.0007 / 0.0014 / 0.0024. Simulator only; the fault model is ours.
