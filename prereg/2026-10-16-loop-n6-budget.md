# Pre-registration: TOQB loop budget run, 6 qubits, 8 layers, 2 minutes of QPU, 1,000 seeds (2026-10-16)

**Status: pre-registration.** It is fixed by the commit that adds it (2026-10-16 CEST), with the plans, the code hash
list and the scoring script. The run is made once. Times are given in CEST. The design was confirmed by the owner
before it was built.

**Where it runs, and how it is fixed.**

- The owner runs it at the workplace. The workplace machine has no GitHub access, so the commit cannot be pushed before
  the run.
- Instead, this document's SHA-256 is given to the owner in the conversation with the authors before the run starts,
  and printed by the run into `times.txt`. The run also checks it.
- The commit is pushed afterwards, from home, with the results.

## 1. The question

With 2 minutes of QPU time, which compiler returns the better model?

This is TOQB's loop question, under the owner's real budget. No earlier loop run had a hard limit.

## 2. What is run

**The plans:** [`loop-n6-budget-2026-10-16/plan_s6001.json`](loop-n6-budget-2026-10-16/) to `plan_s7000.json`, from
`make_plans.py`. `SHA256SUMS` has SHA-256 `71a7f6996324891feaba549a7d7c1700da4a47a4c43a0ba006469ee473d487a7`.

**Run 1's settings, unchanged:**

- the task: n = 6, L = 8, teacher seed 4, 64 training and 48 test points;
- SPSA: batch 8, a = 3.0, c = 0.2, A = 2, initial angles in +-0.5;
- 400 shots; FakeFez with TOQB's noise model;
- the two arms, Qiskit level 2's template and PSF-Zero's template (a22 + c61, the same files and SHA-256 as runs 1
  and 2).

**The budget:** `evaluation.stop_budget_usd = 192`, i.e. 2 minutes at $96 per minute, in batch mode.

- Each arm trains until the next job would pass $192. It is then evaluated on the 48 test points.
- Evaluations are not billed, as in the original design.
- From the short test (seeds 9101-9120, unscored), PSF-Zero stops after 50 iterations and Qiskit after 49. PSF-Zero's
  iteration is 2.5% cheaper, and that iteration counts.
- The iteration cap is 60. It is never reached.

**Other settings:**

- **Engine:** the fast engine.
- **Seeds:** 6001-7000. No earlier run used them.
- **Why not 5001-6000:** an end-to-end test of `run.sh`, made while this document was being written, ran seeds
  5001-5004 of the first plan set and printed their results. Those seeds are therefore not used. The whole set was
  moved to 6001-7000 before anything was fixed.
- **Code:** `CODE_SHA256SUMS` (SHA-256 `dd3c443e...1470`), including the scoring script
  [`toqb/score_loop_preg4.py`](../toqb/score_loop_preg4.py) (tests: `tests/test_score_preg4.py`).

**The machine and the command:**

- the owner's workplace PC (Windows), one process per CPU;
- [`run_budget.py`](loop-n6-budget-2026-10-16/run_budget.py), which checks every hash (including this document's) and
  the versions, and refuses an existing output folder. [`run.sh`](loop-n6-budget-2026-10-16/run.sh) is the same for
  WSL.
- **Expected time:** about 13 s per seed per pair of CPUs, measured in the authors' cloud on 2 CPUs. On 2 CPUs that
  is about 4 hours, on 8 about 1 hour.
- **PSF-Zero's files:** only the four files the PSF-Zero arm reads, taken from PSF-Zero commit `2eb4da1`: c61, a22,
  a15 and a14. The first two are checked by SHA-256.

**Interruption rule:** a run that stops early is started again into a new folder. The first complete run is scored.

## 3. Predictions

d is PSF-Zero minus Qiskit, per seed, at the budget.

**The test:** one-sided sign-flip test of the mean of d, over 200,000 random sign patterns with a fixed seed.

**Failed arms:** a seed whose Qiskit arm failed is left out. A failed PSF-Zero arm counts at its worst value.

| ID | prediction | confirmed if | refuted if | basis |
|---|---|---|---|---|
| B1 | every arm run valid, stopped within the budget, evaluated at the stop | all 2,000 | any not | short test: 40 of 40 |
| B2 | **(primary)** the noiseless accuracy at the budget is higher with PSF-Zero | mean d > 0 and p <= 0.01 | mean d <= 0 | short test: -0.006 (20 seeds); run 1 at 60 iterations: +0.040 |
| B3 | the noisy accuracy at the budget is higher with PSF-Zero | as B2 | as B2 | short test: -0.004 |
| B4 | the noisy margin at the budget is higher with PSF-Zero | as B2 | as B2 | short test: +0.019 (15 of 20); run 2: 1.32 x |
| B5 | PSF-Zero gets at least as many iterations as Qiskit within the budget | every seed | any seed fewer | cheaper iterations |

A value between the thresholds is NOT DECIDED.

**The authors' expectation, stated before the run.** This is not a criterion.

- B2 and B3 are more likely refuted or not decided than confirmed.
- B4 is likely confirmed.
- With 1,000 seeds, the difference is resolved to about +-0.006.

## 4. Reported without prediction

- Per arm: accuracy (noisy, noiseless), margin, iterations, dollars, two-qubit gates, duration and wall time.
- The classical reference.

## 5. How it is read

- **Display:** the mean noisy accuracy at 2 minutes of QPU.
- **Essential:** the share of the 1,000 seeds in which PSF-Zero returned the better model, and the worst seed.
- **Scope:** one task and one device model, in simulation.
