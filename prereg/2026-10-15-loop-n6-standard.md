# Pre-registration: TOQB loop standard run, 6 qubits, 8 layers (2026-10-15)

**Status: pre-registration.** It is fixed by the commit that adds it (2026-10-15, about 13:20 CEST), together with the
plans and the scoring script listed below. That commit is pushed to the public repository before the run starts. The
run is made once. Times are given in CEST.

## 1. The question

For the same money, does PSF-Zero's compiler return a better trained model than Qiskit's?

The pilot ([`results/loop-pilot-n6-2026-10-15/`](../results/loop-pilot-n6-2026-10-15/)) said yes in both of its two
seeds, unscored. Two seeds establish nothing. This run asks the same question on 20 new seeds, with the predictions
and the test fixed here.

## 2. What is run

**The pilot's run, unchanged, on 20 new seeds.**

- **The plans:** [`loop-n6-standard-2026-10-15/plan_s101.json`](loop-n6-standard-2026-10-15/) to `plan_s120.json`.
  - They are written by `make_plans.py` from the pilot's `plan_loop_pilot_n6_s11.json` (SHA-256 `b1b29153...`).
  - Only the name, the note and `loop_seed` change. `loop_seed` is 101-120.
  - The pilot's seeds 11 and 12 are not reused.
  - `SHA256SUMS` lists the 20 plans. Its own SHA-256 is
    `7f8e7a3fa52ab68956fcbe172dee83c445587ca9e2c85edac0041e490251e067`.
- **The task, the optimizer and the device** (the same for every seed):
  - the teacher-student task: n = 6, L = 8, teacher seed 4, 64 training and 48 test points;
  - SPSA: 60 iterations, batch 8, a = 3.0, c = 0.2, A = 2, initial angles in +-0.5;
  - 400 shots; FakeFez with TOQB's noise model.
- **What `loop_seed` changes:** the initial angles, the batches and the SPSA perturbations. Both arms of a seed follow
  the same draws.
- **The arms:**
  - `qiskit:2:target:template`: Qiskit 2.5.2, level 2, one template per circuit shape;
  - `psfai:template`: PSF-Zero's front end a22 with psf_compile c61, the pilot's versions.
    - `patches/psf_compile_c61_2026-10-15/psf_compile.py`, SHA-256 `254cfabc...b3728`;
    - `patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py`, SHA-256 `625f9431...a8ce`;
    - both from the PSF-Zero checkout at commit `9cfa904`.
- **The machine and the command:**
  - the owner's home PC (WSL), Qiskit 2.5.2, Aer 0.17.2, one thread per process, ten seeds at a time;
  - [`loop-n6-standard-2026-10-15/run.sh`](loop-n6-standard-2026-10-15/run.sh).
    - It checks the hashes above, the versions, and that the output folder does not exist yet.
    - It then runs the 20 seeds and scores them with `python -m toqb.score_loop_preg`.
- **The scoring script:** [`toqb/score_loop_preg.py`](../toqb/score_loop_preg.py), SHA-256
  `adae963387b8648468d9d0533d266f811514d693fb200362873d3cb892d7270d`. Tests:
  [`tests/test_score_preg.py`](../tests/test_score_preg.py).

**Interruption rule.**

- If the run stops before all 20 seeds are written (a crash, a power cut), it is started again into a new folder.
- The first complete run is scored. Every incomplete one is kept and reported.
- No seed is run twice inside one run.

## 3. Predictions

**Definitions.**

- **Final:** the evaluation after iteration 60, on the 48 test points.
- **Noisy accuracy:** the share of test points whose measured <Z0> has the label's sign.
- **Noiseless accuracy:** the same, computed exactly from the final angles without noise. It measures how far the
  training itself went.
- **Margin:** the mean of label x <Z0>, noisy.
- **The difference d:** per seed, PSF-Zero minus Qiskit.
- **The test:** exact one-sided sign-flip test of the mean of d over the seeds (2^20 sign patterns).
- **Failed arms:**
  - A seed whose Qiskit arm failed is left out of L2-L4.
  - A seed whose PSF-Zero arm failed counts with PSF-Zero at the worst value: accuracy lower by 1, margin by 2.

| ID | prediction | confirmed if | refuted if | basis |
|---|---|---|---|---|
| L1 | every arm run is valid and complete | all 40: no error, no structural failure, no gate on a failed element, every checked equivalence holds, 60 iterations | any not | pilot: 4 of 4 |
| L2 | **(primary)** the noiseless final accuracy is higher with PSF-Zero | mean d > 0 and p <= 0.01 | mean d <= 0 | pilot: d = +0.208, +0.167 |
| L3 | the noisy final accuracy is higher with PSF-Zero | mean d > 0 and p <= 0.01 | mean d <= 0 | pilot: d = +0.396, +0.156 |
| L4 | the noisy final margin is higher with PSF-Zero | mean d > 0 and p <= 0.01 | mean d <= 0 | pilot: d = +0.207, +0.050 |
| L5 | the effect on the noiseless accuracy is large | mean d >= 0.10 | mean d < 0.05 | pilot: mean 0.188 |
| L6 | PSF-Zero spends no more than Qiskit on the whole training | every seed: batch dollars of PSF-Zero <= Qiskit's | any seed over | pilot: $226.54 against $232.31; the same circuits and shots, shorter circuits |

A value between the two thresholds is NOT DECIDED.

## 4. Reported without prediction

- Per arm: the mean, sd, median and range of the noisy and noiseless final accuracy, the margin, the dollars, the
  two-qubit gates, the duration and the wall time.
- The seeds in which each arm reached accuracy 0.7, and the median dollars to reach it.
- The count of seeds where PSF-Zero is better, equal and worse, and the worst seed's difference.
- The classical reference on the same task.

## 5. How the result is read

**The two numbers.**

- **Display:** the mean final noisy accuracy of each arm, for the same money. This is the benchmark's headline.
- **Essential:**
  - In how many of the 20 seeds PSF-Zero gave the better model, and how bad the worst seed was. That is what someone
    who trains once gets.
  - Together with the noiseless difference: whether the training itself went further.

**Scope.**

- One task, one device model, in simulation.
- It is not a hardware result. It says nothing about other tasks or other sizes.
- It makes no claim that a quantum model beats a classical one.
