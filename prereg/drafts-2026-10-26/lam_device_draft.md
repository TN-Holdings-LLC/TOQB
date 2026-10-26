# DRAFT (not fixed, not declared): the folded ring's signal on a device, against the zipper and the day's twin

Prepared 2026-10-26 for a device day about two weeks later (owner: "一応用意しておいて"). To be completed after flow G
(the same match on the twin of ibm_kingston's 2026-10-24 calibration), then fixed by SHA-256 and CET time at home before
the fetch. Open points are marked **OPEN**.

**Question.** Does the folded ring (PSF-Zero a26's item 50; TOQB `fold:rule`) keep on the device the signal the day's
twin predicts, and more than the zipper does?

**Why this form.** No training and no labels: one random ring classifier and P random inputs, the same for both arms;
the slope of the device's <Z> of clbit 0 against the noiseless value is the arm's kept signal (lam). Flow C's lesson:
its first 90 test points were all of one label; here nothing is labelled. On 2026-10-24 the twin built from the day's
calibration matched the device for the zipper (slope 0.83-0.89 against 0.87-0.88).

- **Device and twin.** The day's Target fetched at home just before (`toqb.s2rc_device fetch`); the twin built from
  it. **OPEN:** backend (ibm_kingston or the fixed order); if `submit` moves the job to another device (its fixed
  order), the twin's prediction is of another device and that is reported, not hidden.
- **Arms.** `fold:rule` (pendants at n = 13) and `psfai:template_zip` (the zipper, PSF-Zero a25).
- **Size.** n = 13, L = 16; **OPEN:** a second n (16) and a second model, if flow G shows a small margin.
- **Points and shots.** P = 48 inputs per arm, 250 shots each (**OPEN:** P 48-64): 96 circuits x 250 shots, about 12 s
  by `s2rc_device`'s time model (0.036 s per circuit + 0.00027 s per shot + 3 s), kingston billed 0.7 x its prediction
  on 2026-10-24.
- **Precision (to check before fixing).** The slope's standard error is about the shot noise per point (about 0.063 at
  250 shots) over the spread of the noiseless z and sqrt(P); it is computed for the chosen model before fixing
  (`lam_device build` prints the spread).
- **Rule (proposal).** WIN if the device slope of `fold:rule` minus the zipper's is more than 2 standard errors of the
  difference; LOSS if less than -2; else TIE. **OPEN:** owner's choice of the rule.
- **Reported beside it.** Each arm's device slope against the twin's slope fixed before submission (the twin's
  accuracy, per arm); the offsets; vanity (two-qubit gates, duration) and essential (lam; shots as 1/lam^2).
- **Not claimed.** One device, one day, one model; a random model is not a trained classifier.

**Procedure** (toqb `lam_device.py`; checked end to end offline with `fetch --fake FakeKingston` and `submit --local`):

```
[home, VPN off]  python -m toqb.s2rc_device fetch --backend <backend> --out DAY/fetch
[pod]            python -m toqb.lam_device build DAY/fetch RUNS --arm fold:rule          --n 13 --L 16 --mseed 0 --P 48
[pod]            python -m toqb.lam_device build DAY/fetch RUNS --arm psfai:template_zip --n 13 --L 16 --mseed 0 --P 48
[pod]            python -m toqb.s2rc_device assemble --fetch DAY/fetch --runs RUNS --out JOB --max-seconds 20
[home, VPN off]  python -m toqb.s2rc_device submit --job JOB ; python -m toqb.s2rc_device result --job JOB
[any]            python -m toqb.lam_device score JOB RUNS
```
