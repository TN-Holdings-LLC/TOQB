# Black stage 3 on ibm_kingston, 2026-10-31: the flip only around the block does nothing (NO EFFECT, LOSES); the global flip helps again

- **Declaration:** `prereg/drafts-2026-10-31/black_stage3_note.md` (SHA-256 11f59455...9f1a), fixed 13:58 CET, TOQB
  80dc84a. Fetch 14:52:30 CET (calibration 14:00:07 CET, Target be5df9d5...). Standard n = 40 ring; off at D = 24
  byte-identical to 30 October; flip positions physical 38, 50, 52, 54, 59 as declared. `sim/`, `dryrun/`.
- **Job** dbiv7p8nceqs73aitbo0, submitted 14:57:59 CET, 48 circuits x 1000 shots, 17.7 s predicted, **15 s billed**.

## Judged (D = 24; `ff_score.txt`, `ff_score.json`)

| block (38, 49-55, 59) | off | local flip | global flip |
|---|---|---|---|
| D = 24 | -0.180 | -0.188 | +0.105 |
| D = 12 | +0.267 | +0.281 | +0.538 |

- **L1:** block, local - off -0.007 +- 0.007: **NO EFFECT**.
- **L2:** rest, local - off -0.009 +- 0.004: **COSTS** (by 2 SE; small).
- **L3:** block, local - global -0.293 +- 0.007: **LOSES**.
- **Outcome by the note:** the stage 2 gain is not reproduced locally; the local flip is not used.

## Reported

- The global flip repeats stage 2: block +0.285 +- 0.007 at D = 24 (stage 2 +0.295), +0.271 at D = 12; rest -0.043.
- Per site at D = 12, off / local / global: 38 -0.39 / -0.36 / +0.29; 49 -0.30 / -0.28 / +0.25; 50 -0.29 / -0.27 /
  +0.32: the local flip leaves the inversion as it is.
- Reading (not tested): every coupler touching the block was flipped in the local arm, so the error the global flip
  cancels does not sit on those couplers; it sits on couplers the global flip covers and the local one does not
  (elsewhere on the ring), and its effect reaches the block through the circuit (Lemma 2).
