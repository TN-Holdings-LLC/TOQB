# Black stage 1 on ibm_kingston, 2026-10-31: the dead run's signal turns over (CROSSES ONCE), length MIXED, pairs NOT SEEN

- **Declaration:** `prereg/drafts-2026-10-31/black_stage1_note.md` (SHA-256 04737044...df0e), fixed 13:22 CET, TOQB
  5451784. Fetch 13:23:46 CET (calibration 13:13:30 CET, Target eba317f1...). Standard rings; the n = 40 D = 24 Z
  circuit byte for byte 30 October's (42376e3f..., the fifth run).
- **Job** dbitu9mne4hc73bfab6g, submitted 13:29:28 CET, 128 circuits x 1000 shots, 42.2 s predicted, **36 s billed**.

## Judged (`stage1_score.txt`, `stage1_score.json`)

- **P0:** PRESENT (the dead run holds the listed path [28, 29, 38, 49]).
- **J1 (block B = 38, 49-55, 59; Z over D):** +0.957, +0.799, +0.657, +0.518, +0.267, +0.060, -0.129, -0.204 at
  D = 2, 4, 6, 8, 12, 16, 20, 24: **CROSSES ONCE**. Rest of the ring: +0.961 ... +0.409, no crossing. Block A (3-7,
  17, 27-29, reported): +0.861 ... -0.036.
- **J2 (D = 12):** block |v| 0.518 against the rest's 0.767 (0.68 x): **MIXED**. Block mean vector (-0.007, +0.040,
  +0.267); transverse fraction 0.25 (rest 0.07). At D = 24: 0.215 against 0.411.
- **J3 (D = 12):** connected pair correlation block / rest: X 0.057 / 0.026, Y 0.096 / 0.048, Z 0.157 / 0.153:
  **NOT SEEN** (no basis above the rest by 3 SE and 0.05).
- **Outcome by the note:** J2 MIXED, reported; stage 2 only by the owner's decision. J1 is not OSCILLATES, so by the
  note the angle is not read from depth alone.

## Reported

- n = 20 control: Z +0.713 (D = 12), +0.343 (D = 24); |v| 0.344 at D = 24 (30 October +0.364).
- Post hoc, not judged (`posthoc_angle.py`, `.txt`): block / rest ratio +0.996, +0.853, +0.724, +0.593, +0.349,
  +0.089, -0.234, -0.500 over D = 2 ... 24; as a pure turn, arccos 0.09, 0.55, 0.76, 0.94, 1.21, 1.48, 1.81, 2.10 rad
  (about 0.07 rad per unit of D after D = 4). The signal goes through zero near D = 16-17 and keeps turning; most of
  it stays along Z (vx, vy small), so it is not a plain single-qubit tilt into the X-Y plane.
