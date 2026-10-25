# Flow D (owner's go of 2026-10-25, a GPU pod): how much signal the hole schedule keeps, against the zipper and Qiskit. Report only, no rule; fixed by SHA-256 and CEST time before the run

**Why.** On the cloud CPU (results/fold-holes-2026-10-25), at L = 8 and n = 9-11, the hole schedule (`fold:template`)
kept 1.5-2.0 times the zipper's signal on the twin and the stand-in. Not run: Qiskit, L = 16, larger n.

- **Run.** `python -m toqb.fold_lam OUT.jsonl --n 9 10 11 13 14 15 16 17 18 19 --L L --P 24 --T 256 --models sim dev
  --arms fold:template psfai:template_zip qiskit:2:target:template --max-active 24`, first with L = 8, then with
  L = 16, on an H100 (cupy, complex64), `snapshot:marrakesh`, TOQB's default front end (PSF-Zero a25, psfbind r3).
  One random model and 24 random inputs per (n, L), the same for every arm.
- **Reported.** Per (n, L, arm, model): lam, delta, correlation and residual against the noiseless model; two-qubit
  count, duration, active qubits. Vanity (counts, duration) and essential (lam, the shots for a fixed precision as
  1/lam^2) side by side. An arm above 24 active qubits is recorded as skipped (Qiskit at n = 19: 32).
- **Not done.** No rule, no claim of a winner; no device; nothing is chosen from the result.
- **Not claimed.** One random model per cell; the twin and the stand-in are TOQB's models of a 2026-10-13
  calibration; the fold arm's single-qubit runs are not merged (as Qiskit's template arm), the zipper's are.
