# Device test D4 (2026-10-28): the kicked Ising ring at n = 20, L = 100 (2000 two-qubit gates) on ibm_kingston

- **Declaration:** `prereg/drafts-2026-10-28/kising_device_d4_note.md`, SHA-256 ea7d872d… (ca1a78f, 12:17 CET).
- **Pod step (TOQB ca1a78f, psf-zero 2cc4f7b6):** 12:20:17 to 12:59:47 CET. D3's fetch was used: calibration
  11:36:52 CET, Target SHA-256 4c3a43e9….
  - Build: 64 circuits, 2000 two-qubit gates, 23.44 µs.
  - Twin: lam 0.028 ± 0.008 (correlation 0.40).
  - Rehearsal: SE 0.011 (fit's own 0.014).
  - Time model: 39.9 s.
  - Manifest written before submission: SHA-256 b193c5f3….
- **Job:** `dbguaiote5oc738ivagg`.
  - Submitted 13:06:35 CET; ran 13:06:37 to 13:07:37 (no queue).
  - 64 circuits × 2000 shots; dynamical decoupling and twirling off.
  - **38 s billed.**
- **Calibration:** at submission kingston reported 12:58:45 CET, newer than the twin's 11:36:52. The twin is of the
  earlier calibration (stated in the declaration).
- **Files:** `d4/` (times, build, rehearse, assemble, runs, job with manifest, circuits, raw counts, submission,
  lam_score). The zip as received is `d4_result.zip`, SHA-256 7411785a….

## Result

| | lam | SE | correlation | delta |
|---|---|---|---|---|
| device | **0.0223** | 0.0111 | 0.248 | +0.012 |
| twin (11:36:52 calibration) | 0.0282 | 0.0081 | 0.402 | −0.000 |

- **Rule:**
  - |lam_device − lam_twin| = 0.006 ≤ 2 SE (0.022), so **AGREE**.
  - lam_device / SE = 2.01 > 2, so **SIGNAL**, but only by 0.01 SE. This is a formal result at the edge, not a robust
    one.
- **Prediction:**
  - "AGREE" held.
  - SIGNAL was predicted only if the twin's lam exceeded 3 rehearsal SE. It did not (0.028 against 0.033), so no SIGNAL
    was predicted.
- **Vanity:** a slope resolved (2.0 SE) after 2000 two-qubit gates on the device.
- **Essential:**
  - Signal kept at L = 100 is about 0.02 of the noiseless output.
  - Reading it to ±0.01 took 128,000 shots and 38 s of QPU time.
  - The 25 % gap of D3 (L = 24) cannot be resolved at this precision.

## Not established

- **Whether the slow tail of flow M is what the device keeps.** The signal is at the 2 SE edge.
- **Whether the twin's optimism at L = 24 grows or shrinks with depth.** This point is too imprecise to say.
