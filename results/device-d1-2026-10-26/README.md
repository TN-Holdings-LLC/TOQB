# Device test D1, 2026-10-26: the folded ring's signal on ibm_kingston against the day's twin (rule declared)

Declared in prereg/drafts-2026-10-26/pend_device_note.md (SHA-256 a751e252…, `2fbe135`, 11:35 CET), before the fetch.

- **Fetch** (home): ibm_kingston, operational, calibration 2026-10-26 11:01:44 CET, Target SHA-256 6779a003….
- **Build** (H100 pod, toqb `2fbe135`, psf-zero `62ae3c2`): `fold:rule` at n = 13, L = 16, model 0 (seed 13016), 64
  random inputs; 224 two-qubit gates, 9.16 us; the twin of the fetched Target predicted lam 0.765 +- 0.011 (delta
  +0.003, correlation 0.993). Not run, for scale: the zipper on the same inputs and Target, twin lam 0.613 +- 0.016
  (464 two-qubit gates, 10.76 us; `scale/`).
- **Job:** manifest written 11:45:52 CET before submission (SHA-256 51be3611…); 64 circuits x 250 shots; predicted
  9.6 s. Submitted 11:48:10 CET to ibm_kingston, which took it under the fetched calibration; job
  `dbfivq0m94ac738tldc0`, done before 12:25:42 CET; **7 s billed**. The calibration in effect when the result was read
  was 12:09:30 CET: the job may have run before or after that recalibration (not known from the record).
- Dynamical decoupling and twirling off.

## Result: AGREE

| | device | twin (fixed before) |
|---|---|---|
| lam (slope on the noiseless z) | **0.904 +- 0.124** | 0.765 +- 0.011 |
| delta | +0.001 | +0.003 |
| correlation with the noiseless z | 0.680 | 0.993 |

|lam_device - lam_twin| = 0.139 <= 2 SE (0.248): **AGREE**, as predicted.

- **Vanity:** the folded ring's first device run kept its signal as its twin said (0.90 against 0.77).
- **What a device user needs:** the test is coarse. Random models at L = 16 spread their noiseless outputs over only
  0.08 (sd), so 250 shots leave the slope uncertain by +-0.12; it rules out a large loss (below about 0.52) such as
  Qiskit's circuits showed on 2026-10-24, not a difference of 0.1. The device's correlation of 0.68 is what shot noise
  alone gives at this spread (expected 0.70). The residual spread (0.078) is a little above shot noise (0.063).
- **Not claimed:** no comparison with the zipper on the device (rehearsal: such a test would be a gamble at this size,
  results/lam-rehearse-2026-10-26); one job, one model, one device, one day.

Files: `job/` (manifest, circuits, raw_counts.json, submission.json, lam_score.json), `runs/`, `scale/`, `times.txt`,
`build.txt`, `assemble.txt`. In `runs/` and `scale/` the Target's pod path in the "device" field is written `<pod>/`;
the manifest's run SHA-256 (028dc0f3…) is that of the record before this one-field change.
