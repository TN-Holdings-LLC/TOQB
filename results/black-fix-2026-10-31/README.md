# Black fix on ibm_kingston, 2026-10-31: a frame flip on 3, 5, 7, 27, 29 is a per-path fix (F1, F2 hold); it is carried by 27 and 29 alone (F3)

- **Declaration:** `prereg/drafts-2026-10-31/black_fix_note.md` (SHA-256 0c72bbe8...165f), fixed 15:30 CET, TOQB
  aff21a8. Fetch 15:32:18 CET (calibration 14:58:44 CET, Target a5fe27ba...). Standard n = 40 ring; off at D = 24
  byte-identical to 30 October; A2 the declared qubits. `dryrun/`.
- **Job** dbivq656p51s73cjp9d0, submitted 15:37:14 CET, 80 circuits x 1000 shots, 27.5 s predicted, **23 s billed**.

## Judged (D = 24; `ff_score.txt`, `ff_score.json`; block = 38, 49-55, 59)

| arm | flipped qubits | block | block - off | rest - off | block - global |
|---|---|---|---|---|---|
| off | - | -0.193 | | | |
| global | every even position | +0.096 | +0.289 HELPS | -0.050 | |
| A2 | 3, 5, 7, 27, 29 | +0.124 | **+0.317 +- 0.007 HELPS** | **+0.010 +- 0.004 NO COST** | **+0.028 KEEPS** |
| A3 | 3, 5, 7 | -0.189 | +0.004 NO EFFECT | -0.024 COSTS | -0.285 LOSES |
| B3 | 27, 29 | +0.129 | **+0.322 +- 0.007 HELPS** | +0.008 NO COST | +0.033 KEEPS |

- **F1** holds (A2 HELPS and KEEPS); **F2** holds (NO COST); **F3: CARRIED BY B3** (B3's gain 1.02 x A2's, A3's
  0.01 x).
- **Outcome by the note:** a frame flip on five qubits (3, 5, 7, 27, 29) is a per-path fix for kingston's dead run:
  the global flip's gain without its cost; the smaller set that carries it is 27, 29 (couplers (17, 27), (27, 28),
  (28, 29), (29, 38)).

## Reported

- D = 12: A2 +0.268 (block 0.538 against rest 0.775), B3 +0.285 (0.555 / 0.768), A3 -0.015, global +0.258.
- RECOVERED (block >= 0.8 x rest): no arm at D = 24 (best B3, 0.30 x); at D = 12 B3 reaches 0.72 x.
- Per site, D = 12, off -> B3: 38 -0.35 -> +0.26, 49 -0.30 -> +0.25, 50 -0.27 -> +0.34, 51 -0.02 -> +0.43,
  52 +0.22 -> +0.63. Block A (3-7, 17, 27-29) is not lifted by any arm (D = 24: -0.047 off, -0.009 B3).
- With stage 3 (a flip at 38, 50, 52, 54, 59 covering (29, 38) did nothing), the cancelled error sits on (17, 27),
  (27, 28) or (28, 29) (not tested which).
