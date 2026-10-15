# Loop pilot, 6 qubits, 8 layers, 2026-10-15 (TOQB v15)

A pilot, not a scored run: no predictions were fixed. It asks whether the compiler changes what the loop learns once
the circuits are deep enough for noise to matter.

**Run.**

- **Plans:** `seed11/plan.json` and `seed12/plan.json` (`plan_loop_pilot_n6_s11.json`, `..._s12.json`).
- **Time:** 12:54-13:05 CEST, the two seeds in parallel, on the owner's home machine (WSL), one thread per process.
- **Versions:** Qiskit 2.5.2, Aer 0.17.2. PSF-Zero 7116bc2: psf_compile c61 and front end a22.

**Fixed before any compiler ran.**

- **The task:** the teacher-student task, n = 6, L = 8, teacher seed 4, 64 training and 48 test points; SPSA with 60
  iterations, batch 8, 400 shots; FakeFez with TOQB noise.
- **Why this task:** it was chosen on a noiseless SPSA check only. Teacher 4 learned from 0.375 to 0.708 in 60
  iterations. At L = 4 the test points started at 0.875 and the loop did not learn.
- **The arms:** Qiskit level 2's template and PSF-Zero's template.
  - Qiskit level 3's template was left out: at this size it had the same two-qubit count as level 2.
  - The front end was Qiskit. The template arms give identical results through PennyLane (smoke b).

## What came out

**Every output was valid.** Three equivalence checks per arm and seed passed, with no structural failure and no
operation on a failed element.

**The circuits.**

| arm | two-qubit gates | duration |
|---|---|---|
| PSF-Zero | 120 | 8.71 µs |
| Qiskit level 2 | 158 | 18.11 µs |

PSF-Zero's circuits are 0.48 x as long.

**The loop.** Accuracy and margin on the 48 test points, at the start and after 60 iterations. "Noiseless" is the
accuracy the final angles would give without noise.

| seed | arm | start | final, noisy | final, noiseless | final margin |
|---|---|---|---|---|---|
| 11 | PSF-Zero | 0.354 | **0.781** | 0.750 | 0.188 |
| 11 | Qiskit level 2 | 0.344 | 0.385 | 0.542 | -0.019 |
| 12 | PSF-Zero | 0.271 | **0.625** | 0.604 | 0.034 |
| 12 | Qiskit level 2 | 0.219 | 0.469 | 0.438 | -0.016 |

**The money.** Batch mode, whole training: $226.54 for PSF-Zero, $232.31 for Qiskit. Session mode: $230.23 against
$235.08. The same budget, to within 3%.

**Reference.** The classical models reach 0.729-0.771 on the same points.

## Reading

**The difference.**

- In both seeds, PSF-Zero's loop learned and Qiskit's barely did.
- The noiseless accuracy of the final angles differs too: 0.750 against 0.542, and 0.604 against 0.438. So the
  difference is not only the noise at evaluation. The training itself went further.
- That is the compounding the scenario was built to see. Each of the 960 circuits of a run is half as long, so every
  gradient is less noisy.

**What two seeds cannot show.**

- Two seeds do not establish it. Seed 12's PSF-Zero run ended at 0.625, so the spread between seeds is large.
- A scored run with more seeds and predictions fixed in advance is needed. Its size can now be set from this pilot:
  one run takes about 5 minutes per arm on the home machine.

**On the classical reference.**

- PSF-Zero's seed-11 model (0.781) is level with the classical models (0.729-0.771) on 48 points. Seed 12's is below
  them.
- Nothing here says a quantum model beats a classical one.

**On the noise model.** It is built from the same Target that Qiskit's passes read, which favours Qiskit if anything
(principle 6).
