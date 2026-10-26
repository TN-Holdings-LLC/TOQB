# Flow G, test match 3 (owner's go of 2026-10-26): the count rule against the zipper on the twin of ibm_kingston's calibration of 2026-10-24, the twin that matched the device. Fixed by SHA-256 and CET time before the run

**Why.** Flows D-F ran on the twin of ibm_marrakesh's 2026-10-13 snapshot. On the device day (2026-10-22) that kind of
twin under-stated the zipper's signal 1.5-2.3 times; on 2026-10-24 the twin built from ibm_kingston's calibration of
that day matched the device for the zipper (n = 10, L = 16, trained models: slope device 0.83-0.89, twin 0.87-0.88,
results/flow-c-2026-10-24, recomputed 2026-10-26). If flow F's WIN came from the snapshot's pessimism or its place, it
should weaken on this twin.

- **Device.** `file:<target.pkl>`: the Target fetched from ibm_kingston on 2026-10-24 (calibration 15:26:59 CEST)
  for flow C, SHA-256 3b93913856d2f0b9bf97ac03f89c43457157735413b02d8722c82d31065b218d (fetch.json); the run stops if
  the file's SHA differs. Only the twin ("sim"); TOQB's stand-in is a model of marrakesh and is not run (owner,
  2026-10-26: no artificial noise).
- **Arms and run.** `python -m toqb.fold_lam OUT --n 13 14 15 16 17 18 --L 16 --P 24 --T 256 --models sim --arms
  fold:rule psfai:template_zip --max-active 20 --models-seed 0 1 2 3 --device file:<target.pkl>` (toqb this commit;
  fold:rule as in flow F, the rule's choice and placement read from this Target; the zipper PSF-Zero a25), on a GPU
  pod.
- **Rule, per n.** A model is a win if `fold:rule`'s lam is larger than the zipper's on the twin, a loss if smaller.
  **WIN** at n: 3 or 4 wins of 4; **LOSS**: 3 or 4 losses; else **TIE**. Six verdicts, each reported; no pooled
  verdict. A cell that errors counts as neither.
- **Prediction (not a rule).** WIN at every n, but with smaller ratios than flow F's (1.5-8.2), since this twin was
  less pessimistic for the zipper.
- **Reported only.** Per n the four models' lam for both arms, beside flow F's on the marrakesh twin; the rule's
  choice and cycle on this Target; vanity (counts, duration) and essential (lam; shots as 1/lam^2) side by side.
- **Not claimed.** No device; one day's calibration of one device; random models, not trained ones (flow C's were
  trained); nothing is chosen from the result.
