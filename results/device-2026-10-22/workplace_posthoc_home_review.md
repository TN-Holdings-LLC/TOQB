# Home's review of the workplace's post hoc notes (2026-10-23, `workplace_posthoc_2026-10-23.md`, as received)

Post hoc only, as the notes say.

- **§1 checked at home, exactly.** Device z on twin z per point (clbit 0, `raw_counts.json.gz`, `manifest.json`
  twin_p1): scale / offset / correlation / residual rms = PSF L 8 1.54 / +0.065 / 0.970 / 0.087; PSF L 16 2.30 /
  +0.041 / 0.969 / 0.078; Qiskit L 16 1.00 / +0.023 / 0.964 / 0.066; Qiskit L 8 0.63 / +0.223 / 0.721 / 0.200; raw CE
  reproduced (0.5087, 0.5716, 0.5867, 0.6613).
- **§2: the arithmetic is right, the sensitivity is not.** (1 - 4r/3)^(28 L) treats every CZ error as reaching the
  read-out signal. The twin's own sensitivity is much weaker: with the CZ error switched off the twin's lam rises only
  by 1 / 0.427 (L 8) and 1 / 0.331 (L 16) (`results/lam-ablate-2026-10-22`, item 31's model and circuit), where the
  naive product gives about 1 / 0.10 and 1 / 0.0098. Scaling the twin's measured CZ factor by the drift (mean CZ error
  0.0077 to 0.0061, x 0.79) predicts 1.19 x at L 8 and 1.26 x at L 16, against 1.54 and 2.30 observed. So the drift
  probably explains a part, not most; a pessimistic noise model remains likely. Rough (mean errors; the couplers are
  used unequally: 48-49, used most, moved 0.0202 to 0.0196). The decisive test is the one proposed: the twin rebuilt
  on the day's calibration.
- **§3 agreed,** with its caveat (in-sample). The correlation guard is a good rule; its threshold is to be fixed
  before the run (with 64 training inputs and 250 shots the correlation itself is noisy; 0.72 against 0.96-0.97 here).
- **§4: the zipper's cost relative to item 31 does not shrink by a common scale.** If both arms' lam are scaled by the
  same device factor, the ratio of shots stays (lam_item31 / lam_zipper)^2: 2.2 at L 16 and 4.8 at L 20 (twin). Only
  a device measurement of both arms shows whether the ratio itself differs on the device.
- **§5 agreed;** add the QPU budget check (IBM's remaining time) to the design.
