# Loop smoke c, 2026-10-15 (TOQB v15): with the classical reference and energy

Run b again, with the classical reference models and energy added to the report. It was not scored and has no
pre-registered predictions.

**Run.**

- **Plan:** [`plan.json`](plan.json) (= `plan_loop_smoke.json`).
- **Time:** 07:35-07:45 CEST, one arm after another, on a 2-core cloud workspace.
- **Records:** `arm-*.json`, `classical.json`. **Report:** [`report.md`](report.md).
- **Report regenerated:** after the run, from the same records, to relabel one column of section 2 ("s holding the
  QPU").

## What came out

**The arms.**

- Every arm was valid.
- Accuracy, margins and trajectories are identical to run b: the same seeds give the same circuits and samples.
- In session mode the dollar figures moved by under 6%: the classical time between jobs is measured anew in each run.

**The reference** (section 2 of the report). The same 64 training and 24 test points:

| row | test accuracy | time | energy (estimate) | money |
|---|---|---|---|---|
| classical: logistic regression | 0.917 | 0.05 s CPU | 1.4e-7 to 6.8e-7 kWh | - |
| classical: logistic, with squares and products | 1.000 | 0.06 s CPU | 1.7e-7 to 8.3e-7 kWh | - |
| classical: MLP, 32 units | 0.958 | 0.24 s CPU | 6.8e-7 to 3.4e-6 kWh | - |
| classical: 5 nearest neighbours | 1.000 | 0.00 s CPU | under 4e-9 kWh | - |
| quantum, best arm (qiskit:2:target:template, batch) | 0.750 | 69.8 s on the QPU | 0.19-0.48 kWh | $111.66 |
| quantum, PSF-Zero template (batch) | 0.708 | 69.6 s on the QPU | 0.19-0.48 kWh | $111.43 |

**Energy.**

- **Quantum arms:** charged 10-25 kW, superconducting systems' wall-plug power as cited in arXiv 2605.09580, for the
  seconds they hold the QPU.
- **Classical models:** charged 10-50 W for each CPU second.
- Both are assumptions, not measurements.
- The least any quantum row is estimated at is 42,000 times the most any classical model is.

## Reading (two numbers)

- **Display number:** for the same money, the compilers' models differ by one test point. In batch mode PSF-Zero's
  two arms spend the least, $0.21-0.23 less than Qiskit's, because their circuits are shorter.
- **Essential number:** on this task, classical models reach 0.92-1.00 in under a quarter of a second, for about a
  millionth of a kWh. Every quantum arm reaches 0.71-0.75, for 0.19-0.49 kWh and about $112.
  - The task was made by a quantum teacher of the same model, so it favours the quantum model if anything.
  - TOQB does not claim that quantum models beat classical ones. The reference is there so that nobody reads the
    compiler comparison as such a claim.
