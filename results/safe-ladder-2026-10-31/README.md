# Safe ladder on ibm_kingston, 2026-10-31: stopped after round 1 without success; safe size of the day n = 40

- **Declaration:** `prereg/drafts-2026-10-31/safe_ladder_note.md` (SHA-256 67d10447...bae7), fixed 12:27 CET, TOQB
  c607888. Seed list `seed_list.json` (7b62a4ca...7301; `seed_list.txt`): [11, 10, 9], [28, 29, 38, 49],
  [87, 86, 85], [35, 19, 15, 14]. `dryrun/`: the build on the 11:39 CET fetch.
- **Round 1** (`round1/`): fetch 12:31:18 CET (calibration 12:20:43 CET, Target c6e079e6...); masked couplers (9, 10),
  (15, 19), (29, 38), (85, 86); job dbit85o1h92s73845bt0, submitted 12:42:17 CET, 144 circuits x 500 shots,
  27.6 s predicted, **22 s billed**.

## Judged (round 1; `round1/judge.txt`, `judge.json`)

| n | weak runs | L* (hz 0) | against n = 20 (24.07 +- 0.51) | verdict |
|---|---|---|---|---|
| 40 | none | 23.06 +- 0.36 | REACHED | **SAFE** |
| 48 | none | 22.26 +- 0.31 | SHORTER | NOT SAFE |
| 56 | none | 22.31 +- 0.30 | SHORTER | NOT SAFE |
| 64 | none | 21.30 +- 0.26 | SHORTER | NOT SAFE |
| 72 | none | 22.02 +- 0.25 | SHORTER | NOT SAFE |

**Stop (by the note):** the round adds no new path while sizes are NOT SAFE, so the list can no longer change those
rings. Outcome: stopped without success; the safe size of the day is **n = 40**; the shortfall at n = 48-72 is not a
weak run the scan can see.

## Reported

- No weak run on any ring (all sites usable at every size; ring medians 0.39-0.45).
- rho_E at D = 24: n = 20 0.399, 40 0.436, 48 0.424, 56 0.413, 64 0.397, 72 0.411.
- n = 72 beside earlier rings today (hz 0): standard ring, 30 October 14.6; around the defect list (clean depth,
  11:39 CET calibration) 20.4; around the strict list here 22.0. n = 40 here 23.1 (clean depth 24.2).
