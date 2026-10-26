# Estimating lam without simulation (owner's go of 2026-10-26, "まず２"): two fixed estimators and the test they must pass before they are used for n = 21-30. Fixed by SHA-256 and CET time before any estimate is computed

**Estimators** (per compiled circuit; model 0's first input, as fold_lam's counts; `snapshot:marrakesh` Target errors
used to *evaluate* only, never to choose):

- **E1 (ESP, whole circuit):** the product of (1 - error) over every gate (cz, sx, x) and the read-out of clbit 0's
  qubit.
- **E2 (ESP, light cone):** the same product over the gates in the backward light cone of clbit 0's measurement (a
  gate is in it if it touches a qubit already in the cone, walking back from the measurement), and that read-out.

Neither has a fitted parameter. Idle decoherence is not in either.

**Test** against the twin's lam (model "sim") of every cell already run with a lam: flow D (L8, L8b, L16: fold:template,
psfai:template_zip, qiskit:2:target:template), flow E (fold:pend; L 8, 16).

- **A. Ranking:** Spearman correlation between the estimate and lam over all cells, per L: at least 0.8.
- **B. Order within n:** over all pairs of arms at the same (n, L) whose twin lam differs by more than 0.1, the
  estimate orders them as lam does in at least 90 %.
- An estimator is **used** for n = 21-30 only if it passes both A and B at both L. If both pass, E2 is used. If none
  passes, no estimate for n = 21-30 is reported as a lam, and the counts alone are reported.

**Known limit, stated before:** the estimate does not depend on the angles, so it cannot follow flow F's spread over
models (the zipper's lam 0.09-0.46 at one n); that spread is reported beside it.
