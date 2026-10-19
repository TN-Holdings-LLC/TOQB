# TF: twin-fidelity proposal — does a PSF-compiled circuit make the GPU twin know the device's gradient better?

**Status: proposal to the owner, 2026-10-19 (workplace).** The design is not fixed. Nothing here was run; the time
figures are formulas on the H100 pilot's timings.

## 1. Hypothesis

> For the same task, the GPU simulator (the digital twin) knows the direction of the stand-in's gradient better when
> the circuits are compiled by PSF-Zero than when they are compiled by Qiskit. In other words, cos(simulator gradient,
> stand-in gradient) is higher for PSF.

**What the H100 pilot showed** (`toqb.gradcos`, 24 directions, 8 points, T = 256, student means 5 / 6):

| | L = 8 | L = 16 |
|---|---|---|
| PSF cos | 1.00 / 1.00 | 0.97 / 0.99 |
| Qiskit cos | 0.80 / 0.85 | 0.87 / 0.97 |
| stand-in gradient size ÷ simulator's, PSF | 0.74-0.79 | (with L 8) |
| stand-in gradient size ÷ simulator's, Qiskit | 0.34-0.50 | 0.81 |

**Why this is a hypothesis, not yet a result:**

- There are only two means per cell, and the measurement is uncertain: with 24 directions, a true 0.9 reads anywhere
  in about 0.81-0.96 (90 %).
- At L = 16 the two Qiskit values (0.87 and 0.97) already straddle the PSF ones.

**Why it matters, if it holds:** it would be a reason for "CUDA-Q + PSF-Zero" that is not about speed. A twin that
knows the device's gradient better makes simulator-driven learning (S2R) more faithful to the device.

## 2. A possible mechanism (unconfirmed)

- Qiskit's circuits are wider and longer: 14 qubits and 25.6 µs at L = 8, against PSF's 10 qubits and 9.5 µs.
- The stand-in contains effects the simulator's model does not: static ZZ crosstalk, relaxation during the longer
  schedule, and calibration differences (over-rotation).
- These effects grow with time and with the number of coupled qubits. So they would bend the stand-in's gradient
  away from the simulator's more for Qiskit's circuits.
- The smaller stand-in-to-simulator gradient size for Qiskit at L = 8 (0.34-0.50, against 0.74-0.79 for PSF) fits this
  picture: more damping. It does not prove it.
- **Not checked:** which effect contributes how much. A follow-up could switch the stand-in's ZZ, idle relaxation and
  over-rotation off one at a time.

## 3. Proposed measurement (simulation only; for the owner to decide)

| item | proposal | alternatives |
|---|---|---|
| directions K | 96 | 48 (half the cost) |
| student means M | 20 (seeds disjoint from all earlier ranges: `[ ]`) | 10 |
| points b, trajectories T | 8, 256 (as the pilot) | T = 128 |
| depths | L = 8 and 16 | – |
| compilers | PSF (compile_template) and Qiskit (setting as X22 §4, `[ ]`) | – |
| pairing | each mean m gives one PSF value and one Qiskit value, with the same student mean, directions and points | – |
| statistic | d_m = z(cos_PSF,m) − z(cos_Qiskit,m), with z = artanh (Fisher) | – |
| test | per depth, two-sided paired t-test (or Wilcoxon signed-rank) on the d_m, p < 0.01, Holm over the 2 depths | one-sided (PSF higher), if the owner prefers to pre-commit the direction |
| also reported | the mean of each cos with 99 % CI; the size ratio sd_dev / sd_sim; the split-half reliabilities | – |

**A technical point to decide before fixing.** The split-half corrected cos can reach or exceed 1 (PSF L 8 gave 1.00),
where artanh is infinite. The options:

- (i) Apply z to the **raw** correlation, and report the corrected cos alongside. This is valid if both compilers'
  reliabilities are similar and high; they are recorded, and T is raised if they are not.
- (ii) Clip the corrected cos at 0.999 before z. This is simple, but the clipping point affects the result.
- **Proposal:** (i), with a pre-declared condition that both reliabilities are ≥ `[ ]` (for example 0.95).

**Rough sensitivity** (not a power calculation). With K = 96, the sampling sd of one z value is about
1/√(K − 3) ≈ 0.10, so about 0.15 for a difference of two values. The pilot's L = 8 gap (cos about 0.99 against 0.83)
is about 1.4 on the z scale. Over 20 means it would be detected easily. The L = 16 gap is smaller and less certain.

## 4. Cost (pod GPU time only; no QPU)

**Per student mean and cell:**

    circuits = 2·K·b
    t_mean   = 4 · circuits · T · s₆₈/(68·32) + (circuits/68) · k₆₈

- The factor 4 is the simulator and the stand-in, two halves each.
- s₆₈ and k₆₈ are the H100 times for 68 circuits (simulator × 32 trajectories, and compile).
- The stand-in is assumed to run at the simulator's batched rate (`[ ]` to confirm).

| K, T | PSF L 8 | Qiskit L 8 | PSF L 16 | Qiskit L 16 | total for M = 20, 4 cells |
|---|---|---|---|---|---|
| 96, 256 | 237 s | 589 s | 433 s | 1,171 s | **13.5 GPU-h** |
| 48, 256 | 119 s | 295 s | 217 s | 585 s | 6.8 GPU-h |
| 96, 128 | 122 s | 297 s | 224 s | 589 s | 6.8 GPU-h |

**Cost:** GPU-hours × p (the pod's $/hour, unconfirmed). Wall-clock time is shorter with several processes or GPUs in
parallel.

## 5. Limits (stated with the proposal)

- **The result may depend on how the stand-in was made.** The stand-in's deviations from the simulator's model were
  fixed in stage 0: ibm_marrakesh calibration data, static ZZ of 10 kHz, and 1 % over-rotation. A different but equally
  plausible stand-in could give a different PSF-vs-Qiskit gap. The stand-in is not changed to fit this proposal.
- **The real answer comes from hardware: decision A,** the same agreement measured on an IBM device. This proposal is
  a step before A. It tells whether the effect exists in simulation and how large it is, which helps size A's shots
  and directions (see the QPU cost check).
- **Vanity and essential figures,** if the hypothesis holds:

  | | figure |
  |---|---|
  | Vanity | for example, "PSF makes the digital twin about 15 % more accurate" (the pilot's L = 8 cos, about 0.99 against 0.83) |
  | Essential | the gap in cos between compilers on a stand-in we built ourselves, at n = 10 and L = 8 / 16; whether it carries over to a real device is unknown until A |
