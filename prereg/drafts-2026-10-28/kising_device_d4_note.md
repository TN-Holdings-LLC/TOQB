# Device test D4 (owner's go of 2026-10-28, "L＝１００の準備して"): does the device keep the kicked Ising ring's slow tail at L = 100 (2000 two-qubit gates), where flow M's twin kept lam_K 0.046 and random Clifford circuits kept nothing? Fixed by SHA-256 and CET time before submission

**Why.** Flow M (2026-10-24 twin) gave lam_K 0.046 +- 0.010 at L = 100, while lam_C of random Clifford circuits was
-0.001 +- 0.004 (flow L). The workplace's noisy free-fermion recursion (reproduced at home) explains a slow tail by
weight-2 conserved modes. Not predicted before flow M. D4 asks whether the device shows it.

- **Workload.** As D3 (`toqb.kising`, n = 20, h = 0.6, `fold:rule`, seed 0, the first 64 inputs of flow M's seed-0 draw
  at the depth), with L = 100 (2000 two-qubit gates, about 23 us on the 2026-10-24 Target).
- **Device and twin.** ibm_kingston. The Target fetched for D3 (calibration 2026-10-28 11:36:52 CET, SHA-256
  4c3a43e9…) is used for compiling and for the twin; no new fetch. The calibration in effect when the job runs is
  read with the result and reported; if it differs from 11:36:52, the twin is of an earlier calibration and that is
  stated beside the verdict.
- **Job.** 64 circuits x 2000 shots (D3: 250); `assemble --max-seconds 75` (the time model gave 9.6 s for 64 x 250 and
  D1, D2 were billed 7 s, so about 60 s expected); dynamical decoupling and twirling off. If the time model predicts
  more than 75 s, the job is not sent.
- **Measure and rule (as D1-D3).** z_device ~ lam z_exact + delta over the 64 inputs; **AGREE** if |lam_device -
  lam_twin| <= 2 SE (the device fit's), **BELOW** / **ABOVE** otherwise; **SIGNAL** if lam_device > 2 SE, else NONE.
- **Prediction (not a rule).** AGREE; SIGNAL if the twin's lam is above 3 rehearsal SE (`lam_device rehearse` on the
  pod with 2000 shots, before submission). Expected (estimate): rehearsal SE about 0.011 against a twin lam near 0.04.
- **Reported beside it.** Correlation, delta; vanity (two-qubit gates, duration) and essential (lam; shots as
  1/lam^2); flow M's lam_K at L = 100 for scale; billed seconds.
- **Not claimed.** One job, one input set, one device, one day; the cause of the tail is not tested; free fermions are
  classically easy.
