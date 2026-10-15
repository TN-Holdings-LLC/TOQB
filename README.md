# TOQB: Task-Oriented Quantum Benchmark

TOQB compares quantum compilers on the quality of what they return within a time budget, from the circuit's
structure to a task's accuracy on a noisy device.

**Status: v0.1.** It has the specification, a budgeted runner and the standard compilation set (the layer-1
circuits, below). Layer 2 is not built yet. Of layer 3, the variational-loop scenario exists at smoke size (v15,
below); it has not had a scored run.

**Scored runs.** Each was pre-registered and its lock pushed before it ran.

- Standard run 1, [`results/standard-run-1/`](results/standard-run-1/).
- Standard run 2, [`results/standard-run-2/`](results/standard-run-2/).

Numbers from this repository should be cited from these results, with their run.

**Contamination notice (2026-10-10).** In runs 1 and 2, some outputs on FakeTorino placed gates on couplers the
device reports as failed. They are unusable on the device, and they were scored. That includes 5 of the
reference's 18 outputs and 10 of PSF-Zero's default call. Figures that count them are contaminated; see
[`results/CONTAMINATION.md`](results/CONTAMINATION.md). From v14 on, such an output is scored as a failure, and
results are given twice: as scored, and as a user who runs them on the device sees them.

## Why another benchmark

Existing compiler benchmarks measure structure, such as two-qubit gate count, depth and compile time. Benchpress is
one example. Structure matters, because every two-qubit gate adds error on hardware. But structure does not show
three things:

- whether a compiler avoids the parts of a device that are failing;
- whether its choices survive a calibration that is out of date;
- whether a better circuit changes the answer a task gets from the device.

Successful AI benchmarks (MLPerf, DAWNBench, ARC Prize, HELM) pair a quality target with a time or cost budget. A
benchmark that measures quality alone, or speed alone, can be won by giving up the other. TOQB applies that to
compilers.

## Principles

1. **Quality within a time budget.**
   - Every compiler gets the same budget per circuit.
   - The budget is a multiple of the reference compiler's time on the same circuit, not a fixed number of seconds.
     So results do not depend on the machine.
   - The reference is Qiskit `optimization_level=2`, as Benchpress calls it.
   - There are three tiers: **1x**, **3x** and **10x** the reference's time. The reference's time is taken as at
     least 0.05 s, so that the tiers stay apart on circuits it compiles in a few milliseconds. No budget exceeds
     600 s: a compiler that needs more than ten minutes for one circuit has failed it, whatever the reference took.
2. **A timeout is a failure, and it is counted.** The first number reported is the share of circuits a compiler
   returned within budget. Quality is compared with the reference's on the circuits a compiler returned within
   each tier's budget, and across all compilers on the circuits that every one of them returned within 10x.
3. **Three layers, each measured the same way for every compiler and task:**

   | layer | what is measured |
   |---|---|
   | 1. compilation | two-qubit gate count and depth, circuit duration, compile time |
   | 2. hardware fitness | gates placed on failed elements; estimated success probability; quality when the calibration is stale |
   | 3. task | classification margin and accuracy at fixed shot budgets, flipped predictions, device time to an accuracy |

   An output that is not executable on the device (structural check), or not equivalent to its input, is a failure,
   not a penalty.
4. **Neutrality rules.**
   - **Calibration split.** The calibration a compiler reads is not the noise it is scored with. Every task is
     scored with the device's true noise, and compilers are also given stale calibrations. The difference between
     the two is reported as "the value of knowing the calibration".
   - **Reference compilers.** Qiskit levels 1, 2 and 3 (with the device's target) and TKET. Others can be added
     through the adapter interface (below).
   - **Two divisions.** In **closed**, the inputs, the trained parameters and the device information are taken as
     given, with one compiler configuration for every task. In **open**, retraining, noise-aware training and
     parallelism are allowed if they are disclosed.
   - **A held-out set.** Scored circuits and data splits are drawn by rules from seeds that are published only after
     a version's results.
   - **Pre-registration.** Predictions and scoring scripts are fixed by hash before a scored run. An independent
     script re-scores every run.
   - **Everything is published,** including timeouts, invalid circuits and undecided verdicts.
5. **Conflict of interest, disclosed.** TOQB is written by the authors of the PSF-Zero compiler. PSF-Zero takes part
   as one participant, never as the reference. Its known weaknesses under these rules are listed in the results like
   anyone else's.
6. **Hardware.** Simulation on fake devices shares its noise model with any compiler that reads the device's
   calibration, so it favours them. The calibration split reduces this. Small runs on real hardware are planned after
   the first standard run.

## Sizes

| size | target time on one 8-core machine | contents |
|---|---|---|
| smoke | under 10 minutes | one circuit per stratum, the 3x tier only |
| standard | under 2 hours | 126 circuits at all tiers; 20 hardware-fitness circuits; task layer on 2 datasets x 3 depths x 3 training seeds |
| full | under a day | standard plus large circuits, more depths and the variational-loop scenario |

## The standard compilation set

- **Population.** These are Benchpress's transpilation tests that its authors have published results for: 1,032 at
  Benchpress commit `b695f30`. They are built as Benchpress's Qiskit gym builds them, with the same input circuit and
  the same backend (`toqb/benchpress_source.py`).
- **Exclusions.** The 152 tests that PSF-Zero's development used are left out (`toqb/data/psf_zero_dev_tests.txt`),
  because PSF-Zero's author also wrote TOQB.
- **Sample.** Each stratum (QASMBench small, medium and large on four maps; HamLib on four maps and on FakeTorino;
  Feynman on FakeTorino) contributes a fixed number of tests, 126 in all. They are chosen by a hash of a secret seed.
  The seed's commitment, `sha256("TOQB-seed|" + seed)`, is in `plan_standard.json` before the run. The seed itself is
  published after the run, so anyone can check that the sample was drawn as declared.
- **Calibration.** Abstract maps carry no calibration, so no compiler receives a Target on them. On FakeTorino every
  target-aware compiler receives the device's Target.
- **Smoke run.** `plan_bp_smoke.json` uses five tests from PSF-Zero's development set, never ones from the sample.

## How a measurement is made (`toqb/runner.py`)

- **One process per (compiler, circuit).** The process uses one thread (OpenMP, BLAS, Rayon and Qiskit's
  parallelism are switched off). Import and device loading are not timed.
- **Repeats.** One warm-up compile is discarded. Then there are five timed compiles; the fastest and the slowest are
  dropped and the rest averaged. If the warm-up takes longer than 2 s, a single timed compile follows instead, because
  long compiles vary little from run to run.
- **Circuit breakers.** Nothing is measured past what the score needs.
  - A compile is stopped at the largest budget (the warm-up, which is cold, 30 s later): the measurement has failed.
  - The reference's compiles stop at 600 s; a circuit without a reference time is left out of every score.
  - The equivalence check stops at 60 s; the output is then recorded as unchecked, not as a failure.
  - A measurement whose resident memory exceeds a fixed cap fails ("memory limit").
  - If the machine runs short of memory, the measurement using the most is stopped and run again alone at the end,
    so that the machine's limits are not counted against a compiler.
  - A run has a time budget. A bound on its time is computed once the reference's times are known, and the run stops
    there if the bound exceeds the budget. A file named `STOP` in the output directory also stops it. A stopped run
    is incomplete and is not scored.
- **Diagnostics, for finding what to fix (never scored, never timed).** Each record carries the input's features
  (qubits, instructions, two-qubit and wider instructions). A measurement that is stopped carries the stack its
  compiler was in, dumped just before the stop (Python frames, without the machine's paths).
  `python -m toqb.weakness DIR` groups failures by where they were stopped and by the input's features, lists the
  slow and the worse outputs, and gives for each group a command that reproduces its first case under a profiler
  (`runner one ... --profile FILE`, which writes the profile also when the compile is stopped).
- **Checked, outside the timed part.**
  - Structure: every gate is in the device's basis and every two-qubit gate is on a coupled pair.
  - Equivalence: the input and the output are simulated from |0...0> and from three random product states, with
    each input qubit prepared where the compiler put it at the start.
    - An input without measurements is compared as a state: each input qubit is read where it is at the end, and
      a state infidelity above 1e-6 is "not equivalent".
    - An input whose measurements are all at the end is compared by the probabilities of its measured bits, each
      bit read from the qubit the output measures into it. A total variation distance above 1e-6 is "not
      equivalent". Passes that act only on what is measured (removing a diagonal gate or a swap before a
      measurement) change the state but not these probabilities, so they are not penalised. Gates after the
      measurements that no later measurement depends on (TKET can leave a swap there) are left out of the
      comparison, counted as "trailing", and still counted in the output's gates.
    - The input is compared as the compiler read it. This differs from Qiskit's reading in one case: TKET builds its
      own first-order product formula for a `PauliEvolutionGate` (below), and is checked against that formula.
    - Outputs that touch more than 12 qubits, and inputs that measure or reset mid-circuit, are reported as not
      checked.
- **Recorded.** The machine, the versions, every time, whether the result was within budget, the output's metrics and
  the checks.

## Adapters (`toqb/adapters.py`)

A compiler takes part through an adapter with two methods:

- `version()`;
- `compile(circuit, device)`, which returns a circuit for `device`.

The built-in adapters cover Qiskit (any level, with or without the target), TKET (the default compilation pass of
pytket-qiskit's IBM backend at the given optimisation level, built offline from the device's map and gate set) and
PSF-Zero (its default call, and its recommended call when the device has a target).

A `PauliEvolutionGate` (the HamLib circuits) is read by each compiler its own way, as Benchpress lets each SDK build
its own Hamiltonian circuit. Qiskit expands it as a product formula with the terms in the given order. The TKET
adapter builds TKET's own product formula (`gen_term_sequence_circuit`, which groups the terms into commuting sets),
with Qiskit's conventions for the gate: U = exp(-i t H), and character k of a Pauli label acts on the gate's qubit
n-1-k. Both are first-order formulas for the same Hamiltonian. They differ in term order, and so in Trotter error. An external one can be
named as `package.module:factory`. The adapter receives exactly the device information its division allows.

## The variational-loop scenario (v15, smoke size): for the same money, which compiler returns the best model?

A quantum classifier is trained by a loop, and every circuit of every iteration goes through the compiler. The
compiler's output noise enters every gradient, and its compile time is spent again on every iteration. TOQB prices
both as an IBM user pays them, in QPU seconds and dollars, and asks which compiler gives the best model for the same
money. `toqb/task_loop.py` runs it. A QML developer can run the same thing from PennyLane.

- **Task.**
  - Data re-uploading on a CZ ring, read from qubit 0 (the classifier PSF-Zero's hardware runs used).
  - The data are a teacher-student task: a teacher of the same model, with angles drawn from a seed, labels uniform
    points. It is learnable by construction, and needs numpy only.
  - Training is SPSA on a batch; each iteration is one job of 2 x batch circuits. The initial angles, the batches and
    the perturbations are drawn before anything runs, so every compiler follows the same draws.
- **Device model ("TOQB noise").** Each output is scheduled with the device's durations, so idle time becomes delays.
  It is then run on Aer's density-matrix simulator with three errors from the device's Target:
  - each gate's reported error, as depolarizing noise;
  - thermal relaxation over gates and delays;
  - the reported readout error.

  Shots use seeds fixed per circuit, the same for every compiler.
- **Price** (`qpu_cost` in the plan). The defaults are IBM's measured rate in PSF-Zero's TIME1 and FRAC1 runs (0.27
  ms per shot and 0.036 s per circuit, plus the circuit's own duration per shot), and the Pay-As-You-Go price ($96 per
  minute, billed per second).
  - **Batch mode** bills only time on the QPU.
  - **Session mode** bills the wall-clock time the QPU is committed to the session. That includes the classical time
    between jobs, so compiling, binding, the front end and the optimiser are paid at the QPU's price.

  TOQB's own checks, and the simulation that stands in for the QPU, are not priced.
- **The result for the money** (first in the report):
  - **The budget:** what the reference arm (`qiskit:2:target:template`, Qiskit's loop practice) spends on the whole
    training, plus 5%, in each mode.
  - **At that budget:** each arm's test accuracy and margin.
  - **Also:** the dollars each arm needs to reach the target accuracy, and the noiseless accuracy of its final angles.
- **Arms.**
  - **Template arms:** Qiskit with every angle a Parameter, transpiled once per circuit structure and bound for each
    circuit. PSF-Zero's AI front end, with `ring_template` built once and bound.
  - **Recompile arms:** the concrete circuit compiled every time.
- **Checks.** Every output is structurally checked and checked for failed elements. TOQB's equivalence check runs on
  the first circuit of the first, middle and last iteration.
- **Reference, not a contest: classical models and energy** (`toqb/classical.py`).
  - **Models:** logistic regression, with and without squares and products, a 32-unit MLP and 5 nearest neighbours.
    They use numpy only, one fixed configuration each, and are trained and scored on the same points.
  - **Energy of every row,** as a range in kWh:
    - a quantum run is charged the system's wall-plug power (10-25 kW, as cited in arXiv 2605.09580) for the seconds
      it holds the QPU;
    - every classical second is charged 10-50 W.

    These are assumptions, set in the plan's `energy`, not measurements.
  - **Why it is there:** TOQB compares compilers. It does not claim that quantum models beat classical ones. The
    reference shows where the bar is.

  From [smoke c](results/loop-smoke-2026-10-15c/) (4 qubits, 2 layers, 64 training and 24 test points):

  | row | test accuracy | time | energy (estimate) | money |
  |---|---|---|---|---|
  | classical: logistic regression | 0.917 | 0.05 s CPU | under 1e-6 kWh | - |
  | classical: MLP, 32 units | 0.958 | 0.24 s CPU | under 4e-6 kWh | - |
  | classical: logistic with squares and products | 1.000 | 0.06 s CPU | under 1e-6 kWh | - |
  | quantum, best compiler arm (batch mode) | 0.750 | 70 s on the QPU | 0.19-0.48 kWh | $112 |

- **Secondary:** the compile time per loop, in tiers of 1x, 3x and 10x the reference's, with a floor of 1 s.
- **From PennyLane.** `toqb.pennylane_device.CompiledDevice` is a PennyLane device.
  - **What it does:** a QNode's circuits are compiled by the chosen arm and run on TOQB noise.
  - **What it returns:** PennyLane's expectation values, probabilities or counts, from samples of every wire.
  - **Cost:** `qml.Tracker` reports the compile time, QPU seconds and dollars of every execution.
  - **In the loop:** with `"frontend": "pennylane"`, the loop itself builds PennyLane tapes and runs them through this
    device. The compilers receive the same Qiskit circuit as from the Qiskit front end; a test checks this.
  - **Example:** `examples/pennylane_spsa.py` trains the task with PennyLane's own SPSAOptimizer.
- **Limits.**
  - Smoke size: one task, one device, 30 iterations.
  - The noise model is built from the same Target that a calibration-aware compiler reads. That favours such
    compilers (principle 6). No calibration split yet.
  - Simulation only. The price is an estimate from measured rates, not a bill.
  - PSF-Zero's arms are written by PSF-Zero's authors (principle 5).
- **Results:** smoke runs in three folders:
  - [`results/loop-smoke-2026-10-15/`](results/loop-smoke-2026-10-15/), the first, before prices and PennyLane;
  - [`results/loop-smoke-2026-10-15b/`](results/loop-smoke-2026-10-15b/), with prices, through PennyLane;
  - [`results/loop-smoke-2026-10-15c/`](results/loop-smoke-2026-10-15c/), with the classical reference and energy.

```
PSF_ZERO_REPO=<a PSF-Zero checkout> python -m toqb.task_loop run plan_loop_smoke.json <new output directory>
PSF_ZERO_REPO=<a PSF-Zero checkout> PYTHONPATH=. python examples/pennylane_spsa.py psfai:template 10
```

## Layout

```
toqb/
  adapters.py   compiler adapters (Qiskit, TKET, PSF-Zero, external)
  devices.py    devices: IBM fake backends and abstract maps; failed elements
  cases.py      circuit sources (a small built-in set, and Benchpress tests)
  benchpress_source.py   Benchpress tests as cases and devices; the standard sample
  data/         the published Benchpress test ids; PSF-Zero's development tests (excluded)
  metrics.py    structural check and metrics of an output
  runner.py     the budgeted runner (one process per measurement)
  score.py      scores a standard run against its pre-registered predictions
  verify.py     an independent re-scoring of a standard run
  essential.py  v14: a run's results as scored and as a user of the device sees them (failed elements, first compile)
  task_loop.py  v15: layer 3's variational-loop scenario (task, SPSA, TOQB noise, prices, template and recompile arms)
  score_loop.py v15: the report of a loop run (the result for the money first)
  pennylane_device.py  v15: CompiledDevice, a PennyLane device that compiles with a TOQB arm and prices each execution
  classical.py  v15: classical reference models for the loop task (numpy only)
examples/       pennylane_spsa.py: the loop task trained from PennyLane
prereg/         pre-registrations of scored runs
tests/          tests that need no quantum package
```

## License

Apache License 2.0.
