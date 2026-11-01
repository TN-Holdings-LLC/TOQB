# Fix repeat on ibm_kingston, 2026-11-01: the two-qubit flip at 27, 29 fixes the dead run again (PERSISTS)

- **Declaration:** `prereg/drafts-2026-11-01/fix_repeat_note.md` (SHA-256 935d3a5d...f386), fixed 03:04 CET, TOQB
  af76d3e. Fetch 03:05:48 CET (calibration 02:53:40 CET, Target f266a3ba...). Off and B3 circuits byte-identical to
  31 October's (off at D = 24: 42376e3f...). `dryrun/`.
- **Job** dbj9v2onceqs73ajj0e0, submitted 03:10:18 CET, queued until about 06:06 CET; 48 circuits x 1000 shots,
  17.7 s predicted, **15 s billed**.

## Judged (D = 24; `ff_score.txt`, `ff_score.json`; block = 38, 49-55, 59)

| arm | block | block - off | rest - off |
|---|---|---|---|
| off | -0.185 | | |
| flip at 27, 29 (B3) | +0.112 | **+0.298 +- 0.007 HELPS** (31 October +0.322) | **+0.005 +- 0.004 NO COST** |
| global flip | +0.096 | +0.281 HELPS | -0.108 |

**PERSISTS.** By the note: the two-qubit flip at 27, 29 fixes the dead run on a second day with the same circuit; a
repair entry (path -> flipped qubits) can be kept in the list like a dead path.

## Reported

- D = 12: B3 +0.281 (block 0.559 against rest 0.741, 0.75 x), global +0.252 (rest -0.051).
- RECOVERED (block >= 0.8 x rest): no (D = 24 B3 0.30 x).
- Per site, D = 12, off -> B3: 38 -0.36 -> +0.28, 49 -0.30 -> +0.27, 50 -0.27 -> +0.34, 51 +0.02 -> +0.40,
  52 +0.24 -> +0.63.
- The global flip cost the rest more than on 31 October (-0.108 against -0.050 at D = 24).
