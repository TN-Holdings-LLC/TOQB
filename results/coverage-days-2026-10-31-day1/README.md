# Coverage days, day 1: ibm_kingston, 2026-10-31

- **Declaration:** `prereg/drafts-2026-10-31/coverage_days_note.md` (SHA-256 4941ddfa...d71d), fixed 11:29 CET, TOQB
  e4486a9. Fetch 11:35:01 CET (calibration 10:56:15 CET, Target e5267212...). Built 11:36-11:37 CET with the day-1
  list (the replay list, SHA-256 b1fe9fe7...6765; LISTED [11, 10, 9], [28, 29, 38, 49], [87, 86, 85]); masked
  couplers (9, 10), (29, 38), (85, 86).
- **Jobs:** A (standard rings, n 20, 40, 72; 24 circuits) dbisb18hoj4c73b6rqu0, submitted 11:40:05 CET, 9 s billed;
  B (rings placed around the list, n 40, 72; 16 circuits) dbisb3g1h92s73843qk0, submitted 11:40:16 CET, 6 s billed.
- The n = 40 standard circuit is byte for byte the one of 30 October (QPY SHA-256 42376e3f...), the fourth run of it.
- Job B's rings: n = 40 leaves 28-29-38 and goes 29-30-31-32-33-39-53; n = 72 contains none of the three paths.

## Judged

| n | usable A (standard) | usable B (around the list) | C | signal on usable sites A / B | signal over the whole ring A / B |
|---|---|---|---|---|---|
| 40 | 22 / 40 | 40 / 40 | **WIDER** (+18) | 0.410 / 0.441 | 0.175 / 0.441 |
| 72 | 38 / 72 | 72 / 72 | **WIDER** (+34) | 0.384 / 0.346 | 0.205 / 0.346 |

- **P, day 1:** [28, 29, 38, 49] PRESENT. Job A's n = 40 dead run is the same 18 qubits as on 30 October
  (3-7, 17, 27-29, 38, 49-55, 59).

## Reported

- n = 72, job A: two dead runs, 15 sites (67-69, 78, 89-83, 96, 103-105; centre [88, 87, 86, 85]) and 19 sites
  (26-31, 18, 11-3, 16, 23, 22; centre [11, 10, 9, 8]); both listed paths PRESENT.
- n = 20, job A: no dead run (signal 0.390; 30 October 0.364).
- Job B: no dead run at either size.
- `list_after.json` (the list for day 2): the three paths LISTED, now seen in 3, 4 and 3 jobs, last on this day.
- Files: `fetch.json`, `fetch_masked/fetch.json`, build logs, `runs_A|B/` (records; circuits by SHA-256 in
  `qpy_sha256.txt`), `job_A|B/` (manifest, submission, `raw_counts.json.gz`), `coverage.json|txt`, `ingest.txt`,
  `list_after.json`, `list_after_status.txt`.
