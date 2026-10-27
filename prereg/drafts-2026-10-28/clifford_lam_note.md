# Flow L (owner's go of 2026-10-28, "次の設計よろしく"; the workplace's option 1): the kept signal of the bare ring at depth, by Clifford eigenstate circuits, with a bridge to the real-angle lam. Fixed by SHA-256 and CET time before the run

**Why.** With random classifiers the noiseless outputs collapse with depth (n = 20, model 0: sd 0.169, 0.071, 0.0046,
0.0009 at L = 10, 20, 50, 100; cloud container, 2026-10-28), so the slope lam of `fold_lam` cannot be fitted at L >= 50.
`toqb.clifford_lam` (this commit; tests/test_clifford_lam.py: the noiseless <Z_0> equals the sign s exactly, for the
logical circuit at n = 4-7 and for the circuit compiled by `fold:rule` at n = 8 and 13, with one template per (n, L))
gives every rotation a random multiple of pi/2 and prepares the +1 eigenstate of U^dagger Z_0 U, so the noiseless value
is s = +1 or -1 at every depth and lam_C = mean of s * (noisy <Z_0>) needs no fit.

- **Device and arm.** `file:<target.pkl>`, ibm_kingston 2026-10-24 (SHA-256 3b939138…; the run stops if it differs);
  twin ("sim"); `fold:rule` at n = 20 (the ring itself on the 20-cycle of flows J and K).
- **Clifford runs.** `python -m toqb.clifford_lam OUT --n 20 --L 8 16 50 100 --P 24 --T 256 --seeds 0 1 2 3 --arms
  fold:rule --device file:<target.pkl>`: per (L, seed) 24 random Clifford circuits, 256 trajectories each.
- **Real-angle runs (the bridge).** `fold_lam` at n = 20, L = 8, models 0-3 (as flow J; noiseless reference on the
  CPU). At L = 16 flow J's rows are used; **check (declared):** the run first repeats flow J's n = 20, L = 16, model 0;
  if lam, q2 or us differs, the run stops.
- **Bridge rule, per L in {8, 16}.** With the four seeds' lam_C and the four models' lam (real angles): AGREE if the
  difference of the two means is at most 2 standard errors of that difference (each standard error the sd of its four
  values over 2); else DIFFER. Reported with both means.
- **Reported only.** lam_C per (L, seed) with its standard error and range over circuits; the mean over seeds per L;
  the per-layer factor (lam_C(L2)/lam_C(L1))^(1/(L2 - L1)) between consecutive depths; counts and duration.
- **Prediction (not a rule).** AGREE at L = 8. At L = 16 no prediction (a CPU smoke run at n = 13 with 8 circuits and
  32 trajectories gave lam_C 0.54 ± 0.08 against a real-angle 0.72 at L = 16, and 0.95 against 0.94 at L = 4). lam_C
  decreases with L, and at L = 100 its mean is more than 2 standard errors above 0.
- **Expected time on one H100:** about 2 h (the real-angle L = 8 runs about 15 min; the Clifford runs about 70, 140, 440
  and 880 s a seed at L = 8, 16, 50, 100).
- **Not claimed.** Clifford angles are not the classifier's angles (coherent errors and relaxation act differently on
  them; the bridge measures how much); no device; one day's calibration; one placement; n = 22 is not part of this run.
