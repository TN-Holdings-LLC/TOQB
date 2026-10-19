# S2R design C: pre-registration skeleton (r4) — train on the GPU twin, predict the device, test with one job ("stamp")

**Status: skeleton, not fixed.** Written at the workplace on 2026-10-19 (CEST). This is design text only; nothing
was run here. Values marked `[ ]` are still open.

**Revision r4 (2026-10-19, evening CEST, home; the workplace was not reachable).** The r3 file is unchanged. Changes:

- **§4, the time model is checked** against three earlier jobs on ibm_marrakesh (2026-10-13): 60 circuits x 6,000
  shots, 99.4 s predicted against 102 s billed; 81 circuits and 198,000 shots, 56.4 s against 56 s; 4 circuits and
  16,000 shots, 4.5 s against 7 s. Within about 3 % for large jobs, plus about 3 s per job.
- **§4, a proposal for the open plan** (2 min 40 s of QPU left on 2026-10-19): option A, P_8 = 150, P_16 = 500,
  N = 250, M = 1, about 138 s. Owner to confirm; nothing else in the design changes.
- **§4, mitigation settings confirmed against the job script** (`toqb/s2rc_device.py submit`).
- **§5, the sequence on the day** is split between home and the pod, so that the IBM key stays at home
  (`toqb/s2rc_device.py`): the Target is fetched at home and carried to the pod as a file; the compiled circuits come
  back as a file and are submitted from home.
- **§6, the procedure check (a)** also runs the device path once with a fake Target and a local simulator.
- **§7**, the proposed values are entered and marked as proposals.

**Revision r3 (2026-10-19, 10:00 CEST).** The r2 file is unchanged. Changes:

- **§7, learning rate 0.4.** It was chosen from the tuning comparison; 0.4 is inside the grid.
- **§6, results of the tuning comparison.** The table and its readings are added.
- **§1 and §9, what the tuning run showed.**
  - The twin predicts PSF's circuits far better (the direction of H2, on the stand-in).
  - Qiskit reaches the lower CE, probably through calibration-aware placement.
  - This placement confound is now listed among the limits. Its handling is the owner's choice: see
    `consult_A-D_2026-10-19.md` §B.
- **§2, H2: deviation measured on a device.** The tuning run's "P(1) rms" uses the stand-in's exact P(1); a device
  gives only the shot estimate, with a floor of about 0.5/√N per point.
- **§4, P and N.** The choice is the owner's: see `consult_A-D_2026-10-19.md` §C for power and cost.

**Revision r2 (2026-10-19, 06:16 CEST).** The r1 file is unchanged. Changes:

- **§2, H1's counting direction is corrected.** In the code, label +1 means ⟨Z⟩ > 0, which is the P(1) < 0.5 side.
  r1 had this the wrong way round. §3's CE is rewritten to match.
- **§5, training time.** It now uses B's pod pilot measurements, with a guide for the time limit and a formula for
  several GPUs.
- **§6, the rehearsal's twin.** By owner decision it is built from the stand-in's public calibration
  (`device snapshot:marrakesh`), and the circuits are compiled against it.
- **§7, learning rate.** It is chosen by comparing 0.2 / 0.4 / 0.8 on the tuning seeds.

**How the document gets fixed.** It is fixed by SHA-256 and the CEST time after three things, in this order:

1. the rehearsal record (§6);
2. the day's training;
3. the predictions (§3).

It must be fixed before the device job is submitted.

**Owner decisions recorded here.**

- **Design C (2026-10-19).** Design B is closed as the "GPU learning vs SPSA2" comparison at its current pilot.
- **Answers of 2026-10-19:**
  - primary hypothesis: accuracy above 0.5;
  - H2 secondary;
  - the in-interval check and |deviation| are report-only, with no δ;
  - twin computational error goes into the interval;
  - the rehearsal is split into (a) and (b);
  - both cost tables are given.

## 1. What is claimed, and how it can fail

**Claim.** A model trained only on the GPU twin (traj2 with the device's noise model) for thousands of loops, with no
device access during training, works on the real device. The twin's pre-registered prediction of the device result is
then compared with the measurement.

**Hypotheses.**

| # | hypothesis | role |
|---|---|---|
| H1 (primary) | On the device, test accuracy is above 0.5, in each cell | confirmatory, α = 0.01 |
| H2 (secondary) | The deviation \|measured − predicted\| is smaller for PSF than for Qiskit, at each depth | confirmatory, α = 0.01, Holm over the 2 depths |
| R1 (report only) | Whether the measured CE and accuracy fall inside the twin's 99 % prediction interval | report only; no test, no δ |
| R2 (report only) | The size of \|measured − predicted\| for CE and accuracy, per cell | report only |

- **Cells:** compiler {PSF, Qiskit} × L {8, 16}; n = 10.
- **Known before fixing** (tuning run, 2026-10-19; stand-in; seeds 101-102, 500 loops; not a test; §6):
  - **Twin P(1) error:** 0.006-0.010 for PSF against 0.012-0.051 for Qiskit.
  - **Stand-in CE inside the twin's interval:** PSF in 12 of 12 runs, Qiskit in 5 of 12.
  - **Absolute CE is lower for Qiskit:** 0.535 against 0.581 at L 8, 0.613 against 0.640 at L 16 (lr 0.4).
    Qiskit's qubits are chosen from the calibration; PSF's by the coupling map alone. This is the likely cause and is
    not checked.
  - **Accuracy at L 16 is 0.56-0.62.**
- **In the rehearsal** (§6), "device" means the stage-0 stand-in throughout.

**How H1 can fail.** Device noise not captured by the twin (crosstalk, drift, readout or schedule effects) can push
accuracy to chance, most plausibly at L = 16 or for the wider Qiskit circuits.

**How H2 can fail.**

- Qiskit's deviation may be equal to or smaller than PSF's.
- The finding of 2026-10-18/19 (twin–stand-in gradient agreement: PSF cos 0.97-1.00, Qiskit 0.80-0.97) was measured
  on the stand-in, not on a device. It does not settle H2.

## 2. Tests

### H1: accuracy above chance (primary)

- **Unit:** the test point.
- **Labels and direction.** Labels are y ∈ {+1, −1}. Label +1 means ⟨Z⟩ > 0, which is the side where P(1) < 0.5.
- **When a point is correct.** A point counts as correct if the measured p̂ = k/N falls on its label's side:
  - p̂ < 0.5 for y = +1;
  - p̂ > 0.5 for y = −1.
- **Ties.** p̂ = 0.5 exactly counts as wrong (strict count).
- **What the code records.** `toqb/s2rc.py` records this strict count of correct points and the one-sided binomial p
  value.
- **Correction of r1.** r1 said "p̂ > 0.5 for label 1". That was the wrong way round.
- **Test:** one-sided exact binomial test of the number correct out of P against 0.5, per cell.
- **Multiple testing:** Holm over the cells at α = 0.01.
  - The family is the 4 cells.
  - If several models are trained (§7), the owner chooses `[ ]` between two options:
    - (a) one test per cell on the pooled points of all models. The points are then not independent across models; the
      test treats each (model, point) as a trial;
    - (b) one test per model and cell, with Holm over 4 × M.
- **Shots are not trials.** The N shots of one point are not independent evidence about accuracy, so the binomial
  count is over points.

**Accuracy needed for p < 0.01** (exact binomial, one-sided; for reference, not a power calculation):

| P | α = 0.01 | α = 0.0025 (first Holm step, 4 cells) |
|---|---|---|
| 200 | 117 / 200 = 0.585 | 121 / 200 = 0.605 |
| 500 | 277 / 500 = 0.554 | 282 / 500 = 0.564 |

### H2: PSF's deviation smaller than Qiskit's (secondary)

- **Per point i and model m:** e_{c,m,i} = \|p̂_{c,m,i} − p1_{c,m,i}\|.
  - p̂ is the device's measured fraction.
  - p1 is the twin's predicted P(1), including readout error.
  - c is the compiler.
- **Pairing:**
  - the same model seed (same initialisation and training data) for both compilers;
  - the same test point;
  - d_{m,i} = e_{QK,m,i} − e_{PSF,m,i}.
- **Statistic:** average d over the models for each point, d̄_i. Then a one-sided Wilcoxon signed-rank test over the P
  points (H2: d̄ > 0), per depth; α = 0.01, Holm over the 2 depths.
  - `[ ]` paired t as an alternative, owner's choice.
- **Why the points are the unit.** With M = 5 models, a test over models alone cannot reach p < 0.01: the smallest
  one-sided Wilcoxon p for n = 5 is 1/32 ≈ 0.031.
- **Shot-noise floor.** e includes shot noise of size about √(p(1−p)/N), which is similar for both compilers at the same
  N. It dilutes H2 but does not bias its direction, unless the two compilers' p1 differ systematically. The mean e of
  each compiler and the expected shot-only floor are both reported.
- **Device against stand-in.** The tuning run's "P(1) rms" (`twin_vs_standin_p1_rmse`) compares the twin with the
  stand-in's *exact* P(1), a mean over many trajectories. On a device only p̂ from N shots exists, so e carries shot
  noise of about 0.5/√N per point: 0.016 at N = 1,000 and 0.032 at N = 250. That is larger than PSF's 0.006-0.010
  on the stand-in. H2's power therefore depends on N (`consult_A-D_2026-10-19.md` §C).
- **Accuracy with ties.** `s2rc`'s accuracy figures (predictions and the tuning table) count a tie as 0.5. H1's
  strict count (`n_correct_strict`) counts it as wrong.
- **Also reported:** the same comparison on the CE scale per model (no test).

## 3. How the twin's prediction is made

1. **Twin output.** For each cell, model and test point, the twin gives p1_i, the predicted P(1) including readout
   error. It is computed with traj2 from T_pred trajectories, T_pred = `[ ]`.
2. **Replicates.** For r = 1 … R (R = `[ ]`), as implemented in `toqb/s2rc.py`:
   - (twin computational error) draw p1'_i ~ N(p1_i, p1_i(1 − p1_i)/T_pred), clipped to [0, 1]. This is an upper-side
     estimate of the trajectory Monte Carlo error;
   - (shot noise) draw k_i ~ Binomial(N, p1'_i) and set p̂_i = k_i/N;
   - compute CE as −(1/P) Σ_i log c_i, exactly as for the device, where:
     - q_i = clip(p̂_i, 1e-4, 1 − 1e-4);
     - c_i = 1 − q_i for y_i = +1 (the P(1) < 0.5 side);
     - c_i = q_i for y_i = −1.

     `[ ]` to confirm against `toqb/s2rc.py`. r1 wrote this formula for 0/1 labels, with the direction of r1's
     error in §2.
   - compute accuracy by the rule of §2.
3. **Intervals.** The 99 % prediction interval is the 0.5th to 99.5th percentile of the R values, for CE and for
   accuracy.
4. **Two intervals are recorded side by side:**
   - shot + twin error (step 2 as written);
   - shot only (step 2 without the redraw of p1').
5. **Model deviation (twin ≠ device) is not in either interval.** Measuring it is the purpose of the experiment (R1, R2,
   H2).
6. **Point predictions are recorded too:** the predicted CE and accuracy at p̂ = p1 (no sampling).

**Expected width (rough, unverified; workplace calculation 2026-10-19, shot only).** The CE half-width is about
0.002-0.008 for P 200-500, N 400-1,000, and mean correct-label probability 0.6-0.8. A device result inside it would
need the twin to be nearly exact. This is why R1 is report-only.

## 4. The device job

**Content of the job:**

- P test points × N shots for each cell (PSF / Qiskit × L 8 / 16) and each model;
- one SamplerV2 job;
- no twirling, no dynamical decoupling, no readout or other error mitigation, all set explicitly in the code.
  Confirmed against `toqb/s2rc_device.py submit` (r4): `dynamical_decoupling.enable`, `twirling.enable_gates` and
  `twirling.enable_measure` are set False; SamplerV2 applies no other mitigation.

**Compilation.**

- The circuits are compiled against the day's backend.target: PSF compile_template, and Qiskit with the setting of X22
  §4 (`[ ]`).
- The same compiled circuits are the ones the twin predicted.

**Recorded:**

- the job ID;
- the backend name;
- the calibration timestamp in effect;
- per-point counts;
- the QPU time billed.

The job ID is a reproducibility identifier, not a credential.

**Cost.**

- The time model is the workplace's estimate (0.036 s per circuit, 0.00027 s per shot). Not stated by IBM; checked in
  r4 against three billed jobs (within about 3 % for large jobs, plus about 3 s per job; see the revision note).
- The price of $96 per minute ($1.60 per s), billed per second, is from IBM's page.
- A per-job minimum charge is not stated there.

Per cell, for one model: P × (0.036 + N × 0.00027) s × $1.60.

| P | N | QPU time per cell | cost per cell | job, 4 cells, M = 1 | job, 4 cells, M = 5 |
|---|---|---|---|---|---|
| 200 | 400 | 28.8 s | $46.08 | $184.32 | $921.60 |
| 200 | 1,000 | 61.2 s | $97.92 | $391.68 | $1,958.40 |
| 500 | 400 | 72.0 s | $115.20 | $460.80 | $2,304.00 |
| 500 | 1,000 | 153.0 s | $244.80 | $979.20 | $4,896.00 |

Job total = 4 cells × M models × cost per cell. The chosen P, N and M are `[ ]` (owner).

- **Options:** P ∈ {100, 200, 300, 500} and N ∈ {250, 500, 1,000}, with P allowed to differ between L 8 and L 16.
  H1 power, H2 power and cost for each are in `consult_A-D_2026-10-19.md` §C.
- **Short version:**
  - H1 at L 16 needs P_16 of about 500 if the accuracy there is about 0.60.
  - N has little effect on accuracy: about 0.01 from N = 1,000 to 250.
  - H2 at L 16-sized gaps needs N = 1,000 or M > 1.

**Proposal for the open plan (r4; owner to confirm).** The open instance had 2 min 40 s (160 s) of QPU time left on
2026-10-19. With a margin of about 20 s for the time model:

| option | P_8 / P_16 | N | QPU time (model + 3 s) | H1 power L 8 / L 16 (a_16 = 0.60) | H2 power, L 8-like / L 16-like gap |
|---|---|---|---|---|---|
| **A (proposed)** | 150 / 500 | 250 | about 138 s | about 0.95 / 0.94 | about 1.0 / 0.14 |
| B | 100 / 300 | 500 | about 140 s | about 0.8 / 0.79 | about 1.0 / about 0.3 |
| C | 100 / 120 | 1,000 | about 138 s | about 0.8 / too low | about 1.0 / low |

- Powers from `pn_power2.py` (consult §C), with M = 1. If the device's L 16 accuracy is 0.56, option A's H1 power at
  L 16 falls to about 0.41.
- Option A uses almost all of the open plan: nothing is left for decision A (gradient agreement on hardware).
- `toqb/s2rc_device.py assemble` stops if the job's modelled QPU time exceeds the stated limit (`--max-seconds`;
  proposal 150 s).

## 5. Twin calibration and timing

**Noise model.** The twin's noise model is built from the device's calibration on the day of the run (backend.target).

- Fetching backend.target is a connection to IBM. It is part of the device step and is done only after the owner's
  permission.
- Nothing in this section is done before that permission.

**Sequence on the day** (T0 = the time the target is fetched). r4: the IBM key never leaves home; the pod has no IBM
connection (`toqb/s2rc_device.py`):

1. **[home, VPN off]** `fetch`: fetch backend.target and save it as a file. Record the backend, the calibration
   timestamp and the SHA-256 of the saved Target.
2. **[pod]** Copy the Target file to the pod. `plans` writes one plan per depth and seed (device `file:<target>`,
   no stand-in step).
3. **[pod]** `toqb.s2rc ... --qpy`: compile against the saved Target, train all models (§7) on the twin built from it,
   with all cells in parallel, and make the predictions (§3); the compiled test circuits are written to QPY.
4. **[pod]** `assemble`: checks (same Target hash, QPY hashes, ISA and failed elements, modelled QPU time within the
   limit) and writes the job folder: one QPY file and a manifest with every prediction, label and hash.
5. **[home]** Copy the job folder home. Fix this document (SHA-256 and CEST time), with the manifest's SHA-256 in it.
6. **[home, VPN off]** `submit`: one job. It stops if the backend's calibration time differs from the fetched one
   (retrain, as below), if the files differ from the manifest, or if a job was already submitted.
7. **[home, VPN off]** `result`, then `score` (offline).

**Time limit.** From T0 to job submission: at most `[ ]` hours.

**Training time, measured.** The source is B's pod pilot (2026-10-19, one H100, 6 runs at a time, evaluation
included; wall time ÷ loops, mean of the 3 learning rates × 2 seeds).

| | PSF L 8 | Qiskit L 8 | PSF L 16 | Qiskit L 16 |
|---|---|---|---|---|
| per loop, t_c | 1.2 s | 3.8 s | 2.4 s | 7.6 s |
| 2,000 loops | 0.67 h | 2.1 h | 1.3 h | **4.2 h** |
| 5,000 loops | 1.7 h | 5.3 h | 3.3 h | **10.6 h** |

**Corrections and limits of these figures.**

- **This replaces r1's estimate** (about 1 h for Qiskit L 16 at 2,000 loops). That estimate was a sum of
  single-process components and was too optimistic.
- **These are B's loops, not C's.** B's loop includes 2 stand-in circuits; C's has none, so C's loop may be slightly
  shorter. The evaluation interval and test set of `s2rc` may differ from B's (`[ ]`).
- **Other concurrency levels are unmeasured.** With fewer than 6 runs per GPU, a loop is probably faster.

**Wall time with several GPUs.**

- **Notation:**
  - M = models (seeds) per cell, so there are R = 4 M runs;
  - G = GPUs, with PAR runs per GPU (6 measured), giving S = G · PAR slots;
  - N = loops;
  - t_c = per-loop time from the table, with t_max = 7.6 s (Qiskit L 16) and Σ_c t_c = 15.0 s.
- **Formulas:**

      if R ≤ S:   wall ≈ N · t_max
      if R > S:   max(N · t_max, N · M · Σ_c t_c / S)  ≤  wall  ≲  N · M · Σ_c t_c / S + N · t_max
      GPU-hours ≈ N · M · Σ_c t_c / (3,600 · PAR)          (at the measured PAR = 6)

  The upper bound is the usual list-scheduling bound.

| example (N = 2,000) | runs R | slots S | wall time |
|---|---|---|---|
| M = 1, G = 1 | 4 | 6 | ≈ 4.2 h |
| M = 5, G = 4 | 20 | 24 | ≈ 4.2 h |
| M = 5, G = 2 | 20 | 12 | 4.2-7.7 h |
| M = 5, G = 1 | 20 | 6 | 6.9-11.2 h |

- GPU-hours: about 1.4 per seed (all 4 cells, 2,000 loops), so about 6.9 for M = 5.

**Guide for the time limit `[ ]`** (owner's decision).

- **Parts:** T_limit ≥ (fetch and compile, minutes, `[ ]`) + training wall time (above) + predictions (`[ ]`) +
  fixing and hashing + a margin.
- **Rough guide:** about 6 h for N = 2,000 with enough slots (R ≤ S), and about 12-13 h for N = 5,000.
- **Not checked:** whether this fits within the device's calibration update interval.

**Queue time.** Queue time after submission is outside our control.

- The calibration in effect when the job executes is recorded, as part of the same permitted device step.
- If it differs from the one at T0, this is reported. The test and prediction are not changed.

**Retraining with the day's calibration.** Retrain if, before submission, either:

- the time limit would be exceeded; or
- the backend publishes a new calibration.

Then:

1. Fetch the target again.
2. Rebuild the noise model.
3. Recompile.
4. Retrain all models from scratch, with the same seeds, settings and loop count.
5. Re-predict.
6. Fix a new version of this document.

The earlier version is kept and marked void, with the reason. Only the version fixed before the actual submission is
scored.

## 6. Rehearsal on the stand-in (simulation only)

**Setup.**

- Script: `gpu/s2rc_rehearsal.sh`.
- Seeds 201-203, P = 500, N = 1,000 shots, 2,000 loops.
- The learning rate is 0.4, chosen by C's tuning run (above and §7).
- The "device" is stage 0's stand-in (`t12` 0.3, `over` 0.01, `zz_hz` 10 kHz, seed 20261017, ibm_marrakesh
  calibration).
- **The twin (owner decision, 2026-10-19)** is built from the stand-in's public calibration, `device
  snapshot:marrakesh`. This is the Marrakesh calibration before the deliberate deviations are added.
- **All rehearsal circuits are compiled against that same calibration.** It plays the role of the day's
  backend.target in §5.

**Before the rehearsal: the learning-rate comparison (2026-10-19; tuning seeds 101-102; not scored).**

- **Run:** `gpu/s2rc_rehearsal.sh` at TOQB `1588e51`, SEEDS 101 102, 500 loops, P = 200, N = 1,000, PAR 4 per lr,
  all three lr values at once (12 runs, one H100), 06:31-09:30 CEST.
- **Twin and compilers:** the twin is built from `device snapshot:marrakesh`, and the circuits are compiled against
  it.
- **Columns:**
  - **CE and accuracy:** one simulated stand-in job, mean of the 2 seeds;
  - **P(1) rms:** twin against the stand-in's exact P(1);
  - **in:** stand-in CE inside the twin's 99 % interval. This is the interval that includes the twin's own Monte
    Carlo error; the shots-only interval is in the JSON records and was not tabulated.

| lr | cell | stand-in CE | accuracy | P(1) rms | in |
|---|---|---|---|---|---|
| 0.2 | PSF L 8 | 0.590 | 0.659 | 0.009 | 2/2 |
| 0.2 | Qiskit L 8 | 0.547 | 0.712 | 0.039 | 0/2 |
| 0.2 | PSF L 16 | 0.659 | 0.600 | 0.006 | 2/2 |
| 0.2 | Qiskit L 16 | 0.617 | 0.579 | 0.012 | 2/2 |
| 0.4 | PSF L 8 | 0.581 | 0.690 | 0.009 | 2/2 |
| 0.4 | Qiskit L 8 | 0.535 | 0.722 | 0.047 | 0/2 |
| 0.4 | PSF L 16 | 0.640 | 0.601 | 0.008 | 2/2 |
| 0.4 | Qiskit L 16 | 0.613 | 0.564 | 0.017 | 1/2 |
| 0.8 | PSF L 8 | 0.578 | 0.722 | 0.010 | 2/2 |
| 0.8 | Qiskit L 8 | 0.555 | 0.639 | 0.051 | 0/2 |
| 0.8 | PSF L 16 | 0.638 | 0.594 | 0.008 | 2/2 |
| 0.8 | Qiskit L 16 | 0.613 | 0.581 | 0.016 | 2/2 |

**Mean CE over the 4 cells:** 0.6032 (lr 0.2), **0.5922 (lr 0.4)**, 0.5957 (lr 0.8).

- lr 0.4 is chosen. It is not at the edge of the grid.
- PSF alone would take 0.8, by 0.001-0.003. Qiskit L 8 takes 0.4, by 0.02.

**Example widths** (twin interval including Monte Carlo error, P = 200, N = 1,000, 1,024 twin trajectories): PSF
L 16, lr 0.2, seed 101 gives 0.6485-0.6641, a half-width of about 0.008.

**Readings** (two tuning seeds; not a test):

- The twin predicts PSF's circuits 4-5 × better at L 8 (H2's direction, on the stand-in).
- Qiskit reaches the lower CE. The likely reason is placement (see §9); this is not checked.
- In B's FakeFez pilot the order of CE was the reverse.

**The same procedure as §3-§5,** with the stand-in in place of the device. Training, predictions and the 1-job
measurement are all simulated.

**(a) Procedure check.** This is the only part that can stop the move to the device. r4 adds one item: the device path
(`toqb/s2rc_device.py`: fetch with a fake Target, plans, training with QPY export, assemble, submit on a local
simulator, score) runs end to end once. Items:

- the script runs end to end;
- all records of §4 and §5 exist (with the stand-in in place of the device);
- the prediction intervals are produced in both forms;
- the device-side CE and accuracy are computed by the same code path as the predictions;
- the H1 and H2 tests run and give output.

If a fault is found here, it is fixed and the rehearsal is rerun with new seeds (`[ ]`) before going further. The fault
and the fix are recorded.

**(b) Record, not a gate.** Recorded for each cell:

- H1's result;
- R1 (in or out of the intervals);
- R2 (|deviation|);
- H2's result (PSF vs Qiskit).

The stand-in differs from the twin on purpose, so deviations are expected there and their cause is known. They do not
stop the device step.

**The rehearsal record is fixed** (SHA-256 and CEST time) before this document is fixed.

- Nothing in the device test is changed because of it: hypotheses, α, test statistics, P, N, M, seeds, loop count and
  learning rate stay as they are.
- There is no δ or threshold that could be moved.

## 7. Training settings

| setting | value | source |
|---|---|---|
| learning rate | **0.4**: lowest mean stand-in CE over the 4 cells among 0.2 / 0.4 / 0.8 (0.5922 against 0.6032 / 0.5957), on tuning seeds 101-102 (`s2rc`, 500 loops, 200 test points). It is inside the grid. In B's pilot, 0.2 had been best but was at the edge of B's grid | C's tuning run, 2026-10-19 (§6) |
| loops per model | `[ ]` (several thousand; the rehearsal uses 2,000). Proposal (r4): 2,000, which the rehearsal times | owner |
| training data (points, batch per loop) | `[ ]` | as B, `[ ]` |
| trajectories per training loop | `[ ]` (B used T = 32) | as B, `[ ]` |
| test points P, shots N | `[ ]`. Proposal (r4, open plan): P_8 = 150, P_16 = 500, N = 250 (§4, option A) | owner |
| models (seeds) per cell, M | `[ ]`. Proposal (r4, open plan): M = 1, so the pooling question of §2 does not arise | owner |
| seeds | `[ ]`; already used and excluded: 9001-9020, 101-102, 201-203. Proposal (r4): 301 | owner |
| T_pred, R (prediction) | `[ ]`. Proposal (r4): T_pred = 1,024, R = 20,000, as in the rehearsal | owner |
| time limit T0 → submission | `[ ]` h | owner |

- **The same models and test points are used for both compilers** within a seed (H2's pairing).
- **No selection.** Models are not selected after training: every trained model goes into the job (if M > 1 is chosen),
  and none is dropped for its twin-predicted score.

## 8. Vanity and essential figures (both reported, side by side)

| | figure |
|---|---|
| Vanity | "On the real device, accuracy `[ ]` %" |
| Essential | how well the GPU twin predicted the device (R1, R2) and the PSF / Qiskit difference (H2); device use: 1 job, $`[ ]`; accuracy above 0.5 is a low bar, and the CE and accuracy shortfall against the twin's prediction is reported next to it |

## 9. What this experiment cannot show

- **That device information improved learning.** Design C uses no device information during training.
- **Results at other widths, depths, devices or calibrations.** Only n = 10, L = 8 / 16, one device on one day.
- **That this is the only solution.** At most, the result shows that this pipeline worked once, on one device.
- **What causes any PSF / Qiskit difference.** This is not identified (TF §2's mechanism is unconfirmed).
- **Compression apart from placement.** Qiskit level 2 places the circuit from the calibration; PSF's template uses
  the coupling map only. Without a control arm, a PSF-vs-Qiskit difference (H2, CE) mixes the two. The handling is
  the owner's choice (`consult_A-D_2026-10-19.md` §B): record only; a control arm with PSF on Qiskit's qubits; or
  calibration-aware placement in PSF-Zero.
- **Stability over time.** There is one job and one calibration.

## 10. Decision rule

- **H1:** confirmed for a cell if its Holm-adjusted p < 0.01. Otherwise it is not confirmed. Each cell is reported
  separately.
- **H2:** confirmed for a depth if its Holm-adjusted p < 0.01 in the stated direction. A difference in the opposite
  direction is reported as such.
- **Reported in every case:**
  - the measured CE and accuracy;
  - both prediction intervals;
  - R1 and R2;
  - the per-compiler mean deviation with 99 % CI;
  - the billed QPU time and cost.
