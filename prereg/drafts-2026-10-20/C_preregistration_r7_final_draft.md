# S2R design C: pre-registration, final draft (r7) — train on the GPU twin, predict the device, test with one job ("stamp")

**Status: final draft (r7), not fixed.** r1-r6 were written at the workplace and at home on 2026-10-19/20 (CEST).
Values marked `[ ]` are still open; `{…}` marks a number that is filled in from a record named next to it, before
fixing.

**Revision r7 (2026-10-20, about 06:10 CEST, home).** The r6 file is unchanged. Owner decisions of 2026-10-20
(06:05 CEST) adopt r6's proposals:

- **seed 301** (outside every used range), **2,000 loops**, **time limit 6 h** from T0 to submission with r6's
  replacement rule (§5);
- **Qiskit at optimization level 2 against the day's Target** (`qiskit:2:target:template`, the arm used in the tuning
  run, the rehearsal and the dry run);
- **the device rule** of §5: eligibility E1-E4, then the fixed order ibm_marrakesh, ibm_fez, ibm_kingston.

Filled from the code, unchanged since the rehearsal (TOQB `5a6981e`; `toqb/s2rc_device.py plans` writes the same
training block as `gpu/s2rc_rehearsal.sh`): the training settings of §7, and the CE formula of §3 (confirmed equal to
the scoring code). Confirmed by the owner at 06:35 CEST: T_pred = 1,024 and R = 20,000 (§3, §7), and H2's test by
Wilcoxon as written (§2). Filled in after the rehearsal: §6's record and W_r (§5). P1's reading (§5) is added when it exists.

**Revision r6 (2026-10-20, 01:40 CEST, workplace).** The r5 file is unchanged. All four items are proposals for
the owner; hypotheses, tests, α, P, N and M are unchanged.

- **§5, the device day as a timed schedule.** Every step has an owner, a place and a planned duration, and a proposal
  for the time limit is given.
- **§5, a written rule for choosing the device** among ibm_fez, ibm_marrakesh and ibm_kingston. It needs no
  measurement and does not compare calibration quality.
- **§5, steps that lower the risk of a calibration update between fetch and submission.** They are procedure only.
- **§7, the open settings** are listed with proposals. Seed 299, used by the device-path dry run, is added to the
  excluded seeds.

**Revision r5 (2026-10-19, 15:45 CEST, home).** The r4 file is unchanged. **Owner decision: option A** (§4):
P_8 = 150, P_16 = 500, N = 250, M = 1, about 138 s of the open plan's 160 s. Still open: the device, the seed (proposal
301), the loop count (proposal 2,000) and the time limit. The device path's procedure check passed at this size on
the home GPU (TOQB `results/s2rc-device-dryrun-2026-10-19/`).

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
  - M = 1 (owner, r5), so the question of pooling several models does not arise.
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
  - Wilcoxon as written; the paired t alternative is not adopted (owner, r7, 06:35 CEST).
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
   error. It is computed with traj2 from T_pred trajectories, T_pred = 1,024 (the code's default and the rehearsal's value; owner,
   r7).
2. **Replicates.** For r = 1 … R (R = 20,000, as T_pred), as implemented in `toqb/s2rc.py`:
   - (twin computational error) draw p1'_i ~ N(p1_i, p1_i(1 − p1_i)/T_pred), clipped to [0, 1]. This is an upper-side
     estimate of the trajectory Monte Carlo error;
   - (shot noise) draw k_i ~ Binomial(N, p1'_i) and set p̂_i = k_i/N;
   - compute CE as −(1/P) Σ_i log c_i, exactly as for the device, where:
     - q_i = clip(p̂_i, 1e-4, 1 − 1e-4);
     - c_i = 1 − q_i for y_i = +1 (the P(1) < 0.5 side);
     - c_i = q_i for y_i = −1.

     Confirmed (r7): `toqb/s2rc.py predict_job` uses `s2r2._ce`; `toqb/s2rc_device.py ce` is the same formula and a
     unit test checks the two agree (`tests/test_s2rc_device.py`).
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

- The circuits are compiled against the day's backend.target: PSF compile_template (psf_ai_compile a22 with
  psf_compile c61, as in the rehearsal), and Qiskit at optimization level 2 against the Target (owner, r7).
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

Job total = 4 cells × M models × cost per cell. Chosen (owner, r5): P_8 = 150, P_16 = 500, N = 250, M = 1.

- **Options:** P ∈ {100, 200, 300, 500} and N ∈ {250, 500, 1,000}, with P allowed to differ between L 8 and L 16.
  H1 power, H2 power and cost for each are in `consult_A-D_2026-10-19.md` §C.
- **Short version:**
  - H1 at L 16 needs P_16 of about 500 if the accuracy there is about 0.60.
  - N has little effect on accuracy: about 0.01 from N = 1,000 to 250.
  - H2 at L 16-sized gaps needs N = 1,000 or M > 1.

**Proposal for the open plan (r4); option A decided by the owner in r5.** The open instance had 2 min 40 s (160 s) of QPU time left on
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

**Choice of device (r6 proposal; adopted by the owner in r7).** E1, E2 and E4's `[ ]` are answered on the day
from the fetched Targets and recorded; they are reads, not choices.

- **Constraint.** Choosing needs the fetched Targets, and fetching is an IBM connection, so the rule is applied at
  home on the day.
- **No measurement, no quality comparison.** The rule reads only failed elements and fixed facts, not error rates.
  This keeps to the owner's rules of 2026-10-14 (no effort on calibration data) and 2026-10-15 (placement ignored for
  now).

1. **Eligible devices.** A device is eligible when all of the following hold. Each is a yes / no read at home.
   - **E1.** It is reachable from the plan whose time is used (the open plan's 160 s), `[ ]` to confirm per device.
   - **E2.** Its two-qubit gate is CZ (all three are Heron-class; `[ ]` to confirm in the fetched Target).
   - **E3.** It is operational now, with no announced maintenance within the time limit after T0.
   - **E4.** PSF's placement contains no failed qubit or coupler. PSF's template places the ring from the coupling map
     alone, so its physical qubits follow from the coupling map. If the three devices share one coupling map, they are
     the same indices on all three (`[ ]` to confirm). "Failed" uses the same rule as `assemble`
     (`toqb.devices._failed`), which stops on a failed element anyway; E4 just applies it before training.
2. **Order among the eligible.** This is a fixed order, declared now and not computed:
   1. **ibm_marrakesh.** The tuning run and the rehearsal used its published calibration (`snapshot:marrakesh`), and
      the stand-in is built on it.
   2. **ibm_fez.** B's pilot and the dry run used FakeFez.
   3. **ibm_kingston.**
3. **The first eligible device in the order is used,** and the reason is recorded: which devices were eligible, and
   which E failed for the others.
4. **Fetch once for each candidate** (read-only; no QPU time). The chosen device's fetch time is T0. The other
   fetches are kept, not used.

**Not proposed:** choosing by error rates, by queue length or by the twin's predicted score. That would select on the
calibration or on outcomes.

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
4b. **[pod] (r7, owner 2026-10-20; report only)** `toqb.reftwin JOB FETCH REF --shots T`: the reference twin (Aer's
   standard noise model from the fetched Target) predicts the same circuits, blind. Its outputs' SHA-256
   (`reftwin.json`) are fixed with the manifest's in step 5. It feeds TOQB v0.2's prediction layer only; H1, H2, R1
   and R2 do not use it. Duration on the pod: {from the dry run of 2026-10-20}; T = {…}.
5. **[home]** Copy the job folder home. Fix this document (SHA-256 and CEST time), with the manifest's SHA-256 in it.
6. **[home, VPN off]** `submit`: one job. It stops if the backend's calibration time differs from the fetched one
   (retrain, as below), if the files differ from the manifest, or if a job was already submitted.
7. **[home, VPN off]** `result`, then `score` (offline).

**Time limit.** From T0 to job submission: at most 6 h (owner, r7), or W_r + 1.6 h if the rehearsal's W_r exceeds
4.4 h (rule below). Rehearsal: W_r = 17,004 s = 4.72 h (the largest Qiskit L 16 run, training
plus prediction, with the stand-in's verification included because the record does not separate it); W_r > 4.4 h,
so **the limit is W_r + 1.6 h = 6.32 h**.

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

**Guide for the time limit** (r7: decided, 6 h; this guide is kept as background).

- **Parts:** T_limit ≥ (fetch and compile, minutes, `[ ]`) + training wall time (above) + predictions (`[ ]`) +
  fixing and hashing + a margin.
- **Rough guide:** about 6 h for N = 2,000 with enough slots (R ≤ S), and about 12-13 h for N = 5,000.
- **Not checked:** whether this fits within the device's calibration update interval.

**Day schedule (r6 proposal).** M = 1, so 4 runs. Durations are planned values; the sources are noted.

| # | step | where | planned duration | source |
|---|---|---|---|---|
| 0 | before T0: pod started, environment and TOQB commit checked, plans template and commands written out, GPU idle | pod | (before T0) | dry run of 2026-10-19 |
| 1 | read the device rule (above), fetch the candidates, choose; T0 = the chosen fetch | home | 10 min | – |
| 2 | copy the Target to the pod; `plans` | pod | 5 min | – |
| 3 | train 2,000 loops, 4 runs in parallel (Qiskit L 16 sets the pace) | pod | 4.2 h | C r3 §5 (B's pilot, 6 runs per GPU; with 4 runs it may be shorter, unmeasured) |
| 4 | predict: 500 points × 1,024 trajectories (Qiskit L 16), with R = 20,000 replicates | pod | about 10 min (rough) | home RTX 4070 dry run: Qiskit L 16 took 45 min for 20 loops plus prediction, mostly prediction; ÷ about 5 (H100 / 4070 speed-up of traj2 for Qiskit L 16). Not measured on the H100; the rehearsal measures it |
| 5 | `assemble` (all checks) | pod | 1 min | 28 s at home |
| 6 | copy the job folder home; fix this document (SHA-256, CEST, manifest hash) | home | 15 min | – |
| 7 | `submit` (it checks the calibration time again) | home | 2 min | – |
| | **T0 → submission** | | **about 5.0 h** | |

**Time limit (r6 proposal): 6 h from T0 to submission**, that is about 5.0 h plus 1 h of margin.

- **Replacement rule, fixed now.** If the rehearsal's measured Qiskit L 16 training plus prediction time, W_r, is
  longer than 4.4 h, the limit becomes W_r + 1.6 h. The rehearsal runs 12 runs at a time, so W_r overstates the day's
  4-run case; using it is conservative.
- **The time limit is about the time from fetch to submission.** Queue time after submission is not included (as
  before).

**Lowering the risk of a calibration update before submission** (procedure only; the design is unchanged).

- **What stops a submission:** `submit` stops when `backend.properties().last_update_date` differs from the fetched
  one. How often that timestamp changes on these devices is not known here.
  - If it changes several times a day, a 5 h pipeline may rarely reach submission.
  - Not verified; P1 checks it.
- **P1. Learn the update times first.** This is a home, read-only step with no QPU time; it needs the owner's
  permission, as for any IBM connection.
  - Before the day, read the properties history of the candidate devices for the past 7 days
    (`backend.properties(datetime=…)`) and record when `last_update_date` changes.
  - Start T0 right after the usual update time.
- **P2. Watch during training.** Every 30 min, home reads `last_update_date` (read-only). If it changes:
  - stop the runs at once and restart from step 1 with the same seed and settings (§5 "Retraining");
  - this saves the rest of the hours that would end in a refused submission;
  - the voided version is recorded with the reason.
- **P3. Shorten T0 → submission without changing the design.**
  - Start the pod before T0 (step 0).
  - Use one GPU per run (4 GPUs). Whether this beats 6 runs per GPU is unmeasured.
  - Have the home side ready to submit at the planned time.
- **P4 (optional, owner's choice): two staggered pipelines.** Start a second complete pipeline (its own fetch) about
  2 h after the first. The rule for which one to submit is fixed now: the pipeline whose fetched calibration time
  equals the backend's at submission; if both match, the earlier fetch.
  - The predictions are never compared, so nothing is selected on outcomes.
  - Cost: about twice the pod time of one pipeline.
- **If P1 shows updates more often than every 6 h,** the design's definition of "a new calibration" (the timestamp)
  would need the owner's decision. One alternative would be to compare the Target's noise values instead of the
  timestamp. That changes the design, so it is only raised here, not proposed as a change.

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

**Rehearsal record (r7; filled in before fixing).** Run 2026-10-20 from 04:07:09 CEST on one H100 (PAR 6), TOQB
`5a6981e`, psf-zero `7a827829`, seeds 201-203, LR 0.4, 2,000 loops, P 500, N 1,000. Record: the pod's zip, SHA-256
`d93dc912365e71bedefb4b31b015e627e98b0292537d0d4e554e8794fa5b389c`, fixed at home on 2026-10-20 at 09:45 CEST; per
run and cell in TOQB `results/s2rc-rehearsal-2026-10-20/README.md`. Procedure check (a): passed (12 of 12 runs valid,
no fault). Record (b), in short: H1 below 0.01 in every cell for every seed; R1, stand-in CE inside the twin + shots
interval for PSF in 6 of 6 runs and for Qiskit in 1 of 6 (every miss above the interval); H2's direction (the twin's
P(1) error larger for Qiskit) at both depths. None of this changes the device test.

- Nothing in the device test is changed because of it: hypotheses, α, test statistics, P, N, M, seeds, loop count and
  learning rate stay as they are.
- There is no δ or threshold that could be moved.

## 7. Training settings

| setting | value | source |
|---|---|---|
| learning rate | **0.4**: lowest mean stand-in CE over the 4 cells among 0.2 / 0.4 / 0.8 (0.5922 against 0.6032 / 0.5957), on tuning seeds 101-102 (`s2rc`, 500 loops, 200 test points). It is inside the grid. In B's pilot, 0.2 had been best but was at the edge of B's grid | C's tuning run, 2026-10-19 (§6) |
| loops per model | **2,000** (owner, r7) | owner |
| training data (points, batch per loop) | 64 training points (teacher seed 4, angle 0.3, gap 0.2); per loop an antithetic gradient from 8 random ±1 directions at step h = 0.1 on 4 training points; initial scale 1.0 | `toqb/s2rc_device.py plans`, identical to the rehearsal |
| trajectories per training loop | 32 (as B) | same |
| test points P, shots N | **P_8 = 150, P_16 = 500, N = 250** (§4, option A; owner, r5) | owner |
| models (seeds) per cell, M | **M = 1** (owner, r5), so the pooling question of §2 does not arise | owner |
| seeds | **301** (owner, r7); already used and excluded: 9001-9020, 101-102, 201-203, 299 | owner |
| T_pred, R (prediction) | **T_pred = 1,024, R = 20,000** (the code's defaults, as in the rehearsal; owner, r7). r6 notes: the twin's Monte Carlo error per point at T_pred = 1,024 is about 0.5/√1,024 = 0.016 at most, half the shot noise at N = 250 (0.032), and it is inside the interval by design. R = 20,000 leaves 100 replicates in each 0.5 % tail of the 99 % interval | owner |
| time limit T0 → submission | **6 h**, with the replacement rule from the rehearsal (§5) (owner, r7) | owner |
| device | **the rule of §5** (eligibility E1-E4, then the fixed order marrakesh, fez, kingston) (owner, r7) | owner |

- **The same models and test points are used for both compilers** within a seed (H2's pairing).
- **No selection.** Models are not selected after training: every trained model goes into the job (if M > 1 is chosen),
  and none is dropped for its twin-predicted score.

## 8. Vanity and essential figures (both reported, side by side)

| | figure |
|---|---|
| Vanity | "On the real device, accuracy `[ ]` %" |
| Essential | how well the GPU twin predicted the device (R1, R2) and the PSF / Qiskit difference (H2); device use: 1 job, $`[ ]`; accuracy above 0.5 is a low bar, and the CE and accuracy shortfall against the twin's prediction is reported next to it |

## 8b. A note on the learning curve (r7, found 2026-10-20 during the rehearsal)

- `toqb/s2rc.py` records the twin's CE every 200 loops on the first `curve_points` = 100 test points. `teacher_data2`
  returns the test points ordered by class (all label +1 first, then all −1), and does not shuffle them.
- So for P = 500 the curve is computed on 100 points of class +1 only; for P = 150 on 75 of class +1 and 25 of class −1.
  The curve's CE is therefore not comparable with the predicted CE (all P points, both classes). Checked from the code;
  that it explains the whole gap seen in the tuning run (curve 0.10-0.17 below the predicted CE) is to be checked with
  the rehearsal records (`twin_p1` and `test_labels` give the CE on the first 100 points directly).
- Nothing tested here uses the curve: training draws from the shuffled training points, and the predictions, H1, H2,
  R1 and R2 use all P test points. The code stays as in the rehearsal for the device day; the curve is reported with
  this note. Changing it is left to the owner, after the stamp.

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
