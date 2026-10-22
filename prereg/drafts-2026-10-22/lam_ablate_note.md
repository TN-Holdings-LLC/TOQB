# Which noise source sets the shrink lam? Report only (declared 2026-10-22, before any output)

Owner, 2026-10-22 about 14:02 CEST: test the explanations instead of leaving them as hypotheses. The lam swap
(`results/lam-swap-2026-10-22`) is repeated on five twins built from `snapshot:marrakesh`: the full one, and one with
each of the twin's four noise sources switched off: two-qubit depolarizing (CZ error 0), one-qubit depolarizing (sx, x
error 0), thermal relaxation (T1 = T2 = 1,000 s), readout (error 0). Failed elements stay failed. L 8 and 16; each model
(item 31's, the zipper's) on each circuit; (lam, delta, fit rms) as `toqb.lam_swap`. Tool `toqb.lam_ablate`. It stops
if a circuit differs between twins, or if the full twin's lam differs from the lam swap's.

Questions it answers (on the twin only; nothing is chosen from it):
- At L 16, which source makes the zipper's circuit shrink more than item 31's (0.183 against 0.268 with item 31's
  model), though it has 25 % fewer CZ and is 31 % shorter: the source whose removal closes the gap.
- Which source makes lam depend on the model on one circuit (not a global depolarizing channel): the source whose
  removal makes the model's rows equal.
- Which source makes item 31's circuit fit a single lam worse (fit rms 0.075 to 0.087 against the zipper's 0.024 to
  0.028), and which gives item 31's offset delta (+0.05 to +0.07; expected: relaxation, T1's pull towards |0>).

Not claimed: one seed, one teacher, TOQB's twin on the 2026-10-13 calibration; the device's noise differs (today the
twin under-stated PSF's signal by 2 to 2.7 times). The depth sweep (`zip_depth_note.md`) is not affected.
