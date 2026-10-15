# Loop standard run 2, 6 qubits, 8 layers, 200 seeds, 2026-10-15 (TOQB, fast engine)

Scored against [`prereg/2026-10-15-loop-n6-standard-2.md`](../../prereg/2026-10-15-loop-n6-standard-2.md) (SHA-256
`d1126e62...ffcbd`). It was fixed at 16:02:41 CEST and pushed (commit `eedcb50`) before the run.

**Run.**

- **Time:** 16:03:46-17:45:15 CEST, on the owner's home machine (WSL), ten seeds at a time.
- **Checks before the first seed:** every fixed hash (pre-registration, the 200 plans, nine TOQB modules, PSF-Zero's
  two files) and the versions.
- **Run once.** There was no interruption.
- **Files:** `score.md` and `score.json` (from `python -m toqb.score_loop_preg2`), `times.txt`, and
  `raw_records.zip`, which holds every seed's plan, records, report and log as the run wrote them.

## Verdicts

| ID | prediction | verdict | numbers |
|---|---|---|---|
| M1 | every arm run valid and complete | **CONFIRMED** | 400 of 400 |
| M2 | (primary) noiseless final accuracy higher with PSF-Zero | **REFUTED** | mean difference -0.0004 (95% interval -0.014 to +0.014); better / equal / worse: 85 / 19 / 96 |
| M3 | noisy final accuracy higher with PSF-Zero | **NOT DECIDED** | +0.0009 (-0.013 to +0.015), p = 0.45; 91 / 7 / 102 |
| M4 | noisy final margin higher with PSF-Zero | **CONFIRMED** | +0.050 (+0.035 to +0.065), p = 0.000005; better in 150 of 200 |
| M5 | the noiseless difference grows from iteration 60 to 200 | **REFUTED** | +0.010 at 60, -0.000 at 200 |
| M6 | PSF-Zero spends no more than Qiskit | **CONFIRMED** | $1,510 against $1,549 in every seed |

The intervals are mean +- 1.96 standard errors. scipy's one-sided t-test and Wilcoxon test agree with the sign-flip
p-values: 0.52 and 0.60 for M2, 0.45 and 0.48 for M3, below 1e-5 for M4.

## The two numbers

- **Display:** mean final accuracy, noisy, for the same money: **PSF-Zero 0.702, Qiskit level 2 0.701.**
- **Essential:**
  - For a classifier trained this way, the compiler made no difference. PSF-Zero gave the better model in 91 of
    200 seeds and the worse one in 102.
  - 114 seeds of each arm reached 0.7.
  - The classical models reach 0.73-0.77.

## Reading

**What was refuted.**

- With SPSA settings under which the model learns, PSF-Zero's shorter circuits do not train a more accurate
  classifier. Any difference is below about 1.5 points.
- Nor does the difference grow with training.
- The +0.040 of run 1 came from a regime where neither model learned. At iteration 60 here, with the calibrated
  settings, it was +0.010 (-0.004 to +0.024).

**Why accuracy did not move.**

- Both arms reach about 0.71 noiseless after 200 iterations. Without noise, the same settings reached 0.726.
- So the noise cost the training little in either arm. Noise at evaluation takes 0.007 of the accuracy
  (PSF-Zero) and 0.008 (Qiskit).
- This noise mostly shrinks <Z0> towards 0 without changing its sign, and a classifier reads only the sign.

**What PSF-Zero's circuits did change: the signal.**

- The mean margin is 0.206 against 0.156, 1.32 x larger. Under PSF-Zero, <Z0> is on average about a third
  larger in the direction of the label.
- That matters wherever the value itself is used rather than its sign:
  - a regression;
  - a probability;
  - an energy;
  - the gradient estimate of an optimiser that is not as forgiving as these settings.
- For the same precision, shots scale as 1 / signal^2. This suggests about 0.57 x the shots, but that has not been
  tested. It is a candidate for the next pre-registration, not a result.

**Money.** PSF-Zero's training cost 2.5% less ($1,510 against $1,549) for the same circuits and shots, because its
circuits are shorter.

**Scope.** One task, one device model, in simulation, with the fast engine (checked against Aer). It is not a
hardware result.
