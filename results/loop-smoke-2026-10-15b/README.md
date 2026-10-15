# Loop smoke b, 2026-10-15 (TOQB v15): for the same money, which compiler returns the best model?

The second smoke run of layer 3's variational-loop scenario. It is the first run with prices and the first through
PennyLane. It was not scored and has no pre-registered predictions.

**Run.**

- **Plan:** [`plan.json`](plan.json) (= `plan_loop_smoke.json`).
- **Time:** 07:03-07:11 CEST, one arm after another, on a 2-core cloud workspace.
- **Arm records:** `arm-*.json`. **Report:** [`report.md`](report.md).
- **Setup:** the same task, device, seeds and arms as [run a](../loop-smoke-2026-10-15/), with two differences:
  - every circuit was built as a PennyLane tape and run through `CompiledDevice` (PennyLane 0.45.1);
  - prices were added: IBM's measured rate in PSF-Zero's runs, and $96 per QPU minute.

## What came out

**Every arm was valid:**

- 0 structural failures;
- 0 operations on failed elements;
- 15 of 15 equivalence checks passed.

**The same money** (the reference's whole training, plus 5%: batch $117.24, session $119.66):

| arm | spent, batch | spent, session | accuracy / margin at the budget, batch | at the budget, session |
|---|---|---|---|---|
| psfai:template | $111.43 | $113.15 | 0.708 / 0.326 | 0.708 / 0.326 |
| qiskit:2:target:template (reference) | $111.66 | $113.96 | 0.750 / 0.366 | 0.750 / 0.366 |
| qiskit:3:target:template | $111.64 | $113.74 | 0.708 / 0.325 | 0.708 / 0.325 |
| qiskit:3:target:recompile | $111.64 | $121.69 | 0.750 / 0.359 | 0.625 / 0.244 (iteration 20) |
| psfai:recompile | $111.43 | $138.82 | 0.708 / 0.302 | 0.625 / 0.195 (iteration 20) |

**Batch mode.**

- Every arm pays almost the same: the circuits' durations change the bill by 0.2%.
- PSF-Zero's shorter circuits are the cheapest by $0.23.

**Session mode.**

- The classical time between jobs is billed at the QPU's price.
- A recompiling arm pays 7% (Qiskit level 3) to 22% (PSF-Zero) more than the template arms.
- So within the same money it stops at iteration 20, with a worse model.
- The template arms differ by under $1.

**Accuracy.**

- At the budget, the template arms are 0.708-0.750: 17 or 18 of 24 test points.
- One test point separates them.

**Identical through PennyLane.**

- The template arms' trajectories are identical to run a's to every printed digit, where the circuits were built in
  Qiskit.
- The recompiling arms part from run a at iteration 1 or 2. They end 0.04-0.08 apart in accuracy.
- **Why the recompiling arms part:**
  - PennyLane computes an expectation value from counts with different rounding from TOQB's own formula. It differs in
    the last bit for 230 of the 401 possible counts at 400 shots.
  - The angles therefore differ by about 1e-16.
  - A template only binds them. A compiler that recompiles makes angle-dependent choices, and its circuits change.
- So at this size, a recompiling arm's result moves by one or two test points from a perturbation of 1e-16. Single-run
  differences of that size are noise.

## Reading (two numbers)

- **Display number:** PSF-Zero's template arm is the cheapest in both modes. In session mode it is $25.67 cheaper
  than PSF-Zero recompiling and $8.54 cheaper than Qiskit recompiling.
  - Against Qiskit's own template, the difference is $0.23-0.81, and Qiskit's bind is faster (0.44-0.46 against
    0.61 ms per circuit).
- **Essential number:** for the same money, every template arm returned the same model, within one test point.
  - At 4 qubits and 2 layers, noise barely matters, as run a found.
  - The money question can only be answered at the standard size: n = 6-8, L = 4-8, several training seeds,
    predictions fixed first.
  - What this run does show: in session mode, a compiler that recompiles in the loop pays for it in QPU dollars, and
    trains less for the same budget.
