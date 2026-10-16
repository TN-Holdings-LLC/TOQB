# Loop reach run, 6 qubits, 8 layers, 1,000 iterations, 200 seeds, 2026-10-16 (TOQB, fast engine)

Scored against [`prereg/2026-10-16-loop-n6-reach.md`](../../prereg/2026-10-16-loop-n6-reach.md) (SHA-256
`f880a674...9317`), fixed at 16:57:53 CEST and pushed (commit `e42b6b3`) before the run. Times in CEST.

**Run.** 18:15:54-21:07:53, the owner's home machine (WSL), ten processes, once, without interruption, at TOQB
`e42b6b3` (PSF-Zero's arm reads only c61 and a22, checked by SHA-256). Every fixed hash was checked before the first
seed; the 200 plans in the run folder are byte for byte the pre-registered ones. **Files:** `score.md` and `score.json`
(`python -m toqb.score_loop_preg5`), `times.txt`, `raw_records.zip` (the run folder as the run zipped it).

**Scored again by the authors** from the raw records: the same verdicts and numbers, except two reported means in the
third decimal (0.583 / 0.582 at iteration 100, 0.682 / 0.683 at 400): Python 3.12 (home) sums floats with compensation,
3.11 (the authors' cloud) does not.

## Verdicts

| ID | prediction | verdict | numbers |
|---|---|---|---|
| R1 | every arm run valid, with all 21 evaluations | **CONFIRMED** | 400 of 400 |
| R2 | (primary) PSF-Zero's model reaches a noisy test accuracy of 0.65 in fewer iterations | **CONFIRMED** | Qiskit - PSF-Zero +73 iterations (95% +27 to +120), p = 0.0011; sooner / equal / later: 103 / 33 / 64 |
| R3 | the same for 0.70 | **CONFIRMED** | +82 iterations (+25 to +140), p = 0.0028; 104 / 27 / 69 |
| R4 | PSF-Zero's model reaches 0.65 for fewer dollars | **CONFIRMED** | +$311 (+$133 to +$490), p = 0.0003; cheaper in 136 of 200 |

scipy's one-sided t-test and Wilcoxon test agree (R2 0.0012 / 0.0017, R3 0.0027 / 0.0028, R4 0.0004 / 0.00007).

## The two numbers

- **Display:** median iterations to a noisy test accuracy of 0.65, **PSF-Zero 200, Qiskit level 2 250**; to 0.70,
  **300 against 400**. Median dollars to 0.65: **$755 against $968**; to 0.70: **$1,133 against $1,549**.
- **Essential:**
  - PSF-Zero's model got to 0.65 sooner in 103 of 200 seeds, at the same time in 33, later in 64.
  - The mean accuracy curve is above Qiskit's at every evaluation from 50 to 1,000 iterations (by 0.02-0.04), and
    still 0.724 against 0.704 at 1,000.
  - Both models stay below the classical ones (0.73-0.77) within 1,000 iterations.

## Reading

- **The question is answered yes, for this task and device model:** PSF-Zero's model reaches the same accuracy about
  a fifth to a quarter sooner and for about 22-27% less QPU money (medians), at IBM's price model.
- **A correction to the authors' reading of the long run** (5 seeds, unscored): from those five curves the authors read
  that the difference vanishes by about 1,000 iterations. With 200 seeds it has not vanished at 1,000 (+0.020).
- **Scope:** one task (n = 6, L = 8, teacher seed 4), one device model (FakeFez with TOQB's noise model), in simulation.
  The test accuracy is on 48 points, in steps of 1/48.
