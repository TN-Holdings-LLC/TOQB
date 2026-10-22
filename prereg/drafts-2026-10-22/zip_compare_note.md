# The zipper against item 31 on the device day's plans: report only (declared 2026-10-22, before the run)

**Owner, 2026-10-22: "try it small".** Report only: nothing is chosen from it, and the device day's job (C r9) is not
touched. Adopting the zipper for a device run needs its own pre-registration.

- **Schedule.** The workplace's prototype P1 (2026-10-22): the "zipper", one more candidate in a22's ring template,
  chosen by item 84's rule among N2, item 31 and the zipper (`toqb/ring_zip.py`, copied unchanged; arm
  `psfai:template_zip`, Python only). Against `psfai:template` (today's template: item 31), built in Rust and
  checked as on the day.
- **Plans.** The device day's own two plans (C r9: seed 301, C0, L 8 with P 150 and L 16 with P 500, N 250, lr 0.4,
  2,000 loops, T_pred 1,024, R 20,000), with the device set to `snapshot:marrakesh` (the same published calibration
  as the day's snapshot folder) and `verify` true: after the prediction, the stand-in (the snapshot with its
  deliberate deviations: T1 / T2 scaled, over-rotation, ZZ) plays the device. 4 runs (2 arms x 2 depths).
- **Reported, per arm and depth:** the stand-in CE and accuracy; whether the stand-in CE falls in the twin's 99 %
  interval; the twin's predicted CE; CZ count and duration on the snapshot; as `summary.txt` of `gpu/zip_compare.sh`.
- **Not claimed.** One seed and one task per depth: a difference is reported as seen, without a test. The stand-in is
  TOQB's own noise model, not the device ("vanity" side); the device-side effect stays unmeasured until a device run.
- **Side benefit, stated now.** The `psfai:template` runs repeat the day's training on the same calibration and seed,
  so their stand-in CE is a rehearsal of the day's own PSF models (reported, not used for the day's scoring).
