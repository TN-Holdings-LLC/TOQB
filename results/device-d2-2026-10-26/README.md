# Device test D2, 2026-10-26: D1's test on ibm_fez (rule declared)

Declared in prereg/drafts-2026-10-26/pend_device_d2_note.md (SHA-256 1d54d1c9…, `0a53248`, 12:33 CET), before the fetch.

- **Fetch** (home, 12:44:55 CET): ibm_fez, operational, calibration 11:45:47 CET, Target SHA-256 8e42c5b8….
- **Build** (H100 pod, toqb `0a53248`, psf-zero `2bed479`): `fold:rule` at n = 13, L = 16, model 0, 64 random inputs;
  224 two-qubit gates, 7.98 us; the twin predicted lam 0.591 +- 0.012 (delta +0.003, correlation 0.987). Not run, for
  scale: the zipper, twin lam 0.432 +- 0.017 (464 two-qubit gates, 9.45 us; `scale/`).
- **Job:** manifest 12:50:16 CET (SHA-256 7a897e1f…); 64 circuits x 250 shots, 9.6 s predicted; submitted 12:52:35 CET,
  job `dbfjtvvsstms73fe0jc0`, done by 12:53:05; **7 s billed**. fez reported a calibration of 12:26:40 CET at
  submission and at the result, newer than the one the twin was built from (11:45:47): the twin is about 40 minutes
  older than the calibration under which the job ran (allowed by the owner's rule of 2026-10-20: a new calibration
  time alone does not stop a submission; no element of the job had failed).

## Result: AGREE

| | device | twin (fixed before) |
|---|---|---|
| lam | **0.504 +- 0.102** | 0.591 +- 0.012 |
| delta | +0.007 | +0.003 |
| correlation with the noiseless z | 0.531 | 0.987 |

|lam_device - lam_twin| = 0.087 <= 2 SE (0.204): **AGREE**, as predicted.

- With D1 (ibm_kingston, 0.904 +- 0.124 against 0.765): on two devices the folded ring kept its signal as each day's
  twin predicted, the device's lower value on fez (0.50) following fez's lower prediction (0.59 against kingston's
  0.77).
- **What a device user needs:** coarse tests (slope error about 0.1, set by the random model's small noiseless
  spread); the correlation (0.53) and the residual spread (0.064) are what 250 shots alone give (0.60, 0.063). No zipper
  on a device.
- Not claimed: one job per device, one model.

Files as in D1; the Target's pod path in `runs/` and `scale/` is written `<pod>/` (the manifest's run SHA-256 is that
of the record before this one-field change).
