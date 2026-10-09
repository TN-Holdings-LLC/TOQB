# TOQB: Task-Oriented Quantum Benchmark

TOQB compares quantum compilers on the quality of what they return within a time budget, from the circuit's
structure to a task's accuracy on a noisy device.

**Status: v0.1.** It has the specification, a budgeted runner and the standard compilation set (the layer-1
circuits, below). The first scored run is pre-registered in
[`prereg/2026-10-08-standard-run-1.md`](prereg/2026-10-08-standard-run-1.md). Layers 2 and 3 are not built yet. No
number from this repository should be cited until a scored run's results are committed.

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
prereg/         pre-registrations of scored runs
tests/          tests that need no quantum package
```

## License

Apache License 2.0.
