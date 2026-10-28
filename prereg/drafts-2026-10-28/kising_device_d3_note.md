# Device test D3 (owner's go of 2026-10-28: "N20L50"; a short device job is outside the 10/27 no-Qiskit rule, which is for long runs): does the kicked Ising ring keep on the device, at 1000 two-qubit gates, what the day's twin predicts? Fixed by SHA-256 and CET time before the fetch

**Why.** Flow M (kising_m_note.md) measures on the 2026-10-24 twin the kept signal lam_K of the kicked Ising ring
(J = pi/4, h = 0.6; real angles, exact reference at any n) at L = 8-100. A twin is a model. One device point at depth
tells whether the twin is right there, with an exact answer and no proxy.

- **Workload.** `toqb.kising`, n = 20, L = 50, h = 0.6, `fold:rule` (the ring on a 20-cycle of the device's Target, by
  the formula; 1000 two-qubit gates on the 2026-10-24 Target), seed 0: the first 64 X-basis inputs of flow M's
  seed-0 draw at L = 50 (the first 24 are flow M's own). `toqb.lam_device build --kind kising` (this commit).
- **Device and twin.** ibm_kingston; the Target fetched at home just before (`toqb.s2rc_device fetch`); compiled for
  it by `fold:rule` and predicted by its twin (256 trajectories), all before submission. If `submit` moves the job to
  another device, the twin is of another device and that is reported. If the formula's placement differs from the
  2026-10-24 one, that is reported; the placement is the formula's, not chosen.
- **Job.** 64 circuits x 250 shots; `assemble --max-seconds 10`; dynamical decoupling and twirling off. If the time model
  predicts more than 10 s, the job is not sent and P is not changed without a new note.
- **Measure.** z_device ~ lam z_exact + delta over the 64 inputs (least squares; the slope's SE from the residuals),
  against the twin's slope fixed before submission. `lam_device rehearse` on the pod gives the expected SE first.
- **Rule (as D1, D2).** **AGREE** if |lam_device - lam_twin| <= 2 SE (the device fit's); **BELOW** if lam_device <
  lam_twin - 2 SE; **ABOVE** if above. One verdict. Also stated: SIGNAL if lam_device > 2 SE, else NONE.
- **Prediction (not a rule).** AGREE (as D1 and D2), and SIGNAL if the day's twin gives lam above 3 rehearsal SE.
- **Procedure check (this commit, no IBM connection):** fake fetch (FakeFez), `build --kind kising` (n = 8, L = 4, P = 6),
  `assemble`, `submit --local`, `score` ran end to end.
- **Reported beside it.** Correlation, delta; vanity (two-qubit gates, duration) and essential (lam; shots for a fixed
  precision as 1/lam^2); flow M's twin lam_K at L = 50 (2026-10-24 calibration) for scale; billed seconds.
- **Not claimed.** One job, one input set, one device, one day. Free fermions are classically easy; this checks the
  twin, not an advantage.
