# Loop budget run, 6 qubits, 8 layers, 2 minutes of QPU, 1,000 seeds, 2026-10-16 (TOQB, fast engine)

Scored against [`prereg/2026-10-16-loop-n6-budget.md`](../../prereg/2026-10-16-loop-n6-budget.md) (SHA-256
`0e35edcf...30ea`), fixed at 02:09:55 CEST by its SHA-256 given to the owner before the first start, and pushed
afterwards (the first start was at the workplace, which has no GitHub). Times in CEST.

**Run.**

- **The first start** (workplace, 02:18) stopped after 240 of 2,000 arm runs and is kept unscored in
  [`../loop-n6-budget-2026-10-16-stopped-at-work/`](../loop-n6-budget-2026-10-16-stopped-at-work/). By the
  pre-registration's interruption rule, this is the run that counts: the first complete one.
- **This run:** 12:55:31-13:57:12, the owner's home machine (WSL), ten processes, into a new folder (`...-16b`), at
  TOQB `79faa58` and PSF-Zero `69b946b` (the arms read only PSF-Zero's c61 and a22, checked by SHA-256).
- **Checks before the first seed:** every fixed hash (pre-registration, the 1,000 plans, the TOQB modules, PSF-Zero's
  two files) and the versions. The 1,000 plans in the run folder are byte for byte the pre-registered ones.
- **Files:** `score.md` and `score.json` (`python -m toqb.score_loop_preg4`; scored again by the authors from the raw
  records: the same verdicts and numbers), `times.txt`, and `raw_records.zip`, the run folder as the run zipped it.

## Verdicts

| ID | prediction | verdict | numbers |
|---|---|---|---|
| B1 | every arm run valid, stopped within the budget, evaluated at the stop | **CONFIRMED** | 2,000 of 2,000 |
| B2 | (primary) noiseless accuracy at the budget higher with PSF-Zero | **CONFIRMED** | +0.026 (95% +0.020 to +0.032), p = 0.000005; better / equal / worse: 550 / 84 / 366 |
| B3 | noisy accuracy at the budget higher with PSF-Zero | **CONFIRMED** | +0.039 (+0.033 to +0.045), p = 0.000005; 624 / 51 / 325 |
| B4 | noisy margin at the budget higher with PSF-Zero | **CONFIRMED** | +0.023 (+0.020 to +0.025), p = 0.000005; 735 / 2 / 263 |
| B5 | PSF-Zero gets at least as many iterations within the budget | **CONFIRMED** | 50 against 49 in every seed |

p = 0.000005 is the floor of 200,000 sign patterns. scipy's one-sided t-test and Wilcoxon test agree: below 1e-16 for
B2, 1e-30 for B3, 1e-60 for B4.

## The two numbers

- **Display:** mean accuracy at 2 minutes of QPU, noisy: **PSF-Zero 0.533, Qiskit level 2 0.494.**
- **Essential:**
  - PSF-Zero gave the better model in 624 of 1,000 seeds and the worse one in 325; worst seed -0.28.
  - **Both models are weak at this budget.** 54 of PSF-Zero's 1,000 models and 23 of Qiskit's reached 0.7 on the noisy
    device; Qiskit's mean is below one half. The classical models reach 0.73-0.77 on the same task.

## Reading

- **The authors' expectation was wrong.** Before the run they expected B2 and B3 refuted or not decided, from the
  20-seed short test (-0.006 noiseless). With 1,000 seeds the difference is +0.026 noiseless and +0.039 noisy. The
  short test was too small to see it (its interval was about +-0.03).
- **Where it comes from.** For the same $192, PSF-Zero's iteration is 2.5% cheaper, so it trains one iteration more
  (50 against 49); its circuit is 8.7 us against 18.1 us (120 two-qubit gates against 158), so the noisy device
  degrades its signal less (margin +0.022 against -0.000).
- **Against run 2.** Run 2 trained 200 iterations with calibrated SPSA, and there the accuracy did not differ (0.702
  against 0.701). Under the owner's real budget, 50 iterations of run 1's SPSA, PSF-Zero's model is better. The
  difference is real but small, and at this budget neither model is useful against a classical one.
- **Scope:** one task (n = 6, L = 8, teacher seed 4) and one device model (FakeFez with TOQB's noise model), in
  simulation. Nothing ran on a device.
