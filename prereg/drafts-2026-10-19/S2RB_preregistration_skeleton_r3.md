# S2R2-B: pre-registration skeleton (r3) — GPU simulator learning with stand-in records vs SPSA2 on the stand-in

**Closed at the pilot (owner decision, 2026-10-19).**

- B is closed as the "GPU learning vs SPSA2" comparison at its pod pilot (§8).
- No scored run is planned, and this document will not be fixed.
- S2R continues as design C (`C_preregistration_skeleton_r2.md`).
- The pilot values in §8 are tuning-seed results. They are not a test of H1 or H2.

**Revision r3 (2026-10-19, 06:16 CEST).** §8 is filled with the pod pilot's results. The r2 file is unchanged.

**Status as written for r2: skeleton, not fixed.** Values marked `[ ]` wait for the pod pilot (tuning seeds 101 and 102). The document
is fixed by SHA-256 and the CEST time before any scored run. Written at the workplace on 2026-10-19 (design text
only; nothing was run). The design is the owner's decision B (final); this document does not change it.

**Revision r2 (2026-10-19).**

- Filled §8 with the H100 pilot's gradient agreement.
- §2 now gives two wordings of the stand-in's contribution, (a) and (b), with a choice field for the owner.
- The r1 file is unchanged; corrections to r1 are in the drafts folder's README.

## 1. What is compared

**Arm S2R2-B** (`toqb.s2r2 s2rg`):

- **Simulator gradient step:** every loop, the simulator's gradient is estimated from 8 pairs of ± directions × 4
  points × T = 32 trajectories, with common random numbers. The update is m ← m − lr · g.
- **Stand-in:** it measures the new m on 2 points × 100 shots. **These are recorded only; they are not used for
  learning.**
- **Billing:** 2 stand-in circuits per loop, **$0.2016** per loop (2 × (0.036 + 100 × 0.00027) s × $1.60/s).

**Arm SPSA2** (stand-in only): one iteration is 2 stand-in circuits (the ± perturbation), with the same budget, so the
same number of billed circuits as S2R2-B.

**Cells:** compiler {PSF, Qiskit} × L {8, 16}; n = 10; device Target FakeFez. The stand-in is stage 0's (`t12` 0.3,
`over` 0.01, `zz_hz` 10 kHz, seed 20261017).

**Primary metric:** the AUC of cross-entropy over the whole budget (CE on the stand-in, evaluated every `[ ]` loops on
`[ ]` test points, 500-1,000), integrated over billed budget. Seeds: `[ ]` (100-200). Significance level
**p < 0.01** (the owner's policy).

## 2. What is already known, and what it means (recorded before the run)

**Finding of 2026-10-18,** confirmed and extended by the H100 pilot of 2026-10-19 (§8).

- The simulator knows the direction of the stand-in's gradient almost exactly for PSF: cos 1.00 / 1.00 at L = 8 and
  0.97 / 0.99 at L = 16 (student means 5 / 6).
- For Qiskit it knows it less well: 0.80 / 0.85 at L = 8, 0.87 / 0.97 at L = 16.
- Measured with `toqb.gradcos`: 24 directions, 8 points, T = 256, split-half corrected. These are two means per cell,
  so each value is uncertain: with 24 directions, a true 0.9 reads anywhere in about 0.81-0.96 (90 %), and the
  spread is narrower near 1.

**Consequence (recorded as part of this pre-registration).**

- In S2R2-B the stand-in's measurements are not used for learning at all.
- So any difference between S2R2-B and SPSA2 is the effect of the GPU simulator, and not of information from the
  stand-in.

**How the stand-in's contribution is worded (owner's choice):**

| option | wording | owner's choice |
|---|---|---|
| (a) | "The stand-in's contribution is approximately zero" — one statement for all cells. | `[ ]` |
| (b) | Two statements. **PSF:** cos ≈ 1, so the stand-in's contribution is approximately zero. **Qiskit:** cos ≈ 0.85-0.9, so the stand-in's measurements could in principle correct the simulator's gradient; design B does not use them for learning, so that room is not used. | `[ ]` |

- (b) is closer to the measurements.
- (a) is simpler, but it hides the compiler difference that the agreement shows. That difference is the subject of the
  separate TF proposal.
- The result can show that a simulator-driven loop, billed only for 2 stand-in circuits per loop, reaches a lower CE
  per dollar than learning on the stand-in alone. It cannot show that information flows from the device through the
  GPU.
- The stand-in is not shifted on purpose to manufacture a stand-in contribution. That would fit the conditions to the
  result.

**Vanity and essential figures** (both reported, side by side):

| | figure |
|---|---|
| Vanity | "S2R2-B learns about `[ ]` × faster than SPSA2 per dollar" |
| Essential | the learning is done by the GPU simulator; the stand-in's information is not used (and for PSF would add about nothing, cos ≈ 1); on real hardware the simulator's model is likely less accurate, so the gap may well be smaller there; untested |

## 3. Hypotheses (the owner chooses the primary)

| # | hypothesis | test | owner's choice |
|---|---|---|---|
| H1 | AUC(S2R2-B) < AUC(SPSA2), for each compiler and each depth | paired by seed; one-sided `[ ]` (Wilcoxon signed-rank or paired t on per-seed AUC differences); α = 0.01; Holm over the 4 cells | primary / secondary / not tested: `[ ]` |
| H2 | AUC(S2R2-B, PSF) ≠ AUC(S2R2-B, Qiskit), at each depth | paired by seed (same seed, same student initialisation); two-sided `[ ]`; α = 0.01; Holm over the 2 depths | primary / secondary / not tested: `[ ]` |

- **Primary hypothesis:** `[ ]` (owner).
- **Multiple testing:** secondary hypotheses are adjusted by Holm at α = 0.01.
- **Effect sizes:** reported with 99 % confidence intervals.
- **Note on H2:** with cos near 0.99 for both compilers, an H2 difference would come from the simulated circuits
  themselves (PSF's narrower and shorter circuits make the simulator's model of the stand-in more or less accurate, or
  the noise floor different). That holds if Qiskit's cos is also near 0.99; if not, it is part of the difference and is
  reported (`[ ]`).

## 4. Settings waiting for the pilot

| setting | value | source |
|---|---|---|
| S2R2-B learning rate lr | `[ ]` (pilot grid {0.05, 0.1, 0.2}) | pilot, seeds 101-102 |
| SPSA2 gain a (c = 0.2, A = 10) | `[ ]` (pilot grid {0.2, 0.5, 1.0}) | pilot |
| budget per run (= number of loops) | `[ ]` $ (`[ ]` loops; several thousand intended) | pilot and §5 of the time estimate |
| test points | `[ ]` (500-1,000) | owner |
| test trajectories (`test_traj`) | `[ ]` | pilot |
| evaluation interval | every `[ ]` loops | pilot |
| seeds | `[ ]` (100-200 seeds; 9001-9020 and 101-102 are used and excluded) | owner |
| student initialisation | `init` = 1.0 (as the pilot), `[ ]` | pilot |

**Tuning rule:** lr and a are chosen from the pilot's grid on seeds 101-102 only, by the pilot's AUC, before this
document is fixed. Their choice is recorded with all pilot values.

## 5. Procedure and integrity

- **Pairing:** each scored seed runs all 8 runs (2 arms × 2 compilers × 2 depths) with the same teacher, data split and
  student initial mean.
- **Interruptions:** a run that fails is restarted from its start with the same seed. The first completed record per
  seed is the one scored (stage 0's rule).
- **No change** to arms, settings, metric, test or seeds after the first scored run.
- **Recorded per run:**
  - the CE curve against billed dollars;
  - the stand-in's recorded measurements (S2R2-B), not used for learning;
  - wall time per loop, split into compile, simulate and stand-in;
  - the agreement cos where measured.

## 6. What the result cannot show

- Any contribution of real-device or stand-in information to learning (see §2).
- Behaviour on real hardware (decision A is pending).
- Behaviour at other widths, depths, noise models or budgets.

## 7. Decision rule

- **H1 or H2 primary:** confirmed if p < 0.01 in the stated direction (Holm where several cells form the primary).
  Otherwise not confirmed. A difference in the opposite direction is reported as such.
- The AUC difference and its 99 % CI are reported for every cell, whatever the test result.

## 8. Values from the pilot (filled in r3; pod pilot of 2026-10-19)

### Setup

- **Run:** 02:30-05:49 CEST, one H100, 6 runs at a time (PAR = 6), tuning seeds 101 and 102.
- **Versions:** psf_compile 2026-10-18.1 (prototype c68), core 2026-09-29.1, toqb `c9ee8f8` at the start.
- **Grid:** the 3 settings were paired as (lr, a) = (0.05, 0.2), (0.1, 0.5) and (0.2, 1.0). S2R2-B uses lr; SPSA2
  uses a (c = 0.2, A = 10).
- **Budget:** about $100 per run ($99.85-99.90 spent). That is 488 / 476 / 482 / 459 loops or iterations (PSF L 8 /
  Qiskit L 8 / PSF L 16 / Qiskit L 16).
- **Metric:** AUC of CE over the budget; lower is better.
- **check_traj2 on the GPU:** PASS (largest deviation 1.36 se).

### Gradient agreement and size (unchanged from r2, plus sd_dev from the same runs)

| item | PSF L 8 | Qiskit L 8 | PSF L 16 | Qiskit L 16 |
|---|---|---|---|---|
| cos (simulator vs stand-in), student means 5 / 6 (24 directions, 8 points, T = 256) | 1.00 / 1.00 | 0.80 / 0.85 | 0.97 / 0.99 | 0.87 / 0.97 |
| sd_sim, means 5 / 6 (b = 8) | 0.0139 / 0.0306 | 0.0134 / 0.0267 | 0.0055 / 0.0097 | 0.0046 / 0.0070 |
| sd_dev, means 5 / 6 (b = 8) | 0.0110 / 0.0236 | 0.0066 / 0.0090 | 0.0041 / 0.0077 | 0.0037 / 0.0057 |
| sd_dev / sd_sim | 0.79 / 0.77 | 0.50 / 0.34 | 0.74 / 0.80 | 0.81 / 0.82 |

### Pilot AUC by setting

| cell | seed | S2R2-B lr 0.05 | lr 0.1 | lr 0.2 | SPSA2 a 0.2 | a 0.5 | a 1.0 |
|---|---|---|---|---|---|---|---|
| PSF L 8 | 101 | 0.6318 | 0.6039 | **0.5791** | 0.6620 | **0.6339** | 0.6432 |
| PSF L 8 | 102 | 0.5943 | 0.5733 | **0.5619** | 0.6266 | **0.6252** | 0.6384 |
| Qiskit L 8 | 101 | 0.6455 | 0.6281 | **0.6128** | 0.6607 | 0.6378 | **0.6378** |
| Qiskit L 8 | 102 | 0.6174 | 0.6049 | **0.5980** | 0.6356 | 0.6358 | **0.6351** |
| PSF L 16 | 101 | 0.6685 | 0.6582 | **0.6377** | 0.6748 | **0.6735** | 0.6805 |
| PSF L 16 | 102 | 0.6576 | 0.6465 | **0.6267** | **0.6703** | 0.6783 | 0.6864 |
| Qiskit L 16 | 101 | 0.6724 | 0.6649 | **0.6474** | 0.6763 | **0.6757** | 0.6832 |
| Qiskit L 16 | 102 | 0.6608 | 0.6533 | **0.6397** | **0.6682** | 0.6730 | 0.6812 |

- Bold marks the best setting of each arm.
- Qiskit L 8, seed 101: a 0.5 and a 1.0 differ only in the fifth decimal (0.63783 against 0.63777).

### The 8 pairs: best S2R2-B against best SPSA2 (difference = SPSA2 − S2R2-B; positive favours S2R2-B)

| cell | seed 101 | seed 102 | CE start → end, S2R2-B best (101 / 102) | CE start → end, SPSA2 best (101 / 102) |
|---|---|---|---|---|
| PSF L 8 | 0.055 | 0.063 | 0.673 → 0.524 / 0.631 → 0.547 | 0.673 → 0.605 / 0.631 → 0.619 |
| Qiskit L 8 | 0.025 | 0.037 | 0.675 → 0.579 / 0.639 → 0.596 | 0.675 → 0.640 / 0.639 → 0.623 |
| PSF L 16 | 0.036 | 0.044 | 0.676 → 0.605 / 0.664 → 0.601 | 0.676 → 0.669 / 0.664 → 0.672 |
| Qiskit L 16 | 0.028 | 0.028 | 0.678 → 0.616 / 0.667 → 0.616 | 0.678 → 0.669 / 0.667 → 0.667 |

- All 8 pairs have the same sign, with differences of 0.025-0.063.
- **Against every SPSA2 setting** (not only the best), S2R2-B at lr 0.2 is lower in all 24 comparisons, by
  0.025-0.083.

### PSF against Qiskit within S2R2-B (H2's direction; not a test)

- PSF's AUC is lower in all 12 comparisons (3 lr × 2 seeds × 2 depths).
- The differences are 0.014-0.036 at L 8 and 0.003-0.013 at L 16.

### Wall time per loop (measured, 6 runs at a time, evaluation included)

| | PSF L 8 | Qiskit L 8 | PSF L 16 | Qiskit L 16 |
|---|---|---|---|---|
| S2R2-B, measured | 1.2 s | 3.8 s | 2.4 s | 7.6 s |
| S2R2-B, r2's estimate from single-process components | 0.69 s | 1.09 s | 1.42 s | 2.14 s |

- The two rows are not like for like: the measurement includes 6-way sharing of the GPU and the evaluations.
- Qiskit / PSF is 3.1-3.2 × measured, against 1.5-1.6 × estimated.

### Cautions (recorded with the values)

- **Tuning seeds, 2 per cell.** These values were used to choose settings. They are not a test, and no p value is
  given.
- **Best lr is at the edge of the grid.** lr 0.2 was best in all 8 pairs, so a larger lr may be better. This is
  untested.
- **SPSA2's best a is not stable.** It moves between 0.2, 0.5 and 1.0 across seeds and cells.
- **SPSA2 hardly learns at L 16 in this budget.** With a = 1.0, CE rises (0.6636 → 0.6900, 0.6757 → 0.6803), and at
  best it falls by about 0.008. The L 16 comparison is against an arm that barely moves.
- **PSF against Qiskit is confounded.** For the same seed, the starting CE differs between compilers (for example
  0.6730 against 0.6747 at L 8, seed 101), and so does the number of loops in the same budget (488 against 476 at
  L 8, 482 against 459 at L 16). The 12/12 direction is not evidence for H2.
- **The learning is done by the GPU simulator** (§2). The stand-in's measurements are not used. CE ends at 0.52-0.62
  for S2R2-B, against ln 2 = 0.693 for chance: a real but modest improvement.

### Vanity and essential figures (pilot)

| | figure |
|---|---|
| Vanity | "GPU learning beats SPSA2 in all 8 (cell, seed) pairs, and lowers CE about twice as much" |
| Essential | 2 tuning seeds, not a test; AUC differences 0.025-0.063; best lr at the grid's edge; SPSA2 barely learns at L 16; final CE 0.52-0.62 against 0.693 for chance; the learning is done by the GPU simulator, and the stand-in's information is not used |
