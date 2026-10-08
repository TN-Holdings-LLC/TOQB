# TOQB: Task-Oriented Quantum Benchmark

TOQB compares quantum compilers on the quality of what they return within a time budget, from the circuit's
structure to a task's accuracy on a noisy device.

**Status: v0, a draft.** It has the specification and a budgeted runner. Nothing has been scored yet, and no
number from this repository should be cited.

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
     least 0.05 s, so that the tiers stay apart on circuits it compiles in a few milliseconds.
2. **A timeout is a failure, and it is counted.** The first number reported is the share of circuits a compiler
   returned within budget. Quality is compared on the circuits that every compiler returned within budget.
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
| standard | under 2 hours | about 140 circuits at all tiers; 20 hardware-fitness circuits; task layer on 2 datasets x 3 depths x 3 training seeds |
| full | under a day | standard plus large circuits, more depths and the variational-loop scenario |

## How a measurement is made (`toqb/runner.py`)

- **One process per (compiler, circuit).** The process uses one thread (OpenMP, BLAS, Rayon and Qiskit's
  parallelism are switched off). Import and device loading are not timed.
- **Repeats.** One warm-up compile is discarded. Then there are five timed compiles; the fastest and the slowest are
  dropped and the rest averaged.
- **Limits.** A compile that exceeds ten times the budget is stopped, and the whole process has a wall-clock limit.
- **Checked, outside the timed part.**
  - Structure: every gate is in the device's basis and every two-qubit gate is on a coupled pair.
  - Equivalence: the input and the output are simulated from |0...0> and from three random product states, with
    each input qubit placed where the compiler put it at the start and read where it is at the end. A state
    infidelity above 1e-6 is "not equivalent". Outputs that touch more than 12 qubits, and inputs that measure or
    reset mid-circuit, are reported as not checked.
- **Recorded.** The machine, the versions, every time, whether the result was within budget, the output's metrics and
  the checks.

## Adapters (`toqb/adapters.py`)

A compiler takes part through an adapter with two methods:

- `version()`;
- `compile(circuit, device)`, which returns a circuit for `device`.

The built-in adapters cover Qiskit (any level, with or without the target), TKET (the default compilation pass of
pytket-qiskit's IBM backend at the given optimisation level, built offline from the device's map and gate set) and
PSF-Zero (its default call, and its recommended call when the device has a target). An external one can be
named as `package.module:factory`. The adapter receives exactly the device information its division allows.

## Layout

```
toqb/
  adapters.py   compiler adapters (Qiskit, TKET, PSF-Zero, external)
  devices.py    devices: IBM fake backends and abstract maps; failed elements
  cases.py      circuit sources (v0: a small built-in set)
  metrics.py    structural check and metrics of an output
  runner.py     the budgeted runner (one process per measurement)
tests/          tests that need no quantum package
```

## License

Apache License 2.0.
