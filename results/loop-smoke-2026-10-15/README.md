# Loop smoke, 2026-10-15 (TOQB v15)

The first run of layer 3's variational-loop scenario (`toqb/task_loop.py`), at smoke size. It was not scored and has
no pre-registered predictions. It checks that the loop runs end to end for every arm, and shows what the scenario can
and cannot tell apart at this size.

**Run.**

- **Plan:** [`plan.json`](plan.json) (= `plan_loop_smoke.json`).
- **Time:** 06:08-06:19 CEST, one arm after another, on a 2-core cloud workspace.
- **Arm records:** `arm-*.json`. **Report:** [`report.md`](report.md).
- **Task:** a 4-qubit, 2-layer ring classifier, a teacher-student task, 30 SPSA iterations with batch 8 and 400 shots,
  on FakeFez with TOQB noise. Each arm compiled 576 circuits.
- **Versions:** Qiskit 2.5.2; PSF-Zero release `psf_compile` 2026-10-14.1 with its AI front end prototype a21.
- **Code changes after the run:** `task_loop.py` now writes its timestamps in CEST, and `run` copies the plan into the
  output directory. Neither changes a result. The records' timestamps were converted from the workspace's clock (JST)
  to CEST.

## What came out

**Every arm was valid:**

- 0 structural failures;
- 0 operations on failed elements;
- 15 of 15 equivalence checks passed.

**The loop's cost** (compile time per loop of 576 circuits):

| arm | compile s | per circuit | tier |
|---|---|---|---|
| qiskit:2:target:template (reference) | 0.18 | 0.23 ms | 1x |
| qiskit:3:target:template | 0.17 | 0.22 ms | 1x |
| psfai:template | 0.21 | 0.34 ms | 1x |
| qiskit:3:target:recompile | 10.6 | 18.3 ms | over 10x |
| psfai:recompile | 29.2 | 50.6 ms | over 10x |

- A template is 60 x (Qiskit) to 140 x (PSF-Zero) cheaper per loop than compiling every circuit.
- **Between the template arms, PSF-Zero's bind is 1.5 x Qiskit's** (0.34 against 0.23 ms per circuit). All three
  are in the 1x tier.
- The simulation took 103-122 s per arm. That is 500-700 times every template arm's compile time.

**The circuits** (means over the loop):

| arm | 2q gates | duration |
|---|---|---|
| PSF-Zero | 14 | 2.73-2.74 µs |
| Qiskit level 2 | 17 | 3.48 µs |
| Qiskit level 3 | 17 | 3.40-3.41 µs |

PSF-Zero's circuits are 0.80 times Qiskit level 3's duration.

**The loop's result:**

- **Final noisy test accuracy:** 0.71-0.79 on 24 points, which is 17-19 points correct. The noiseless accuracy of
  the final angles is the same in every arm.
- **Loss curves:** within 0.02 of each other at every fifth iteration.
- **Target 0.75:** three arms reached it at iteration 30 (psfai:recompile, qiskit:2:target:template and
  qiskit:3:target:recompile). Two did not (psfai:template, qiskit:3:target:template).
- The differences are one or two test points. They do not separate the arms.

## Reading (two numbers)

- **Display number:** a template makes the loop's compile cost 60-140 times smaller. Measured only against the
  recompiling arms, PSF-Zero's template "wins" by 140 x.
  - Against Qiskit's own loop practice (a parametrised circuit, transpiled once), it does not win: its bind is 1.5
    times Qiskit's.
  - Both compile times are negligible next to the circuits' execution.
- **Essential number:** at this size, the 20% shorter circuits did not change what the loop learned.
  - At 4 qubits and 2 layers, a circuit lasts about 3 µs against T1 of about 100 µs or more. Noise barely moves
    <Z_0>, so the gradients are dominated by shot noise and SPSA's own randomness.
  - The scenario works. This size cannot show a compiler's effect on learning.

## What the standard size needs (from this smoke)

- **Larger and deeper circuits:** n = 6-8 and L = 4-8, where noise matters. In PSF-Zero's RING1 rehearsal on FakeFez's
  noise model, F at n = 6, L = 8 was 0.65 against 0.47 for Qiskit level 3.
- **More test points and training seeds,** so that one or two points do not decide the result.
- **Predictions fixed before the run.**
- **The calibration split** (principle 4).
- **The arms run in parallel,** one process each. Sequentially, this smoke took 11 minutes on 2 cores.
