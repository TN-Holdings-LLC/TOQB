# Check of the QPU cost estimate for measuring gradient agreement on hardware (decision A), 2026-10-19

Workplace review of the stated assumptions. **Nothing was run on any device and no money was spent.** The noise
figures come from a formula and from a small Monte Carlo of `toqb.gradcos`'s estimator (`mc_gradcos.py`, shot noise
only). The estimator was read from the bundle `toqb_s2rg2.bundle` (commit c9ee8f8).

**Note added 2026-10-19: the pod pilot uses different settings.**

- **Different from this document's plan:** the pilot measures agreement with b = 8 points, T = 256 trajectories,
  K = 24 directions and two student means (seeds 5 and 6). This document's hardware plan assumes b = 4.
- **Read `sd_dev` as a b = 8 value:** the `sd_dev` the pilot reports is the spread of the 8-point mean loss
  difference.
- **The signal changes with b.** Averaging over more points shrinks the part of each point's gradient that is
  independent of the others, so s at b = 4 is expected to be larger than at b = 8. By how much depends on how
  correlated the points' gradients are; it is `[ ]` until it is measured.
- **The noise also changes with b.** Shot noise per direction scales as 1/(2bN) (§2), so b = 4 has twice the noise
  variance of b = 8 at the same N.
- **Recompute the reliability for the hardware plan** with s measured at b = 4. `toqb.gradcos` prints only summary
  figures, so this needs one more stand-in run with b = 4 on the pod (simulation only, no QPU). Otherwise the plan's b must be changed to 8, which doubles the
  circuits (192 → 384). Per compiler-depth, that costs:
  - at the same 1,000 shots per circuit: twice as much (117.5 s, about $188);
  - at the same total shots (N = 500 per circuit): only the extra per-circuit overhead, 192 × 0.036 s ≈ 6.9 s (about
    $11). This leaves the noise per direction unchanged.

## 1. The arithmetic and the price

- **Arithmetic:** 192 × (0.036 + 1000 × 0.00027) = 192 × 0.306 = **58.75 s → $94**. Two compilers × 8 layers make
  **$188**; adding 16 layers makes **$376**. Correct.
- **Price:** IBM's pricing page currently states Pay-As-You-Go "starts at $96 USD per minute", "billed per second of
  usage" ($1.60/s; the plan's `usd_per_s` 1.6 matches).
- **Not stated by IBM** (checked on the pricing page and the "manage cost" guide): any minimum charge per job, and
  exactly which parts of a job count as QPU usage.
- **Treat as unconfirmed:** the $94 per compiler-depth is a lower bound until a small first job's reported usage
  confirms the per-circuit and per-shot rates.

**Rates.** The 0.036 s per circuit and 0.27 ms per shot are ibm_fez measurements on PSF-Zero's circuits
(2026-10-14). They should carry over to these circuits, with three conditions:

- The per-shot time is mostly the device's repetition delay and readout. A 10-21-qubit, 16-layer circuit lasts a few
  µs, so the per-shot rate should hold for both compilers and both depths. **Not measured** for these circuits.
- **Use one job:** all 192 circuits as PUBs of one SamplerV2 job. Separate jobs may add per-job overhead.
- **No twirling or mitigation:** gate or measurement twirling multiplies the circuits run. EstimatorV2 enables
  mitigation by default; SamplerV2 does not.

## 2. Is 1000 shots enough? (signal sd ≈ 0.02)

**What gradcos measures.**

- It uses K = 24 random ±1 directions at one student mean. For each direction it takes the loss difference
  L(m + hD) − L(m − hD), with h = 0.1, on b points.
- The loss is (1 − z·y)/2, averaged over the b points. Here z is ⟨Z⟩ of the readout qubit. **Note:** this is a
  linear loss, not CE.
- The cosine is the correlation of the simulator's and the device's differences over the K directions. It is
  corrected by the split-half reliability (Spearman-Brown).

**Shot noise of one direction's difference** (worst case z = 0, b points, N shots per circuit):

    Var = 2 · (1/4) · (1/(b N)) = 1/(2 b N)        → b = 4, N = 1000:  sd ≤ 0.0112

**Reliability** of the device side = s² / (s² + 1/(2bN)), where s is the signal sd:

- s = 0.02 gives **0.76**. The split-half estimate in the Monte Carlo matched this (0.77).
- If the real device's signal is s = 0.01, it drops to **0.44**. That is plausible after real decoherence and readout
  error at 16 layers or with Qiskit's wider circuits.

**Monte Carlo of the corrected cosine** (90 % range over 20,000 repetitions; K = 24, b = 4):

| s | N | true cos 0.99 | true cos 0.9 | true cos 0.5 |
|---|---|---|---|---|
| 0.02 | 1,000 | 0.88-1.16 | 0.74-1.07 | 0.15-0.79 |
| 0.02 | 3,000 | 0.95-1.03 | 0.79-0.97 | 0.18-0.74 |
| 0.02 | 10,000 | 0.97-1.00 | 0.81-0.96 | 0.20-0.73 |
| 0.01 | 1,000 | 0.67-unbounded (the correction blows up) | 0.55-unbounded | -0.00-unbounded |
| 0.01 | 3,000 | 0.85-1.24 | 0.71-1.14 | 0.14-0.83 |
| 0.01 | 10,000 | 0.94-1.04 | 0.78-0.98 | 0.17-0.75 |

**Reading.**

- **With 1,000 shots and s = 0.02,** one measurement tells "near 1" apart from "about 0.5". It does **not** tell 0.99
  apart from 0.9.
- **If the real signal is smaller (s ≈ 0.01),** 1,000 shots are not enough: the reliability correction becomes
  unstable.
- **K = 24 is a second limit, independent of shots.** Even with almost no shot noise (s = 0.02, N = 10,000), a true
  0.9 reads as 0.81-0.96.

**Shots needed for a device-side reliability R:** N = R / ((1 − R) · 2b · s²), with b = 4.

| R | s = 0.02 | s = 0.01 |
|---|---|---|
| 0.8 | 1,250 | 5,000 |
| 0.9 | 2,800 | 11,000 |
| 0.95 | 5,900 | 24,000 |

**Cost** at the stated rates, per compiler and depth (192 circuits):

| N | QPU seconds | per compiler-depth | for both compilers × L = 8, 16 |
|---|---|---|---|
| 1,000 | 59 s | $94 | $376 |
| 2,000 | 111 s | $177 | $708 |
| 3,000 | 162 s | $260 | $1,040 |
| 10,000 | 525 s | $840 | $3,362 |

## 3. Points for the owner (the design is not changed here)

1. **Decide first what the measurement must distinguish.** If it is "0.99 against about 0.5", 1,000 shots suffice
   when s ≈ 0.02. If it is "0.99 against 0.9", more shots and more directions are needed.
2. **Before buying time, know the real signal s.** Tonight's pilot gives `sd_dev` on the stand-in for each compiler
   and depth. The hardware's s may be smaller. The first, cheapest hardware job (one compiler, L = 8) gives the real s
   and the real per-shot rate. The remaining jobs can then be sized from those.
3. **Ways to raise the signal-to-noise ratio** (each is a design change, for the owner to decide; listed only):
   - more shots;
   - more points b (the noise falls with b·N, but each point adds circuits and their 0.036 s overhead);
   - a larger step h (the signal grows about linearly in h; the bias from curvature grows too);
   - more directions K (narrows the correlation's own sampling range);
   - repeating at a second student mean.
