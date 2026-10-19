# S2R2-B: pre-registration skeleton (r2) — GPU simulator learning with stand-in records vs SPSA2 on the stand-in

**Status: skeleton, not fixed.** Values marked `[ ]` wait for the pod pilot (tuning seeds 101 and 102). The document
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

## 8. Values from the pilot (to fill in before fixing)

| item | PSF L 8 | Qiskit L 8 | PSF L 16 | Qiskit L 16 |
|---|---|---|---|---|
| cos (sim vs stand-in), means 5 / 6 (H100 pilot; 24 directions, 8 points, T = 256) | 1.00 / 1.00 | 0.80 / 0.85 | 0.97 / 0.99 | 0.87 / 0.97 |
| stand-in gradient size ÷ simulator's (sd_dev / sd_sim) | 0.74-0.79 (PSF, both depths together) | 0.34-0.50 | (with L 8) | 0.81 |
| sd_dev (b = 8) | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| pilot AUC, S2R2-B, by lr | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| pilot AUC, SPSA2, by a | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| wall time per loop, S2R2-B, H100 (s): estimate from the pilot's component timings / measured | 0.69 / `[ ]` | 1.09 / `[ ]` | 1.42 / `[ ]` | 2.14 / `[ ]` |
