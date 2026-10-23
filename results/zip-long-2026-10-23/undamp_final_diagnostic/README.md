# Diagnostic only: the undamped readout at the final point (16,000 loops), run after the score (2026-10-23)

Not part of any rule and not for use (owner, 2026-10-23: no correction). Run on the same pod with
`toqb.undamp_run --final-only`, one run at a time, 64-80 s each (the declared all-points run had taken 11-14 min a
point with three at once; cause not found). Zip SHA-256 c442c9e0ad3f94393af2fc46c7cd20bd9a3d3ea94ea0275dd3ee4d986319373c.
Shots reproduced in all 6.

| teacher | arm | lam / delta | stand-in acc with shots: raw -> undamped | noiseless test acc |
|---|---|---|---|---|
| 11 | item 31 | 0.317 / +0.036 | 0.587 -> 0.648 | 0.650 |
| 11 | zipper | 0.227 / -0.007 | 0.672 -> 0.674 | 0.698 |
| 12 | item 31 | 0.293 / +0.056 | 0.617 -> 0.676 | 0.660 |
| 12 | zipper | 0.221 / -0.006 | 0.686 -> 0.686 | 0.736 |
| 13 | item 31 | 0.233 / +0.048 | 0.630 -> 0.676 | 0.650 |
| 13 | zipper | 0.195 / +0.008 | 0.687 -> 0.684 | 0.724 |

Reading (the workplace's point, with home's): the zipper's raw lead with shots (+0.057 to +0.085) falls to +0.008 to
+0.026 once item 31's read-out offset delta is removed. Three parts, roughly: (1) the zipper's trained model is better
(noiseless accuracy +0.05 to +0.08, no noise and no delta involved); (2) its smaller lam lets the 250 shots flip more
answers, which takes much of (1) back; (3) item 31's circuit reads out with an offset (+0.04 to +0.06; a property of
the circuit, results/lam-ablate-2026-10-22), which costs it raw accuracy. Used raw, as the owner decided, (1) and (3)
are both the zipper's: a better model and a readout without offset, both by formula; (2) is its price.
