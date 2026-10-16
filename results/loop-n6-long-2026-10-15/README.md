# Loop long run, 5 seeds x 100,000 iterations: stopped by the owner at about 70,000 (2026-10-16)

Pre-registration: [`prereg/2026-10-15-loop-n6-long.md`](../../prereg/2026-10-15-loop-n6-long.md) (commit `013bb48`,
pushed before the run).

- **Started:** 2026-10-15 18:16:48 CEST on the owner's home machine.
- **Stopped:** by the owner on 2026-10-16, after the trajectory below. It is not scored. The raw partial records were added on 2026-10-16:
  `times.txt`, and per seed `plan.json` (byte for byte the pre-registered plan) and both arms' `*.partial.json`;
  `raw_records.zip` holds the same folder with the logs (home paths shortened to `~/`), which `.gitignore` keeps out
  of the tree. The last evaluation written was at 70,000 or 80,000 iterations (PSF-Zero's arm at
  70,000 in seeds 3001, 3003 and 3005, every other arm at 80,000).

## Why it was stopped: the design had no time limit

- The run asked whether the difference compounds over 100,000 iterations. It had no QPU budget: 100,000 iterations
  stand for about 67 QPU hours per model.
- TOQB's question is what a fixed amount of QPU time buys. The owner's real budget is about 2 minutes, about 50
  iterations.
- The authors (Claude) built the run without pointing out that the question drops the time limit. The owner stopped it.

## The trajectory as read at about 70,000 iterations (`score_loop_preg3 --partial`, pasted by the owner)

Mean noiseless accuracy over the 5 seeds, and the difference d (PSF-Zero minus Qiskit level 2):

| iteration | PSF-Zero | Qiskit | d noiseless | d noisy |
|---|---|---|---|---|
| 60 | 0.487 | 0.537 | -0.050 | -0.017 |
| 600 | 0.738 | 0.667 | +0.071 | +0.027 |
| 2,000 | 0.738 | 0.754 | -0.017 | -0.015 |
| 10,000 | 0.758 | 0.762 | -0.004 | +0.033 |
| 30,000 | 0.758 | 0.775 | -0.017 | +0.004 |
| 70,000 | 0.762 | 0.783 | -0.021 | -0.033 |

**Reading.**

- d moves between -0.05 and +0.07 without a trend: no compounding.
- Seeds 3002 and 3004 stay above 0, and 3001, 3003 and 3005 below.
- Both arms reach 0.76-0.78 by about 10,000 iterations and stay there.
