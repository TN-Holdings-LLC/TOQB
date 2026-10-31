# Clean depth on ibm_kingston, 2026-10-31: n = 40 REACHED n = 20's depth (3 of 3), n = 72 SHORTER (3 of 3); mixed

- **Declaration:** `prereg/drafts-2026-10-31/clean_depth_note.md` (SHA-256 2c45ee4b...05b4), fixed 11:55 CET, TOQB
  11e6620. Fetch 11:58:03 CET (calibration 11:39:20 CET, Target 01483d1c...). Masked by
  `results/coverage-days-2026-10-31-day1/list_after.json` (couplers (9, 10), (29, 38), (85, 86)). Self-checked
  category. Not added to the coverage-days list.
- **Job** dbisog8hoj4c73b6sda0, submitted 12:08:51 CET, done 12:10:28 CET; 216 circuits x 500 shots; 39.9 s
  predicted, **32 s billed**. Options off. Rings: n = 20 the standard ring; n = 40, 72 day 1's job B rings (no listed
  path).

## Judged (L* in layers, fit over D = 24, 50, 100; `judge.py`, `judgement.json`)

| hz | n = 20 (control) | n = 40 | n = 72 |
|---|---|---|---|
| 0 | 23.9 +- 0.5 | 24.2 +- 0.4 **REACHED** | 20.4 +- 0.2 **SHORTER** |
| 0.1 | 24.7 +- 0.5 | 24.6 +- 0.4 **REACHED** | 20.8 +- 0.2 **SHORTER** |
| 0.3 | 24.1 +- 0.5 | 24.2 +- 0.3 **REACHED** | 20.4 +- 0.2 **SHORTER** |

Overall: **mixed** (by the note, no general sentence).

## Reported

- Beside 30 October (standard rings, rerun): n = 40 13.0-16.0 -> 24.2-24.6 here; n = 72 14.6-16.0 -> 20.4-20.8
  here (30 October's live sites after masking: 19.7-21.3 and 18.6-21.2); n = 20 21.9-22.3 -> 23.9-24.7.
- rho_E at D = 24: n = 20 0.40-0.42, n = 40 0.46-0.48, n = 72 0.38.
- No dead run on any ring (`coverage.txt`: usable 20/20, 40/40, 72/72).
- Post hoc, not judged: the n = 72 ring's weakest stretch is 35, 19, 15, 14 (signal 0.13-0.18 at D = 24, above the
  0.12 line); the other n = 72 sites and all n = 20, 40 sites are 0.21 or more (n = 40, 20: 0.35 or more).
