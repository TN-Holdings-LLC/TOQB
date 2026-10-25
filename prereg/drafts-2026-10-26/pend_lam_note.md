# Flow E (owner's go of 2026-10-26, a GPU pod): how much signal the pendant schedule keeps, against the zipper. Report only, no rule; fixed by SHA-256 and CET time before the run

**Why.** In flow D (results/flow-d-2026-10-25) the hole schedule kept the least signal of the arms in 3 of 4 values at
n = 13, 14, L = 16 (6-7 holes on a 20-cycle). The pendant schedule (`fold:pend`, toqb `ec3da86`, `94b442c`) lays the
ring on a 12-cycle and hangs the n - 12 extra nodes off it: n + (n - 12) two-qubit gates per layer on exactly n qubits
(L = 16: 224-384 against the holes' 352-434 on 20 qubits and the zipper's 464-656), exact on every clbit.

- **Run.** `python -m toqb.fold_lam OUT.jsonl --n 13 14 15 16 17 18 --L L --P 24 --T 256 --models sim dev
  --arms fold:pend fold:pendbind psfai:template_zip --max-active 20`, first with L = 8, then with L = 16, on a GPU pod
  (cupy, complex64), `snapshot:marrakesh`, TOQB's default front end (PSF-Zero a25, psfbind r3). The settings, seeds
  and models of flow D; the same random model and 24 inputs per (n, L) for every arm.
- **Arms.** `fold:pend` (pendants spread over the cycle nodes that have one); `fold:pendbind` (the same placement, the
  angles bound before transpiling, so that single-qubit runs are merged; 3-9 % fewer sx); `psfai:template_zip`, the
  zipper, as in flow D. The hole schedule is not run again: flow D's lines are used for it.
- **Check (not a rule).** The zipper's lines are those of flow D's L8.jsonl / L8b.jsonl / L16.jsonl for the same
  (n, L, model), to the printed digits. If not, flow D's hole lines are not set beside this run's, and that is reported.
- **Reported.** Per (n, L, arm, model): lam, delta, correlation and residual against the noiseless model; two-qubit
  count, duration, active qubits. Vanity (counts, duration) and essential (lam; shots for a fixed precision as 1/lam^2)
  side by side, with flow D's hole lines beside them.
- **Not done.** No rule, no claim of a winner; no device; nothing is chosen from the result.
- **Not claimed.** One random model per cell, one seed; at L = 16 a difference of about 0.1 in lam is within the
  estimate's spread (flow D); the twin and the stand-in are TOQB's models of a 2026-10-13 calibration. The pend arms'
  placement is the formula's first 12-cycle on marrakesh; other cycles or devices are not run.
