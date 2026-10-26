# Flow H, a small match (owner's go of 2026-10-26, 14:15 JST): where the rule keeps the most holes, holes against the zipper. Fixed by SHA-256 and CET time before the run

**Why.** Under item 50's rule (PSF-Zero a26) the holes remain at n = 8-11 (4, 3, 2, 1 holes on the 12-cycle) and
18-19; at n = 8 the rule's count is a tie with the zipper's (8 extra two-qubit gates per layer each), at n = 9 6
against 10. The owner asks whether the zipper would do better where the holes are many.

- **Arms.** `fold:template` (holes, as in flow D) and `psfai:template_zip` (the zipper, PSF-Zero a25).
- **Run.** `python -m toqb.fold_lam OUT --n 8 9 10 --L 16 --P 24 --T 256 --models sim dev --arms fold:template
  psfai:template_zip --max-active 20 --models-seed 0 1 2 3` (snapshot:marrakesh, flows D-F's settings; model 0 is flow
  D's at n = 9, 10), on the cloud container's CPU (numpy), as two processes on its two cores: models 0 1 into
  part0.jsonl and models 2 3 into part1.jsonl (each line carries its model; the split changes no value). About 1.5 h
  (a timing run with T = 16 took 54 s for n = 10).
- **Rule, per n.** A model is a win for the holes if their lam is larger than the zipper's on both the twin and the
  stand-in, a loss if smaller on both. **WIN** (holes better) at n: 3 or 4 of 4; **LOSS** (zipper better): 3 or 4 of
  4; else **TIE**. Three verdicts, no pooled one.
- **Prediction (not a rule).** WIN at n = 9, 10 (flow D, model 0: 0.26 / 0.26 and 0.51 / 0.50 against the zipper's
  0.11 / 0.15 and 0.10 / 0.11); n = 8 not known (4 holes).
- **Check.** Model 0's lines at n = 9, 10 equal flow D's L16 lines.
- **What follows.** Nothing is changed by this run alone: a LOSS at n = 8 or 9 would be brought to the owner as a
  proposal for item 50's tie rule, not applied.
- **Not claimed.** Models of a 2026-10-13 calibration, not a device; one place; four models.
