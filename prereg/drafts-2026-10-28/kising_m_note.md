# Flow M (owner's go of 2026-10-28, "1" to the workplace's direction (A), h = 0.6 chosen by the owner): real angles at depth with an exact answer, the kicked Ising ring at J = pi/4 on the same schedule as flow L. Fixed by SHA-256 and CET time before the run

**Why.** Flow L: the slope lam of random classifiers cannot be fitted past L about 24 (their noiseless outputs
collapse), and the Clifford proxy lam_C diverged from the real-angle lam (ratio 0.92, 0.75, 0.56 at L = 8, 16, 24).
`toqb/kising.py` (this commit) runs the kicked transverse-field Ising ring at J = pi/4 (one step: CZ ring, Z, RX(2h)),
written in the angle order of TOQB's classifier, so `fold:rule` compiles it with the same schedule. Its noiseless
<X_0> from X-basis product inputs is exact at any n and depth (free fermions; the workplace's ff_check.py and
ff_general.py, reproduced at home: 5.7e-16 and 2.1e-14). tests/test_kising.py (6 passed): the free-fermion value
equals Qiskit's Statevector (n = 5-8, h = 0.3, 0.6, 0.9), the circuit measures -<X_0>, and the compiled `fold:rule`
circuit keeps it exact with one template (n = 8, 13).

- **Device and arm.** `file:<target.pkl>`, ibm_kingston 2026-10-24 (SHA-256 3b939138…; stops if it differs); twin
  ("sim"); `fold:rule`, n = 20 (the 20-cycle of flows J, K and L).
- **Runs.** `python -m toqb.kising OUT --n 20 --L 8 16 24 50 100 --h 0.6 --P 24 --T 256 --seeds 0 1 2 3 --arms
  fold:rule --device file:<target.pkl>`: per (L, seed) 24 random X-basis product inputs (seed 8,000,000 + 1000 n + L
  + 100,000 seed), 256 trajectories each; lam by least squares z ~ lam z_exact + delta, as `fold_lam`.
- **Check (declared).** On the pod, before the run: `pytest tests/test_kising.py` must pass; else the run stops.
- **Noiseless spread (computed before this note, exact):** sd of z_exact over the 24 inputs, seeds 0-3: L = 8
  0.09-0.11; L = 16 0.24-0.29; L = 24 0.36-0.46; L = 50 0.12-0.21; L = 100 0.22-0.28. The slope can be fitted at
  every depth.
- **Comparison rule, per L in {8, 16, 24}** (with flow L's means: real-angle lam 0.934, 0.818, 0.696; lam_C 0.860,
  0.617, 0.392): **CLIFFORD-SIDE** if |mean lam_K - mean lam_C| < |mean lam_K - mean real lam|, else **CLASSIFIER-SIDE**.
  Reported with it: agreement within 2 SE (SE = sd of four / 2, combined as in flow L) with each.
  At L = 50 and 100: lam_K against lam_C (0.061 ± 0.010; -0.001 ± 0.004) within 2 SE, reported.
- **Reported only.** lam, delta, corr, rms per (L, seed); means and SE per L; per-layer factors; counts and duration;
  the time per cell.
- **Prediction (not a rule).** CLIFFORD-SIDE at L = 16 and 24. Basis: a CPU smoke run at n = 13 (P = 8, T = 32, seed
  0) gave lam_K 0.91 at L = 4 and 0.56 at L = 16, near flow L's n = 13 smoke for Clifford (0.54) and below its real
  angles (0.72). Expected ranges: L = 8 0.80-0.92, L = 16 0.50-0.72, L = 24 0.28-0.55, L = 50 below 0.15, L = 100
  |lam_K| below 0.1. Reading if it holds: real angles alone do not keep the classifier's signal; the evolved X_0 of
  this model is spread over Jordan-Wigner strings of high Pauli weight, like the Clifford case (not tested here).
- **Expected time on one H100:** about 2 h (per seed about 75 + 145 + 215 + 440 + 880 s, as flow L; the exact
  reference is instant).
- **Not claimed.** Free fermions are classically easy; no advantage claim. lam_K is this model's, not the classifier's.
  No device; one day's calibration; one placement; one h; n = 20 only.
