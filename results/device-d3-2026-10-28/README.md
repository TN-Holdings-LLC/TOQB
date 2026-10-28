# Device test D3 (2026-10-28): the kicked Ising ring at n = 20, L = 24 on ibm_kingston, against the day's twin

- **Declarations:** `prereg/drafts-2026-10-28/kising_device_d3_note.md` (558aa6cd…) and amendments 1-3 (the depth went
  50 → 24 → 50 → 24 before any run; amendment 3, ec85287e…, holds: L = 24, a check of the twin, not a new computation).
- **Fetch (home, 11:46:49 CET):** ibm_kingston, calibration 2026-10-28 11:36:52 CET, Target SHA-256 4c3a43e9…
  (`fetch.json`).
- **Pod step (TOQB 55642f1, psf-zero 2cc4f7b6):** 11:52:23 to 12:01:56 CET.
  - Build: 64 circuits, 480 two-qubit gates, 7.33 µs.
  - Twin: lam 0.247 ± 0.014 (correlation 0.912).
  - Rehearsal SE: 0.021 (fit's own 0.025).
  - Time model: 9.6 s.
  - Manifest written before submission: SHA-256 c5c46227….
- **Job:** `dbgte1hq260s73bu1aqg`.
  - Submitted 12:05:39 CET. The calibration at submission was 11:36:52, the twin's. The calibration in effect when
    the job ran was not read.
  - Queued until 12:25:14, finished 12:25:45 CET.
  - 64 circuits × 250 shots; dynamical decoupling and twirling off.
  - **7 s billed.**
- **Files:** `d3/` (times, build, rehearse, assemble, runs, job with manifest, circuits, raw counts, submission,
  lam_score) and `fetch.json`. The zip as received is `d3_result.zip`, SHA-256 2898b30f….

## Result

| | lam | SE | correlation | delta |
|---|---|---|---|---|
| device | **0.186** | 0.022 | 0.739 | +0.024 |
| twin (same calibration) | 0.247 | 0.014 | 0.912 | +0.004 |

- **Rule:** |lam_device − lam_twin| = 0.061 > 2 SE (0.043), so **BELOW**. lam_device = 0.186 > 2 SE, so **SIGNAL**.
- **Prediction:** "AGREE" did not hold. "SIGNAL" (the twin's lam above 3 rehearsal SE) held.
- **Vanity:** a signal kept on the device through 480 two-qubit gates (n = 20, L = 24), at 8.6 SE.
- **Essential:**
  - The device kept 0.75 of the twin's predicted slope.
  - Shots for a fixed precision are (0.247 / 0.186)² ≈ 1.8 times the twin's estimate.
  - D1 and D2 (n = 13, L = 16, 224 two-qubit gates) agreed with their twins. This is the first deeper point, and the
    first BELOW.

## Not established

- **Why the twin is optimistic here.** Candidates: crosstalk or leakage that the twin lacks, readout, and calibration
  drift during the 20 min queue. None was tested.
- **Whether the gap grows with depth.** D4 (L = 100) and D5 (same day, same fetch) add points.
- **Whether comparisons of schedules survive.** If both schedules shift alike, their order does; D5 part A tests this
  on the device.
