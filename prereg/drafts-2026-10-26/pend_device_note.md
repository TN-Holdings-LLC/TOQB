# Device test D1 (owner's go of 2026-10-26, the open plan's last 18 s): does the folded ring's signal survive on the device as the day's twin predicts? Fixed by SHA-256 and CET time before the fetch

**Question.** PSF-Zero a26's folded ring (item 50; TOQB `fold:rule`, pendants at n = 13) keeps on TOQB's models 0.6-0.8
of a random classifier's noiseless output at 16 layers (flows E, F). On 2026-10-24 the twin built from the day's
calibration predicted the zipper's kept signal on ibm_kingston (slope 0.83-0.89 against 0.87-0.88). Does the same hold
for the pendant schedule, which has never run on a device?

- **One arm, no comparison.** Only `fold:rule` is sent. The rehearsal on the 2026-10-24 twin
  (results/lam-rehearse-2026-10-26) found the pendants' lead over the zipper there to be 0.08-0.10 in lam (0.77
  against 0.66-0.69 at n = 13), which even 1 min of QPU time would decide in at most about half of the cases; the 18 s
  left are spent on whether the pendants' signal survives at all. A comparison is a later, separate test.
- **Precision.** With 64 inputs x 250 shots the slope's standard error is about 0.09-0.10 (the rehearsal's 48 and 96
  points bracket it): the test tells a twin-like device from a large loss (as Qiskit's circuits showed on 2026-10-24),
  not a difference of 0.1.
- **Model and inputs.** TOQB's ring classifier, n = 13, L = 16, model 0 of `toqb.lam_device` (seed 13016), its first 64
  random inputs; no training, no labels.
- **Device and twin.** ibm_kingston; the Target fetched at home just before (`toqb.s2rc_device fetch`); the circuits
  compiled for it by `fold:rule` and predicted by its twin (256 trajectories), all before submission. If `submit`
  moves the job to another device (its fixed order), the twin is of another device and that is reported.
- **Job.** 64 circuits x 250 shots, at most 12 s by the time model (`assemble --max-seconds 12`; 9.6 s predicted),
  dynamical decoupling and twirling off (`s2rc_device submit`).
- **Measure.** z_device ~ lam z_noiseless + delta over the 64 inputs (least squares, the slope's standard error from the
  residuals), against the twin's slope fixed before submission.
- **Rule.** **AGREE** if |lam_device - lam_twin| <= 2 SE (SE: the device fit's); **BELOW** if lam_device < lam_twin -
  2 SE; **ABOVE** if above. One verdict.
- **Prediction (not a rule).** AGREE (as the zipper did on 2026-10-24).
- **Reported beside it.** The device's correlation with the noiseless values; delta; the twin's slope for the zipper on
  the same inputs and Target (computed, not run), for scale; vanity (two-qubit gates, duration) and essential (lam;
  shots for a fixed precision as 1/lam^2).
- **Not claimed.** One job, one model, one device, one day; a random model is not a trained classifier.
