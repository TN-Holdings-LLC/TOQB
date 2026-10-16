# Pre-registration: TOQB loop reach run, 6 qubits, 8 layers, 1,000 iterations, 200 seeds -- how soon each compiler's model reaches a target accuracy (2026-10-16)

**Status: pre-registration.** Fixed by the commit that adds it and by its SHA-256, given to the owner before the run;
pushed by the owner before the run starts. The run is made once. Times in CEST. The design was confirmed by the owner
before it was built (2026-10-16, about 16:54 CEST).

## 1. The question

The budget run (1,000 seeds, $192) found PSF-Zero's model better at the owner's budget, and the unscored long run
(5 seeds) suggested that both models reach the same ceiling, PSF-Zero's sooner. The question: **does the model
trained through PSF-Zero reach a given test accuracy in fewer iterations and for less money?**

## 2. What is run

**The plans:** [`loop-n6-reach-2026-10-16/plan_s8001.json`](loop-n6-reach-2026-10-16/) to `plan_s8200.json`, from
`make_plans.py`. `SHA256SUMS` has SHA-256 `0421cfe0b373c60c3cf1dd396c343d5cfc9776c533447ebc42dacd02dddcc92a`.

**Run 1's settings, unchanged** (as the budget run): the task (n = 6, L = 8, teacher seed 4, 64 training and 48 test
points); SPSA (batch 8, a = 3.0, c = 0.2, A = 2, initial angles in +-0.5); 400 shots; FakeFez with TOQB's noise model;
the two arms, Qiskit level 2's template and PSF-Zero's template (a22 + c61, the same files and SHA-256 as before).

**What changes:**

- **Iterations:** 1,000, no budget stop.
- **Test evaluations:** every 50 iterations (21 points with iteration 0). Evaluations are not billed.
- **The loss curve:** every 10th iteration (recorded, not scored).
- **Engine:** the fast engine. **Seeds:** 8001-8200; no earlier run used them.
- **Code:** `CODE_SHA256SUMS` (SHA-256 `3ec365d95cee45aac361f2bfe472a96000215743617982f7d8615947182f057d`): the engine modules are those of the budget run, byte for byte;
  the scorer is new, [`toqb/score_loop_preg5.py`](../toqb/score_loop_preg5.py) (tests: `tests/test_score_preg5.py`).

**The machine and the command:** the owner's home PC (WSL), ten processes, with
[`run.sh`](loop-n6-reach-2026-10-16/run.sh), which checks every hash and the versions and refuses an existing output
folder. **Expected time:** about 3.5 hours (300 s per arm run at home, 400 arm runs, 10 at a time).

**Interruption rule:** a run that stops is started again into a new folder; the first complete run is scored.

## 3. Predictions

**Reaching a target:** for each arm and seed, the first evaluation (iteration 50 or later) whose noisy test accuracy
is at least the target. An arm that never reaches it counts as reaching it at 1,050 iterations, for its dollars per
iteration times 1,050. **d** is Qiskit minus PSF-Zero, per seed (positive: PSF-Zero sooner or cheaper).

**The test:** one-sided sign-flip test of the mean of d, 200,000 random sign patterns with a fixed seed.

| ID | prediction | confirmed if | refuted if | basis |
|---|---|---|---|---|
| R1 | every arm run valid, with all 21 evaluations | all 400 | any not | the budget run: 2,000 of 2,000 |
| R2 | **(primary)** PSF-Zero's model reaches a noisy test accuracy of 0.65 in fewer iterations | mean d > 0 and p <= 0.01 | mean d <= 0 | long run (5 seeds, unscored): about 300 against 600 |
| R3 | the same for 0.70 | as R2 | as R2 | long run: both about 0.70 at 600-1,000 |
| R4 | PSF-Zero's model reaches 0.65 for fewer dollars | as R2 | as R2 | R2, and 2.5% cheaper iterations |

A value between the thresholds is NOT DECIDED.

**The authors' expectation, stated before the run** (not a criterion): R2 and R4 confirmed; R3 less certain, because
at 0.70 both arms are near their ceiling and many seeds may not reach it within 1,000 iterations.

## 4. Reported without prediction

- Per target and arm: the share of seeds reaching it, the median iterations and dollars.
- The mean noisy test accuracy at each evaluation point, per arm; the accuracy at 1,000 iterations.

## 5. How it is read

- **Display:** the median iterations (and dollars) to 0.65 and 0.70 per compiler.
- **Essential:** in how many of the 200 seeds PSF-Zero's model got there sooner, and how much QPU money that saves at
  IBM's price. One task, one device model, in simulation; noisy test accuracy on 48 points moves in steps of 1/48.
