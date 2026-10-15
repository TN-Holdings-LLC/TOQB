# Loop standard run, 6 qubits, 8 layers, seeds 101-120, 2026-10-15 (TOQB v15)

Scored against the pre-registration [`prereg/2026-10-15-loop-n6-standard.md`](../../prereg/2026-10-15-loop-n6-standard.md)
(SHA-256 `e584bbcd...f8da`). It was fixed at 13:24:01 CEST and pushed (commit `393995e`) before the run.

**Run.**

- **Time:** 13:27:53-14:00:28 CEST, on the owner's home machine (WSL), ten seeds at a time, one thread per process.
- **Command:** `run.sh` of the pre-registration. Every fixed hash was checked before the first seed.
- **Versions:** TOQB `393995e`, PSF-Zero `4f6070c` with psf_compile c61 and front end a22, Qiskit 2.5.2, Aer 0.17.2.
- **Run once.** There was no interruption.

## Verdicts

| ID | prediction | verdict | numbers |
|---|---|---|---|
| L1 | every arm run valid and complete | **CONFIRMED** | 40 of 40; equivalence 3 of 3 in every run |
| L2 | (primary) noiseless final accuracy higher with PSF-Zero | **NOT DECIDED** | mean difference +0.040, p = 0.059 (threshold 0.01); PSF-Zero better in 14 of 20, worse in 6; worst seed -0.188 |
| L3 | noisy final accuracy higher with PSF-Zero | **CONFIRMED** | mean difference +0.078, p = 0.0013; better in 16, equal in 1, worse in 3; worst seed -0.135 |
| L4 | noisy final margin higher with PSF-Zero | **CONFIRMED** | mean difference +0.038, p = 0.00056; better in 16 of 20 |
| L5 | the noiseless effect is large (>= 0.10) | **REFUTED** | 0.040 (below 0.05) |
| L6 | PSF-Zero spends no more than Qiskit | **CONFIRMED** | every seed: $226.54 against $232.31, batch |

The sign-flip p-values were checked with scipy: a one-sided t-test gives 0.054 and 0.0008, and the Wilcoxon test gives
0.056 and 0.0024, for L2 and L3.

## The two numbers

- **Display:** mean final accuracy, noisy, for the same money: **PSF-Zero 0.549, Qiskit level 2 0.471.**
- **Essential:**
  - PSF-Zero gave the better model in 16 of 20 seeds and a worse one in 3. The worst seed was -0.135.
  - But both models are weak. Neither arm reached accuracy 0.7 in any seed. The classical models reach 0.73-0.77 on
    the same points.

## Reading

**Where the difference comes from.**

| | PSF-Zero | Qiskit level 2 |
|---|---|---|
| start, noiseless (the same angles) | 0.287 | 0.287 |
| final, noiseless | 0.552 | 0.512 |
| final, noisy | 0.549 | 0.471 |
| what noise takes at evaluation | 0.003 | 0.042 |

- The noisy difference of 0.078 splits about in half.
  - **About 0.040 comes from the training.** The noiseless accuracy of the final angles is higher with PSF-Zero, but
    not at the pre-registered strength (L2 not decided, L5 refuted).
  - **About 0.039 comes from evaluation.** PSF-Zero's circuits are 0.48 x as long: noise takes 0.003 from its
    accuracy, and 0.042 from Qiskit's.
- So "the compiler compounds through training" is not established. "Shorter circuits give a better model for the same
  money" is, on this task.

**The pilot overstated the effect.**

- Pilot: noiseless differences of +0.208 and +0.167, from two seeds.
- Here: a mean of +0.040 over 20 seeds. The pilot's seed 11 (0.781) lies above every seed of this run: the best was
  0.688.
- L5's threshold of 0.10 was set from the pilot and was wrong.

**What the task shows about itself.**

- The loop moves from 0.29, worse than chance, to about 0.55 in 60 iterations, near chance. Neither arm learns the task
  well at this budget.
- The comparison is therefore made in a regime where both models are poor. A longer training, or an easier task, is
  needed before a statement about good models.

**Compiler versions.** psf_compile c62, c63 and c63a, built today, give circuits identical to c61's on this task. 40
circuits were compared after a22's template, bit for bit, with the same two-qubit count (120) and duration
(8.712 us). So the result holds for them too.

## Later note (2026-10-15, after scoring)

The same 20 plans were run again with TOQB's fast engine
([`../fast-engine-check-2026-10-15/`](../fast-engine-check-2026-10-15/)). Its noise model is the same; its shot stream
is not.

- The noiseless difference was again +0.040.
- The noisy difference was +0.039, with PSF-Zero better in 15 of 20 seeds.
- So the split of the noisy difference into "half training, half evaluation" above is not robust: it moves with the
  shots alone.
- The verdicts are not changed. They are those of this run, as pre-registered.

## Files

- `seed101/` to `seed120/`: the plan, both arms' records, the classical reference and the per-seed report.
- `score.md`, `score.json`: `python -m toqb.score_loop_preg`, as pre-registered.
- `logs/`: one log per seed and the scoring log.
- `times.txt`: the commits and times.
