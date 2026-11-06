# Every device job: with a search-based arm in the same job, or our arms alone (2026-11-06 13:47 CET; owner's
question: "does a search arm in the job make our results worse?"). Read from the committed results; not declared.

## Jobs with a search-based arm (Qiskit level 2 target / blind, SABRE)

| date | device | folder | our arm against the search arm in the same job |
|---|---|---|---|
| 10-24 | kingston | flow-c | zipper scale 1.00 / corr 0.98 against the twin; Qiskit L2 -0.16 / -0.53 |
| 10-28 | kingston | device-d5a | rule lam 0.943, Qiskit 0.765 (TIE, +1.6 SE) |
| 10-28 | kingston | device-d6 | rule ahead at 11 of 12 n, 1 TIE |
| 10-29 | marrakesh, kingston | noise-wall-1 (2 jobs each) | rule readable depth L* +30 to +73 layers over blind Qiskit |
| 10-30 | marrakesh, kingston | device-2026-10-30 test 2, 3E, 3P, 3P max | rule 0 LOSS in 144 duels |
| 10-30 | kingston | device-2026-10-30 qelmA (one arm per job) | each arm alone in its own job |
| 11-06 | marrakesh | os3d-device | v3 per-site MSE 2-3 x SABRE's (q29, q49 on its bridge); v3 mirror higher |

All other device jobs (65 of 82: d1-d4, coverage days, clean depth, safe ladder, gray/black stages, fix repeat, two
devices, qca, m6, psf-os first run, du-repro, du-stage2, kim-*, p6, os2d, repair, corr, practice, daily, twirl
explore, 3D probe) had our arms alone (several of our own arms at most).

## Matched checks of the question

1. **10-30 kingston, the same rule echo cells with and without Qiskit.** Morning: test 2 / 3E (rule, zipper, blind
   Qiskit in one job). Afternoon 14:12 CET: the rule cells alone (rerun-rule-only, declared). Differences of a few
   per cent in both directions: rule-only higher by 0.02-0.05 at n = 36, lower by 0.035 at one n = 20 cell; L* n = 20
   21.9-22.3 alone against 22.8-23.7 with Qiskit, n = 36 24.5-26.2 against 23.0-23.6, n = 40 and 72 the same within SE.
   No consistent direction.
2. **10-29 kingston noise wall:** the rule's charge ratio with Qiskit in the job (n = 20, L 24 / 50 / 100: 0.731 /
   0.536 / 0.304) was at or above the value declared from earlier rule-only runs (p = 0.0051: 0.721 / 0.505 / 0.256).
3. **11-06 marrakesh:** the daily FX-A job (no search arm) showed the same q29 shift (0.402 against exact 0.240;
   11-05: 0.198) and the same DEAD sentinel stretch as the 3D job with SABRE, three minutes apart.

## Reading

- The data do not support "a search arm in the job makes our arm worse": where it can be checked, our arm's values
  with and without a search arm differ by device drift, in both directions.
- Mechanism: a job's circuits run one after another, each for all its shots, with the qubits reset between shots;
  two arms of one job never run at the same time.
- Until 11-06, our arm read better than the search arm in every comparison job (TIE at most). 11-06 is the first job
  where the search arm had the lower per-site error, and its cause is the two elements on v3's bridge.
