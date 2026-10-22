# The undamped readout on the zipper comparison's four runs: report only (declared 2026-10-22, before any output)

**Proposed by the workplace (2026-10-22), run at the owner's go-ahead.** `toqb.undamp_run --final-only` on the four
records of `results/zip-compare-2026-10-22/runs/` (item 31 and zipper, L 8 and L 16, seed 301, teacher 4, angle 0.3).
(lam, delta) come from each run's own twin on its 64 training inputs against the exact noiseless model (no labels, no
stand-in data); the stand-in's job is redrawn with the run's own seed and checked against the record's raw CE.

- **Reported, per run:** lam, delta; the undamped stand-in CE and accuracy beside the raw ones; whether the undamped
  stand-in CE falls in the undamped prediction's 99 % interval; and the mean |z| of the trained model's noiseless output
  on the test points (W12's check: is a small output the model's own or the noise's).
- **Main figure:** the undamped stand-in CE, zipper against item 31, per depth.
- **Not claimed.** One seed and one teacher per depth; the stand-in is TOQB's own noise model. A small lam amplifies
  the shots' noise, which can make the undamped CE worse; that is reported as it comes. A pre-registered match (W8's
  rules, fresh seeds and teachers) would follow only if the owner asks.
