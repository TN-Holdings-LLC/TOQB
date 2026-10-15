# A hard 2-minute QPU budget: short test, not scored (2026-10-16)

The owner's real constraint is about 2 minutes of QPU time. No loop run so far had a hard budget. Runs 1, 2 and the
long run compared the arms after a fixed number of iterations. Their "budget" was the reference arm's own spend plus
5%, which never binds. This short test checks a hard stop and gives a first look. It is not a scored run: no
prediction was fixed, and the seeds (9101-9120) are not used by any scored run.

**Setup.**

- Run 1's plan unchanged, with the fast engine.
- **Stop:** `evaluation.stop_budget_usd = 192` (2 min at $96/min, batch mode). Training stops before the job that
  would pass $192. The model it bought is evaluated at that point. Evaluations are not billed, as in the original
  design.
- Iterations are capped at 60.
- Run in the authors' cloud workspace, 2 processes, 2026-10-16 01:42-01:47 CEST.

**Mechanics (as intended).**

- PSF-Zero stopped after 50 iterations ($188.78); Qiskit level 2 after 49 ($189.72).
- PSF-Zero's iteration is 2.5% cheaper (shorter circuits), so it gets one more.
- Every arm run was valid; 2 of 2 equivalence checks passed per arm. The third check, at iteration 59, is never
  reached.
- 22 s per seed for both arms.

**First look (20 seeds).**

| | PSF-Zero | Qiskit level 2 | difference | PSF-Zero better / equal / worse |
|---|---|---|---|---|
| noiseless accuracy | 0.549 | 0.555 | -0.006 | 7 / 4 / 9 |
| noisy accuracy | 0.520 | 0.524 | -0.004 | 9 / 0 / 11 |
| margin | 0.027 | 0.008 | +0.019 (t-test p = 0.014) | 15 / 0 / 5 |

**Reading.**

- Within 2 minutes, no accuracy difference is visible on 20 seeds.
- The margin (signal) is larger with PSF-Zero, as in run 2.
- A scored run would need its own pre-registration on new seeds.

`rows.json` holds every seed's figures and the plan.
