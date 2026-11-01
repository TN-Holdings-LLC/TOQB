# Coverage days, day 2: ibm_kingston, 2026-11-01

- **Declaration:** `prereg/drafts-2026-10-31/coverage_days_note.md` (SHA-256 4941ddfa...d71d). Fetch 01:43:23 CET
  (calibration 2026-11-01 00:27:29 CET, Target a510608c...). Built 01:45-01:46 CET with day 1's `list_after.json`
  (LISTED [11, 10, 9], [28, 29, 38, 49], [87, 86, 85]); masked couplers (9, 10), (29, 38), (85, 86).
- **Jobs:** A dbj8p3hkdqps739039f0, submitted 01:49:18 CET, 9 s billed; B dbj8p7hffo6c73b95ang, submitted 01:49:34
  CET, 6 s billed. Both queued about an hour (done by 02:57 CET).
- All five circuits are byte for byte day 1's (`qpy_sha256.txt`): the same rings, the same list.

## Judged

| n | usable A (standard) | usable B (around the list) | C | signal on usable sites A / B | signal over the whole ring A / B |
|---|---|---|---|---|---|
| 40 | 22 / 40 | 40 / 40 | **WIDER** (+18) | 0.393 / 0.438 | 0.158 / 0.438 |
| 72 | 39 / 72 | 72 / 72 | **WIDER** (+33) | 0.382 / 0.416 | 0.205 / 0.416 |

- **P, day 2:** [28, 29, 38, 49] PRESENT; job A's n = 40 dead run is again exactly 3-7, 17, 27-29, 38, 49-55, 59.

## Reported

- n = 72, job A: dead runs of 15 sites (67-69, 78, 89-83, 96, 103-105) and 18 sites (26-31, 18, 11-3, 16, 23); both
  listed paths PRESENT. n = 20: no dead run (0.365). Job B: no dead run at either size.
- `list_after.json` (the list for day 3): the same three paths, seen in 4, 5 and 4 jobs.
