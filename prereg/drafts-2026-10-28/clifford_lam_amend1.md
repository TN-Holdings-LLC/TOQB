# Flow L, amendment 1 (owner's go of 2026-10-28, "では、足しましょう２４"; proposed by the workplace, scoped at home): one more bridge point at L = 24. Fixed by SHA-256 and CET time before it runs

**Why.** The bridge of the main run (clifford_lam_note.md, SHA-256 1afcd16b…) gave DIFFER at L = 8 (real-angle mean
0.934, lam_C 0.860, ratio 0.92) and at L = 16 (0.818 from flow J, reproduced exactly by the declared check; lam_C
0.617, ratio 0.75). The ratio is not constant. A third depth shows how it falls. L = 24 is the deepest depth where
the real-angle slope can still be fitted (noiseless sd about 0.05 at L = 24 by interpolation of 0.071 at L = 20 and
0.0046 at L = 50; expected standard error of lam about 0.03). L = 32 (expected error about 0.06) is not run.

- **Same as the main run:** device file (kingston 2026-10-24 Target, SHA-256 3b939138…; stops if it differs), twin,
  `fold:rule`, n = 20, P = 24, T = 256; real-angle models 0-3 by `fold_lam` with the noiseless reference on the CPU;
  Clifford seeds 0-3 by `clifford_lam` (circuits drawn with the seed formula of the main run at L = 24).
- **Runs** (after the main run's "all done", in a new folder): `fold_lam --n 20 --L 24 --models-seed 0 1 2 3`, then
  `clifford_lam --n 20 --L 24 --seeds 0 1 2 3`.
- **Bridge rule at L = 24:** as in the main run (AGREE if the difference of the means is at most 2 standard errors of
  the difference, each the sd of four over 2; else DIFFER).
- **Reported only.** The ratio mean lam_C / mean lam at L = 8, 16, 24; the per-layer factors of both; reading of the
  ratio at L = 24: 0.75 or more, the ratio falls slowly and lam_C is a near guide to lam; below 0.70, at depth lam_C is
  only a lower side; between, neither.
- **Prediction (not a rule).** DIFFER. Real-angle lam 0.66-0.80 (per-layer factor 0.984 of L = 8 to 16 kept: 0.72);
  lam_C 0.30-0.48 (log-interpolation of L = 16 and the first three L = 50 seeds: 0.36); ratio 0.40-0.70.
- **Expected time on one H100:** about 45 min (real-angle about 8 min a model with the CPU reference; Clifford about
  215 s a seed).
- **Not claimed.** As the main run; the reading of the ratio is a description of three depths, not a model of it.
