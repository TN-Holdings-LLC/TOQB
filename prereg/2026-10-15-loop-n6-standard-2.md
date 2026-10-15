# Pre-registration: TOQB loop standard run 2, 6 qubits, 8 layers, 200 seeds (2026-10-15)

**Status: pre-registration.** It is fixed by the commit that adds it (2026-10-15, about 16:05 CEST), together with the
plans, the code hash list and the scoring script below. That commit is pushed to the public repository before the run
starts. The run is made once. Times are given in CEST.

## 1. Why a second run

Standard run 1 ([`results/loop-n6-standard-2026-10-15/`](../results/loop-n6-standard-2026-10-15/)) left three things
open.

- **Its primary prediction was not decided.** The noiseless difference was +0.040, p = 0.059, on 20 seeds.
- **Its models were weak.** No seed reached 0.7. The loop stopped near chance after 60 iterations.
- **Its noisy difference moved with the shots alone.** A re-run with another shot stream gave +0.039 instead of
  +0.078 ([`results/fast-engine-check-2026-10-15/`](../results/fast-engine-check-2026-10-15/)).

Run 2 changes two things.

- **SPSA's settings are calibrated so that the models learn.** This was done before any compiler ran on them.
- **Ten times the seeds,** made affordable by the fast engine.

It also asks the question the loop scenario was built for: does the difference grow with training?

## 2. What is run

**The plans:** [`loop-n6-standard-2-2026-10-15/plan_s1001.json`](loop-n6-standard-2-2026-10-15/) to
`plan_s1200.json`, written by `make_plans.py`. `SHA256SUMS` lists them; its SHA-256 is
`b77a961f1012faec71356b8a0845d91b15feedaacc5aff905a2153051f35b3f9`.

**What is the same as run 1:**

- the task: n = 6, L = 8, teacher seed 4, 64 training and 48 test points;
- 400 shots; FakeFez with TOQB's noise model;
- the two arms, Qiskit level 2's template and PSF-Zero's template (a22 + c61, the same files and SHA-256 as run 1);
- the price.

**What changes:**

- **SPSA:** 200 iterations, batch 16, a = 10, c = 0.4, A = 2. Each iteration runs 32 circuits.
- **Evaluations:** every 20 iterations.
- **Loop seeds:** 1001-1200.
- **The engine:** `"engine": "fast"` (`toqb.fast_noise`). It is the same noise model. It was checked against an exact
  evolution to 1e-14 and against Aer to 1e-7 in the probability. Its shot stream is its own.

**How the settings were chosen** ([`calibration/`](loop-n6-standard-2-2026-10-15/calibration/)):

- **No compiler and no noise:** exact <Z0> with 400 shots drawn per point, on seeds 901-920 and 941-980, which no
  scored run uses.
- **The grid:** batch 8, 16 and 32; a from 1 to 16; c from 0.1 to 0.8.
- **The choice:** the best mean noiseless test accuracy for the number of circuits.
- **Confirmed on 40 fresh seeds (941-980):** mean 0.726 after 200 iterations, 75% of seeds at 0.7 or above. The old
  settings gave 0.694 and 30% at 200 iterations on 10 seeds, and about 0.60 at 60.
- So 0.73 is about what this model reaches with SPSA without noise. It is level with the classical models
  (0.73-0.77).
- **One timing run, seed 999.** Only its times were read: 105 s and 95 s per arm in the authors' cloud workspace.

**The code:** `CODE_SHA256SUMS` lists the nine TOQB modules the run uses (SHA-256 `808c6a55...abcf`). Among them is
the scoring script [`toqb/score_loop_preg2.py`](../toqb/score_loop_preg2.py) (tests:
[`tests/test_score_preg2.py`](../tests/test_score_preg2.py)).

**The machine and the command:**

- the owner's home PC (WSL), Qiskit 2.5.2, Aer 0.17.2, ten seeds at a time;
- [`run.sh`](loop-n6-standard-2-2026-10-15/run.sh). It checks every hash above and the versions, and refuses an
  existing output folder.
- **Expected time:** 1.5-2 hours.

**Interruption rule:** as run 1.

- A run that stops before all 200 seeds are written is started again into a new folder.
- The first complete run is scored. Incomplete ones are kept and reported.

## 3. Predictions

**Definitions:** as run 1. "Final" is iteration 200. d is PSF-Zero minus Qiskit, per seed.

**The test:** a one-sided sign-flip test of the mean of d. With 200 seeds it is computed over 200,000 random sign
patterns with a fixed seed.

**Failed arms:** as run 1. A seed whose Qiskit arm failed is left out. A failed PSF-Zero arm counts at the worst value.

| ID | prediction | confirmed if | refuted if | basis |
|---|---|---|---|---|
| M1 | every arm run is valid and complete | all 400 | any not | run 1: 40 of 40; the fast engine's re-run: 40 of 40 |
| M2 | **(primary)** the noiseless final accuracy is higher with PSF-Zero | mean d > 0 and p <= 0.01 | mean d <= 0 | run 1 and its re-run: +0.040 both, at 60 iterations |
| M3 | the noisy final accuracy is higher with PSF-Zero | mean d > 0 and p <= 0.01 | mean d <= 0 | +0.078 and +0.039 |
| M4 | the noisy final margin is higher with PSF-Zero | mean d > 0 and p <= 0.01 | mean d <= 0 | +0.038 and +0.029 |
| M5 | **the noiseless difference grows with training:** d at iteration 200 is larger than d at iteration 60 | mean of (d_200 - d_60) > 0 and p <= 0.01 | mean <= 0 | none: this is the open question |
| M6 | PSF-Zero spends no more than Qiskit on the whole training | every seed | any seed over | the same circuits and shots, shorter circuits |

A value between the two thresholds is NOT DECIDED.

## 4. Reported without prediction

- Per arm: the mean, sd and range of the noisy and noiseless accuracy at iteration 60 and at the end, the margin, the
  dollars, the two-qubit gates, the duration and the wall time.
- The seeds reaching 0.7.
- The classical reference.

## 5. How the result is read

**The two numbers.**

- **Display:** the mean final noisy accuracy of each arm, for the same money.
- **Essential:** in how many of the 200 seeds PSF-Zero gave the better model, the worst seed, and how many seeds of
  each arm reached 0.7.

**Scope.**

- One task and one device model, in simulation.
- It is not a hardware result.
- It makes no claim that a quantum model beats a classical one.
