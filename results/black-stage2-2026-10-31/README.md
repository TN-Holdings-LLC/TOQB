# Black stage 2 on ibm_kingston, 2026-10-31: the frame flip HELPS the dead block (+0.30 at D = 24), not RECOVERED; it costs the healthy n = 20 ring

- **Declaration:** `prereg/drafts-2026-10-31/black_stage2_note.md` (SHA-256 72aedffa...f8cc), fixed 13:41 CET, TOQB
  5174dc8. Fetch 13:44:09 CET (calibration 13:13:30 CET, Target 804d4da2...); the job ran on calibration 13:38:23
  CET. Standard rings; n = 40 D = 24 off byte-identical to 30 October (42376e3f...). `sim/`: the simulator checks
  quoted in the note; `dryrun/`.
- **Job** dbiu78nbipls73bdqi70, submitted 13:48:36 CET, 48 circuits x 1000 shots, 17.7 s predicted, **15 s billed**.

## Judged (`ff_score.txt`, `ff_score.json`; block = 38, 49-55, 59)

| n = 40 | block off | block flip | flip - off | rest off / flip |
|---|---|---|---|---|
| D = 24 (judged) | -0.197 | +0.098 | **+0.295 +- 0.007 HELPS**; RECOVERED: **NO** (0.28 x rest) | 0.389 / 0.354 |
| D = 12 (reported) | +0.272 | +0.550 | +0.278 +- 0.006 HELPS; 0.76 x rest | 0.752 / 0.722 |

- **Control n = 20, D = 24:** 0.350 off, 0.239 flip: **HURTS** (-0.110 +- 0.005).
- **Outcome by the note:** HELPS, not RECOVERED: part of the dead run is a coherent two-qubit phase error; the flip
  brings part back.

## Reported

- Per site, block, D = 12, off -> flip: 38 -0.36 -> +0.29, 49 -0.30 -> +0.25, 50 -0.31 -> +0.33, 51 -0.03 -> +0.42,
  52 +0.22 -> +0.62, 53-59 about 0.8 both. D = 24: -0.29 ... -0.15 -> +0.04 ... +0.22. The flip removes the
  inversion at every block site.
- Block A (3-7, 17, 27-29): D = 12 0.281 -> 0.301, D = 24 -0.043 -> -0.010: no clear change.
- The rest of the n = 40 ring loses 0.03-0.035; the n = 20 ring loses 0.11 (about a third of its signal).
