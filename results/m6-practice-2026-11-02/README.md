# OS plan M6 (sentinels, part 1) and practice problems P2, P3 on ibm_kingston, 2026-11-02

- **Declaration:** `prereg/drafts-2026-11-02/m6_practice_note.md` (SHA-256 a247cea8...7a0a), fixed 11:59 CET, TOQB
  574dea4. Fetch 12:00:25 CET (calibration 11:27:08 CET, Target 1c40ad59...). Registry
  `results/coverage-days-2026-11-02-day3/list_after.json`; masked (9, 10), (29, 38), (85, 86). Built by
  `gpu/m6_practice.py` with psf-os eb20501 (`build.json`); rings equal to day 3's (S = A n = 40, V = B n = 40,
  P = A n = 20).
- **Jobs** (every manifest "stay"; calibration at submission 11:54:20 CET):
  S dbk6rphffo6c73baub3g, 12:03:02 CET, 7 s billed; V dbk6rshffo6c73baubc0, 12:03:15 CET, 7 s; P dbk6s0hffo6c73baubn0,
  12:03:31 CET, 6 s. All done by 12:04 CET. 20 s billed in all (26.1 s by the time model).

## Judged

| # | item | S (standard n = 40) | V (around the registry) | verdict |
|---|---|---|---|---|
| 1 | sentinel on S | **DEAD**: one run of 18 sites, qubits 3-7, 17, 27-29, 38, 49-55, 59 (mean -0.12) | | the sentinel sees the known dead run in the user's job |
| 2 | sentinel on V | | **CLEAN** (sites 0.34-0.55, median 0.44) | the ring placed around the registry was clean at the job's time |
| 3 | sh6, D = 12 (ring mean) | 0.780 +- 0.001 | 0.825 +- 0.001 | **HELPS** (+0.045 +- 0.002) |
| 3 | sh6, usable sites | 40 / 40 | 40 / 40 | **SAME** |
| 4 | P2 cluster parity, fraction right | 0.482 +- 0.008 | 0.602 +- 0.008 | **HELPS** (+0.121 +- 0.011) |
| 5 | P3 kicked Ising n = 20, L = 4 | MSE 0.0061 against 0.595 for a mixed output | | **READS** |
| 5 | P3 kicked Ising n = 20, L = 8 | MSE 0.0171 against 0.416 | | **READS** |

- **Sentences fixed in advance:** (1) the sentinel sees the known dead run in the user's job; (2) the ring placed
  around the registry was clean at the job's time; (4) avoiding the dead path helps even a one-layer computation.
  Item 3 is HELPS and SAME, so by the note its verdicts are reported as they come. Part 2 of M6 may now be declared
  (part 1 held).

## Reported

- **sh6 on the dead run:** the sh6 computation was not dead where the echo was. On the 18 positions of the echo's dead
  run the sh6 signal averaged 0.72 (the rest of the ring 0.83; lowest site 0.13), so the run is not a dead run for
  this computation and no usable site was lost. The avoiding ring raised the ring mean by 0.045, about 6 % of the
  signal, as on marrakesh (M3b: +0.040).
- **P2:** on the standard ring the weight-40 parity read near zero for every input (-0.09 to +0.04); on the avoiding
  ring it read 0.18-0.25. One CZ layer on the defect's couplers was enough to erase the parity. Cause not chased.
- **P3:** the device recovered 0.91 (L = 4) and 0.84 (L = 8) of the exact answer (sum of answer x measured over sum of
  answer squared), on the healthy n = 20 ring.
- **Headline and essential numbers:** headline, parity right 48 % -> 60 % and sentinel DEAD / CLEAN as predicted;
  essential, the defect that kills a 24-layer mirror echo costs a 12-layer forward computation only 0.1 on its sites,
  but erases a weight-40 parity in one layer. What a defect costs depends on the computation; the sentinel reports the
  echo's view of it.
