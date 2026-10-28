# Device test D5 (owner's go of 2026-10-28: tests 1, 2 and 3 of the evening's list; choices "n = 20, rule against zipper" and "fit p at n = 20, predict n = 32 and 40 by the formula"): one job, three parts, on ibm_kingston. Fixed by SHA-256 and CET time before submission

All parts: ibm_kingston; compiled for and predicted by D3's fetched Target (calibration 2026-10-28 11:36:52 CET,
SHA-256 4c3a43e9…), no new fetch; the calibration in effect when the job runs is read with the result and reported.
One job, 1000 shots per circuit in every cell (`assemble` takes one shot count per job); 6 cells x 64 = 384
circuits; `assemble --max-seconds 180` (the time model gives 120.5 s; D1 and D2 were billed about 0.7 of it); dynamical decoupling and twirling off. Measure in every
cell: z_device ~ lam z_noiseless + delta over its 64 inputs (least squares; the slope's SE from the residuals).

## Part A (test 1): the formula's schedule against the zipper on the same qubits, on the device

- TOQB's ring classifier, n = 20, L = 16, model 0 of `toqb.lam_device` (as flows J and K), 64 inputs x 1000 shots,
  arms `fold:rule` (the bare ring on the 20-cycle) and `fold:zipcyc` (the zipper on the same 20 qubits); twin per arm.
- **Rule.** d = lam_rule - lam_zipcyc on the device; **WIN** if d > 2 SE (SE = hypot of the two fits' SE), **LOSS**
  if d < -2 SE, else **TIE**. Also per arm against its twin: AGREE / BELOW / ABOVE within 2 SE.
- **Prediction (not a rule).** WIN (flow K, twin: 1.44-1.81 times); both arms AGREE.

## Part B (test 2): the twin at a larger ring with pendants

- The classifier, n = 22 (the 20-cycle with two pendants, as flow J), L = 16, model 0, 64 x 1000 shots, `fold:rule`,
  twin. (n = 24 is not included: its twin takes about 5 h for 64 inputs.) Part A's rule arm is the n = 20 point.
- **Rule.** AGREE / BELOW / ABOVE within 2 SE against the twin. **Prediction.** AGREE.

## Part C (test 3): beyond the twin, a formula prediction

- `toqb.kising`, h = 0.6, L = 24, `fold:rule`, seed 0, 64 inputs x 1000 shots at n = 20 (with twin), n = 32 and n = 40
  (no twin: `lam_device build --twin none`; on the 2026-10-24 Target the ring is placed at n = 32 with 32 and at
  n = 40 with 44 two-qubit gates per layer).
- **Rule** (`toqb.kising_formula`, this commit; tests/test_kising_formula.py). One uniform depolarizing rate p is
  fitted so that the noisy free-fermion recursion (`kising.x0_noisy`, exact for that noise; checked against density
  matrices at n = 4-6) gives the device's lam at n = 20 on its own 64 inputs. The same p then predicts lam at n = 32
  and 40 on their inputs. **AGREE** if |lam_device - lam_pred| <= 2 sqrt(SE_device^2 + SE_pred^2), where SE_pred
  propagates the n = 20 fit's SE through p; else **BELOW** / **ABOVE**. No calibration data enter the formula.
- **Prediction (not a rule).** AGREE at n = 32 and 40. For scale, at p = 0.004 the formula gives lam 0.26, 0.30 and
  0.10 at n = 20, 32 and 40 on these inputs; the order follows how far X_0's strings reach around each ring at L = 24.
- **Reported beside it:** the twin at n = 20 against the device (AGREE / BELOW / ABOVE); the readout error of the
  measured qubit in each placement, from the Target (not used in the formula); D3's n = 20, L = 24 point (250 shots,
  same inputs) for comparison.

## Not claimed

One job, one model or input set per cell, one device, one day; uniform depolarizing is a model, and a disagreement
says that it does not carry from n = 20 to larger rings on this device, not why.
