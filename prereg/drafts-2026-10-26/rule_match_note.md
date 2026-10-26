# Flow F, test match 2 (owner's go of 2026-10-26, a GPU pod): the count rule against the zipper over four random models; the read-out node moved, reported. Fixed by SHA-256 and CET time before the run

**Why.** Flow E (results/flow-e-2026-10-26) had one random model per cell. The count rule (the workplace's proposal:
of the extra two-qubit gates per layer -- pendants n - m_below, holes 2 (m_above - n), the zipper's -- the fewest
decides) picked the larger lam in every cell there. This match asks whether that holds over more models. Qiskit is
not in it (owner, 2026-10-26: too slow; a separate match).

- **Arms.** `fold:rule` (toqb `fold.py`, this commit: pendants at n = 13-17, holes at n = 18, exact on every clbit at
  n = 9-19, L = 2, 4); `psfai:template_zip` (the zipper, PSF-Zero a25, as in flows D and E); `fold:rulerot` (the rule
  with ring node 0, the read-out node, on the plain cycle node farthest from the pendants).
- **Run.** `python -m toqb.fold_lam OUT --n 13 14 15 16 17 18 --L 16 --P 24 --T 256 --models sim dev --arms fold:rule
  psfai:template_zip --max-active 20 --models-seed 0 1 2 3`, then `--n 13 14 15 16 17 --arms fold:rulerot` with the
  same settings; GPU pod (cupy, complex64), `snapshot:marrakesh`. Model 0 is flow D's and E's model; models 1-3 are new
  (seed 1000 n + L + 100000 s).
- **Rule (main match: `fold:rule` against the zipper), per n.** For each of the four models, a model is a win if
  `fold:rule`'s lam is larger than the zipper's on both the twin and the stand-in, a loss if smaller on both, else
  neither. **WIN** at n: 3 or 4 wins of 4; **LOSS**: 3 or 4 losses; else **TIE**. Six verdicts (n = 13-18), each
  reported; no pooled verdict. A cell that errors counts as neither.
- **Prediction (not a rule).** WIN at every n = 13-18 (flow E: 1.5-4.0 times the zipper's lam at L = 16, model 0).
- **Check (not a rule).** Model 0's lines equal earlier ones: `fold:rule` at n = 13-17 flow E's `fold:pend`, at
  n = 18 flow D's `fold:template`; the zipper flow E's.
- **Reported only.** `fold:rulerot` against `fold:rule` (n = 13-17): per n the four models' lam differences on both
  models. Vanity (counts, duration) and essential (lam; shots as 1/lam^2) side by side.
- **Not claimed.** No device; the twin and the stand-in are TOQB's models of a 2026-10-13 calibration; one
  placement per n on one device; nothing is chosen from the result (the rule was fixed before these data).
