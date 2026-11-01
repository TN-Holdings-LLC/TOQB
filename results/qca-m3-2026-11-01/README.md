# OS plan M3 on ibm_kingston, 2026-11-01: INCONCLUSIVE (the 40-layer forward computation is too deep to read, on either ring)

- **Declaration:** `prereg/drafts-2026-11-01/qca_m3_note.md` (SHA-256 8a5618ca...180e), fixed 12:35 CET, TOQB 428bda4.
  Fetch 12:38:03 CET (calibration 11:36:54 CET, Target 358f653c...). Avoid ring from
  `results/coverage-days-2026-11-01-day2/list_after.json` (masked (9, 10), (29, 38), (85, 86)). `sim/`, `dryrun/`.
- **Jobs:** S dbjia99kdqps7390lfng (n = 20 D = 20, n = 40 D = 40, standard rings), submitted 12:40:21 CET, done by
  15:17 CET, 6 s billed; V dbjiaid6p51s73cksitg (n = 40 D = 40, avoid ring), submitted 12:40:58 CET, 4 s billed.

## Results (`score_S.json`, `score_V.json`; signal a_j = mean over inputs of <z_in,j Z_j>)

| ring | mean signal | per-bit right | usable sites | whole string |
|---|---|---|---|---|
| n = 20, D = 20, standard (control) | +0.268 +- 0.003 | 0.634 | 20 / 20 | 0.084 |
| n = 40, D = 40, standard (holds [28, 29, 38, 49]) | +0.009 +- 0.002 | 0.504 | 0 / 40 | 0.000 |
| n = 40, D = 40, avoid ring | +0.020 +- 0.002 | 0.510 | 0 / 40 | 0.0003 |

**Judged:** the avoid ring's mean signal is below 0.05: **INCONCLUSIVE** by the note; Q1 and Q2 are not judged.
(For the record only: V - S = +0.011 +- 0.004; usable 0 -> 0; V per site -0.01 to +0.05.)

## Reported

- The forward computation reads at n = 20 after 20 layers (0.268) and is gone at n = 40 after 40 layers on both
  rings. The circuit's depth equals the ring length (its period), so n = 40 needs 40 layers, beyond kingston's
  readable depth (about 24 layers for the echo on healthy rings, 31 October). The test did not reach the question
  it asked.
