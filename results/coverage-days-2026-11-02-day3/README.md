# Coverage days, day 3: ibm_kingston, 2026-11-02, and the three-day verdict

- **Declaration:** `prereg/drafts-2026-10-31/coverage_days_note.md` (SHA-256 4941ddfa...d71d). Fetch 11:26:08 CET
  (calibration 11:19:47 CET, Target bade99bf...). Built 11:28-11:29 CET with day 2's `list_after.json` (LISTED
  [11, 10, 9], [28, 29, 38, 49], [87, 86, 85]); masked couplers (9, 10), (29, 38), (85, 86).
- **Jobs:** A dbk6cq56p51s73cm1n8g, submitted 11:31:02 CET, 9 s billed; B dbk6d0onceqs73al975g, submitted 11:31:30
  CET, 6 s billed. Both done by 11:33 CET.
- All five circuits are byte for byte day 2's (`qpy_sha256.txt`), and so day 1's: the same rings, the same list.
- The jobs were sent with the VPN on by mistake (the procedure says off). They were accepted and ran normally; the
  results are kept.

## Judged (day 3)

| n | usable A (standard) | usable B (around the list) | C | signal on usable sites A / B | signal over the whole ring A / B |
|---|---|---|---|---|---|
| 40 | 22 / 40 | 40 / 40 | **WIDER** (+18) | 0.405 / 0.429 | 0.169 / 0.429 |
| 72 | 54 / 72 | 72 / 72 | **WIDER** (+18) | 0.322 / 0.411 | 0.237 / 0.411 |

- **P, day 3:** [28, 29, 38, 49] PRESENT; job A's n = 40 dead run is again exactly 3-7, 17, 27-29, 38, 49-55, 59.

## The three-day verdict (by the note)

| day | C n = 40 | C n = 72 | P |
|---|---|---|---|
| 1 (31 Oct) | WIDER (22 -> 40) | WIDER (38 -> 72) | PRESENT |
| 2 (1 Nov) | WIDER (22 -> 40) | WIDER (39 -> 72) | PRESENT |
| 3 (2 Nov) | WIDER (22 -> 40) | WIDER (54 -> 72) | PRESENT |

- **C: WIDER in 6 of 6, NARROWER in none.** Sentence fixed in advance: *placing around a self-measured list widens the
  usable part of the device; the list joins the procedure as the self-checked category, always labelled.*
- **P: PERSISTENT (3 of 3).** Sentence fixed in advance: *the defect stays for days without showing in the
  calibration; a list with a multi-day expiry is sound.*

## Reported

- n = 72, job A: one dead run of 18 sites (26-31, 18, 11-3, 16, 23): [11, 10, 9] PRESENT. The 15-site run of day 2
  (67-69, 78, 89-83, 96, 103-105) is gone today: [87, 86, 85] ABSENT. That path stays LISTED (last seen 1 November,
  expiry 7 days); it was avoided today with nothing to avoid.
- n = 20: no dead run (0.371). Job B: no dead run at either size.
- The n = 40 dead run has now been the same 18 qubits on 30 October, 31 October, 1 November and 2 November.
- `list_after.json`: [28, 29, 38, 49] seen in 6 jobs, [11, 10, 9] in 5, [87, 86, 85] in 4 (not today).
- **Stop.** Three days were declared; the test ends here.
