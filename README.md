# TOQB: Task-Oriented Quantum Benchmark

TOQB compares quantum compilers on the quality of what they return within a time budget, from the circuit's
structure to a task's accuracy on a noisy device.

**Status (2026-10-30).** The specification, a budgeted runner and the standard compilation set (layer 1) are as in
v0.1. Layer 3's variational-loop scenario has had scored runs at 6 qubits (below). Since 2026-10-22 the work has moved
to **declared tests on IBM devices**: how much of a circuit's signal each placement keeps, and how deep it stays
readable, when no placement reads the calibration's quality numbers ([Device results](#device-results-no-calibration-map)).
Layer 2 as specified (stale calibrations, estimated success probability) is not built as a standard set; its
questions are answered by the device tests instead.

**The standard since 2026-10-29: no calibration map.** A placement that reads only the coupling graph, the basis and
which elements have failed is *map-free*; this is how every arm is compared. A placement that reads error rates is
*map-aware*: a special condition, always labelled so. A classical computer has no daily map, and a map is stale
once read.

**Scored runs.** Each was pre-registered and its lock pushed before it ran.

- Standard run 1, [`results/standard-run-1/`](results/standard-run-1/).
- Standard run 2, [`results/standard-run-2/`](results/standard-run-2/).
- Loop standard run, 6 qubits, 8 layers, [`results/loop-n6-standard-2026-10-15/`](results/loop-n6-standard-2026-10-15/).
- Loop standard run 2, 6 qubits, 8 layers, 200 seeds, [`results/loop-n6-standard-2-2026-10-15/`](results/loop-n6-standard-2-2026-10-15/).
- Loop budget run, 6 qubits, 8 layers, 2 minutes of QPU, 1,000 seeds, [`results/loop-n6-budget-2026-10-16b/`](results/loop-n6-budget-2026-10-16b/).
- Loop reach run, 6 qubits, 8 layers, 1,000 iterations, 200 seeds, [`results/loop-n6-reach-2026-10-16/`](results/loop-n6-reach-2026-10-16/).

Numbers from this repository should be cited from these results, with their run.

## Device results (no calibration map)

Every device test was declared (SHA-256 and CET time, in [`prereg/`](prereg/)) before its calibration was fetched.
No mitigation, dynamical decoupling or twirling. Predictions that failed are reported as failed.

**Noise wall, stage 1 (2026-10-29), two devices.** The kicked-Ising ring (J = pi/4, h = 0.6; exact answer at any n)
at n = 20 and 36, L = 24, 50, 100 steps (up to 3600 CZ per circuit). Probe: a weight-2 charge conserved by the circuit
itself, read with four inputs that cancel readout and first-order relaxation; no calibration data used. Arms:
`fold:rule` (the ring on a lattice cycle, by formula), `fold:zipcyc` (the zipper on the same qubits) and
`qiskit:2:blind:template` (Qiskit level 2 given the coupling map and basis only). L* is the 1/e decay length.

| | marrakesh n = 20 | marrakesh n = 36 | kingston n = 20 | kingston n = 36 |
|---|---|---|---|---|
| L*, rule | 56.5 | 56.6 | 81.3 | 89.7 |
| L*, zipper | 15.1 | 15.7 | 22.6 | 25.6 |
| L*, blind Qiskit | 26.4 | 15.7 | 22.0 | 17.0 |
| rule's lead (Delta L) against zipper / blind Qiskit | +41 / +30 | +41 / +41 | +59 / +59 | +64 / +73 |
| rule wins on the charge (2 SE) | 6/6 | 6/6 | 6/6 | 6/6 |

- **Benchmark number:** the rule won all 24 comparisons and stayed readable 30-73 steps deeper.
- **Device user's number:** at n = 36, L = 100 the rule's charge was 0.178 +- 0.006 (marrakesh) and 0.314 +- 0.006
  (kingston); the others' were zero within 2 SE.
- **Failed declared predictions:** one depolarizing rate did not describe the decay on either device (shot-noise-only
  tolerance; rates scatter by 10-20 % between depth segments); the rule's size independence held on marrakesh but not
  on kingston; the zipper's penalty was 3.5-3.7 times the rule's decay rate on both devices, not the 2.2-2.4 its gate
  count and duration predict; the single-qubit output probe (P2, 250 shots) was at the noise floor.
- **Fixed after the run (post-hoc, to be declared next):** the rule's own L = 24 point with a +-20 % rate band (8/8);
  a constant zipper penalty of 3.6 +- 0.3 (4/4, and 4/4 when fitted on one device and applied to the other). A
  map-aware formula (median CZ error of the ring) failed across devices (1/4).
- Results: [`results/noise-wall-1-marrakesh-2026-10-29/`](results/noise-wall-1-marrakesh-2026-10-29/),
  [`results/noise-wall-1-kingston-2026-10-29/`](results/noise-wall-1-kingston-2026-10-29/) (figure
  `declared_vs_fixed_two_devices.png`).

**Tests 2 and 3, QELM A (2026-10-30), two devices** ([`results/device-2026-10-30/`](results/device-2026-10-30/)).
- Mirror echo with a longitudinal field hz = 0, 0.1, 0.3 (non-integrable for hz > 0), n = 20, 36, 40, 72: the rule
  against zipcyc and blind Qiskit, 71 wins, 11 ties, **0 losses**, 62 not judged (both on the floor). The rule's
  echo at D = 24 is 0.17-0.44 and does not shrink with n; the twin's volume prediction (below 2 SE at n = 40, 72)
  failed. Rule B (zipcyc's kappa 3.3-3.9) came out BELOW (kappa 1.7-2.7) wherever it could be judged.
- Global parity (weight n): the rule's V* below the declared value in 3 of 4; at n = 40 and above the readout
  reference collapses, so the parity's size wall is readout. Longest exact ring: kingston n = 88 (rho 0.22 +- 0.10).
- QELM task A (kingston, n = 20, search-free classifier): all arms inside their declared bands; rule 0.810 at
  S = 250 (ceiling 0.840) beats zipcyc at S = 64 and 250 (McNemar, Holm).

**Earlier device tests** (ibm_kingston unless noted; each folder's README has the declaration, jobs and verdicts):

| test | date | what | result |
|---|---|---|---|
| [D6](results/device-d6-2026-10-28/) | 10-28 | ring classifier, L = 16, n = 13-24; rule, zipper, blind Qiskit; no simulator | rule against blind Qiskit: 11 wins, 1 tie, 0 losses; against the zipper (even n): 3 wins, 3 ties |
| [D5 part A](results/device-d5a-2026-10-28/) | 10-28 | n = 20, the same qubits; **map-aware** Qiskit (special condition) | rule 0.943 +- 0.044, zipper 0.600 +- 0.044 (win), map-aware Qiskit 0.765 +- 0.099 (tie) |
| [D4](results/device-d4-2026-10-28/) | 10-28 | kicked Ising ring, n = 20, L = 100 | device 0.022 +- 0.011 against twin 0.028: agree |
| [D3](results/device-d3-2026-10-28/) | 10-28 | kicked Ising ring, n = 20, L = 24 | device 0.186 +- 0.022 against twin 0.247: below |
| [D2](results/device-d2-2026-10-26/) | 10-26 | the folded ring on ibm_fez against the day's twin | 0.50 +- 0.10 against 0.59 |
| [D1](results/device-d1-2026-10-26/) | 10-26 | the folded ring against the day's twin | 0.90 +- 0.12 against 0.77 |
| [C r9](results/device-2026-10-22/) | 10-22 | design C's device day | see the folder |

Twin accuracy over six device points: device / twin = 0.75-1.18, with no fixed sign. The twin is used for rankings,
with a +-20 % band on values, and is always built from the day's calibration.

Papers that use these results: PSF-Zero's Paper 4 (formula schedules on heavy-hex) and the draft of Paper 5
(readable depth without the calibration map), in [psf-zero `docs/papers/`](https://github.com/TN-Holdings-LLC/psf-zero/tree/main/docs/papers).

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
   calibration, so it favours them. The calibration split reduces this. Since 2026-10-22, short declared runs on IBM
   devices (ibm_kingston, ibm_marrakesh, ibm_fez) carry the main results; see
   [Device results](#device-results-no-calibration-map). Qiskit arms run on devices only, never in long simulations.

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
- **A fast engine** (`"engine": "fast"`, `toqb.fast_noise`, prototype 2026-10-15). It runs the same noise model
  about 13 x faster per run, for many seeds.
  - **How:** the noisy circuit is scheduled once per structure, evolved exactly as a density matrix with numpy
    (batched, one-qubit runs fused), and the shots of clbit 0 are drawn from the exact probability.
  - **Checked:** against an exact `qiskit.quantum_info` evolution to 1e-14, and against Aer to 1e-7 in the
    probability (Aer itself is off the exact value by about 1e-9 per element). PSF-Zero's and Qiskit's arms, 4 and
    6 qubits ([`results/fast-engine-check-2026-10-15/`](results/fast-engine-check-2026-10-15/)).
  - **Not yet used in a scored run.** Its random stream differs from Aer's, so a run is not bit-identical to an
    Aer run with the same seeds.
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
- **Pilot and scored run** (6 qubits, 8 layers, Qiskit level 2's template against PSF-Zero's):
  - [`results/loop-pilot-n6-2026-10-15/`](results/loop-pilot-n6-2026-10-15/), two seeds, unscored;
  - [`results/loop-n6-standard-2026-10-15/`](results/loop-n6-standard-2026-10-15/), 20 seeds, pre-registered.
    - For the same money, PSF-Zero's model was more accurate on the noisy device: 0.549 against 0.471, better in 16
      of 20 seeds (confirmed).
    - That the training itself went further was not decided: +0.040 noiseless, p = 0.059.
    - Both models are weak (no seed reached 0.7; classical models 0.73-0.77).
  - [`results/loop-n6-standard-2-2026-10-15/`](results/loop-n6-standard-2-2026-10-15/), 200 seeds, pre-registered,
    SPSA calibrated so that the models learn (fast engine).
    - **No difference in accuracy:** 0.702 against 0.701, noiseless -0.000 (95% interval +-0.014). The primary
      prediction was refuted.
    - **The difference does not grow with training** (refuted).
    - **PSF-Zero's signal is 1.32 x larger** (margin 0.206 against 0.156, confirmed), for 2.5% less money.
    - So for a classifier trained this way the compiler does not matter. Where the value of <Z> is used, it may.
  - [`results/loop-n6-budget-2026-10-16b/`](results/loop-n6-budget-2026-10-16b/), 1,000 seeds, pre-registered, a
    hard budget of 2 minutes of QPU ($192), run 1's SPSA.
    - **PSF-Zero's model is better at the budget:** noisy 0.533 against 0.494 (+0.039), noiseless +0.026, better in
      624 of 1,000 seeds; every prediction confirmed. It trains 50 iterations against 49 and its circuit is half as
      long (8.7 us against 18.1 us).
    - **Both models are weak at this budget:** 54 and 23 of 1,000 reached 0.7; classical models 0.73-0.77.
  - [`results/loop-n6-reach-2026-10-16/`](results/loop-n6-reach-2026-10-16/), 200 seeds, pre-registered, 1,000
    iterations, test accuracy every 50.
    - **PSF-Zero's model reaches a target sooner and cheaper:** to 0.65 in a median 200 iterations against 250 ($755
      against $968), to 0.70 in 300 against 400 ($1,133 against $1,549); every prediction confirmed.
    - The accuracy curve stays above Qiskit's up to 1,000 iterations (0.724 against 0.704).

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
  fold.py       formula placements of a ring on heavy-hex (fold:rule, fold:zipcyc, holes, pendants)
  lam_device.py the signal-on-the-device test: build, rehearse and score the kept signal (lam) per arm
  s2rc_device.py  device steps: fetch the day's Target, assemble one job, submit, fetch results (IBM key at home only)
  kising.py     kicked Ising ring at J = pi/4: circuits and the exact (and exactly noisy) free-fermion answer
  kising_formula.py  the formula prediction of the device slope from one depolarizing rate
  kising_charge.py   noise wall probe P1: the conserved weight-2 charge, readable depth L*, Delta L, kappa
gpu/            run scripts for pods and home builds (device_d6.sh, noise_wall_1.sh, ...)
examples/       pennylane_spsa.py: the loop task trained from PennyLane
prereg/         pre-registrations of scored runs and declarations of device tests (drafts-YYYY-MM-DD/)
tests/          tests that need no quantum package
```

## License

Apache License 2.0.
