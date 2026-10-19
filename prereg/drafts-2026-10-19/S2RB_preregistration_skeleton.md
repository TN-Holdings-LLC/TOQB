# S2R2-B: pre-registration skeleton — GPU simulator learning with stand-in records vs SPSA2 on the stand-in

**Status: skeleton, not fixed.** Values marked `[ ]` wait for the pod pilot (tuning seeds 101 and 102). The document
is fixed by SHA-256 and the CEST time before any scored run. Written at the workplace on 2026-10-19 (design text
only; nothing was run). The design is the owner's decision B (final); this document does not change it.

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

**Finding of 2026-10-18.**

- The simulator knows the direction of the stand-in's gradient almost exactly: cos ≈ 0.99, measured for PSF at
  L = 8, on CPU, with `toqb.gradcos` (split-half corrected).
- Not yet measured: Qiskit at L = 8, and both compilers at L = 16. These come from the pilot (`[ ]`, table in §8).

**Consequence (recorded as part of this pre-registration).**

- In S2R2-B the stand-in's measurements are not used for learning at all.
- So any difference between S2R2-B and SPSA2 is the effect of the GPU simulator, and not of information from the
  stand-in. **The stand-in's contribution is recorded as approximately zero.**
- The result can show that a simulator-driven loop, billed only for 2 stand-in circuits per loop, reaches a lower CE
  per dollar than learning on the stand-in alone. It cannot show that information flows from the device through the
  GPU.
- The stand-in is not shifted on purpose to manufacture a stand-in contribution. That would fit the conditions to the
  result.

**Vanity and essential figures** (both reported, side by side):

| | figure |
|---|---|
| Vanity | "S2R2-B learns about `[ ]` × faster than SPSA2 per dollar" |
| Essential | the learning is done by the GPU simulator; the stand-in's information contributes about nothing, because the simulator already knows the gradient (cos `[ ]`); on real hardware the simulator's model is likely less accurate, so the gap may well be smaller there; untested |

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
| cos (sim vs stand-in), seed 5 / 6 | 0.99 (CPU) / `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| sd_dev (b = 8) | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| pilot AUC, S2R2-B, by lr | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| pilot AUC, SPSA2, by a | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| wall time per loop, S2R2-B (s) | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
