# Depth sweep, the zipper against item 31: report only, with a rule fixed before the run (declared 2026-10-22)

The workplace's direction 1 (2026-10-22), with the owner's choices of 2026-10-22 about 13:25 CEST (new teachers 11,
12, 13 with seed 301; P 500 at every depth; the workplace's rule as written; on the same pod after the lam swap, then
stop). Report only: nothing is chosen from it, no device run follows from it, and adopting the zipper for a device
run needs its own pre-registration. Direction 2 (the full budget) is designed after this result.

- **Runs.** L 8, 12, 16, 20 x teachers 11, 12, 13 (angle 0.3, gap 0.2, 64 training and 500 test points; teachers 4 to
  9 were used before) x the two arms `psfai:template` (item 31, built in Rust and checked) and `psfai:template_zip`
  (the zipper, `toqb/ring_zip.py`, Python): 24 runs of design C (C0, seed 301, lr 0.4, 2,000 loops, T_pred 1,024,
  R 20,000), on the published calibration `snapshot:marrakesh`, verified on its stand-in (t12 0.3, over-rotation 0.01,
  ZZ 10 kHz). Then `toqb.undamp_run --final-only` on each (lam, delta from the twin on the 64 training inputs).
  Script `gpu/zip_depth.sh`, score `toqb.zip_depth_score`.
- **The rule (fixed now).** Per depth and teacher: d_i = CE_i(item 31) - CE_i(zipper), the per-point CE of the
  undamped stand-in's exact P(1) (no shots); two-sided Wilcoxon signed-rank, Holm over the depth's 3 teachers,
  alpha 0.01; WIN if the adjusted p < 0.01 and mean d > 0. A depth is **widened** if, in at least 2 of the 3 teachers,
  the zipper WINs and its trained model's noiseless test CE is also lower than item 31's.
- **Reported, not tested.** Per arm and depth: lam, the raw and undamped CE (exact and, raw, with shots), the
  noiseless CE, whether the mean undamped CE is at chance (>= ln 2 - 0.01); the device cost of the undamped readout:
  250 / lam^2 shots for the noise of 250 raw shots, and the QPU seconds of 500 test points at that count against 250
  (`toqb.s2rc_device.qpu_seconds`). Whether the undamp step reproduced the stand-in's shots is reported; the rule uses
  only the shot-free values, so a non-reproduction does not stop the score.
- **Not claimed.** One seed; the stand-in is TOQB's own noise model on a 9-day-old calibration ("vanity" side). Today's
  device day showed the twin under-stating PSF's signal on the device by 2 to 2.7 times, so the stand-in's depth at
  which the CE reaches chance is not the device's.
- **Seen before fixing.** The lam swap (`toqb.lam_swap`, 13:28-13:30 CEST; `zip_depth` does not use it) was complete
  before this note was fixed. L 8: lam follows the circuit (item 31's circuit 0.334 / 0.337, the zipper's 0.366 /
  0.369, for either model). L 16: both matter (item 31's model on item 31's circuit 0.268, on the zipper's 0.183; the
  zipper's model on item 31's circuit 0.182, on the zipper's 0.158). Nothing in this design was changed by it.
- **Time and cost (estimate).** On an H100, PAR 4: about 2 to 3 h of training (the zipper comparison's 4 runs at L 8
  and 16 took 21 min), then about 15 min of undamping; about $10 to 12.
