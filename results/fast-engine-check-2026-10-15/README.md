# The fast engine, checked (2026-10-15)

`toqb.fast_noise` runs TOQB's loop noise model without asking Aer for counts circuit by circuit (`"engine": "fast"`
in a plan). This folder checks that it is the same physics and measures what it saves. It is a prototype and has not
been used in a scored run. Times are CEST. The work was done in the authors' cloud workspace, on 2 cores, with
Qiskit 2.5.2 and Aer 0.17.2.

## 1. The same noisy circuit, evolved exactly

[`check.json`](check.json), from `python -m toqb.check_fast_noise check.json 20`.

**What was compared.** Random angles, the loop's model circuit, compiled by:

- PSF-Zero's template (a22 + c61);
- Qiskit level 2's template;
- Qiskit level 2's recompile arm.

At n = 6, L = 8 and n = 4, L = 2: 20 circuits per template cell and 5 per recompile cell.

| check | worst over all 90 circuits | required |
|---|---|---|
| the engine's density matrix against an exact `qiskit.quantum_info` evolution of the same noisy circuit, with the errors of the noise model Aer is given | 8.7e-15 | 1e-12 |
| the engine's p1 of clbit 0 (readout included) against Aer's | 8.1e-8 | 1e-6 |
| the batched path the loop uses against one program per circuit | 4.4e-15 | 1e-12 |

- The engine matches the exact evolution to rounding.
- Aer is the one that differs: up to 4.7e-9 per density-matrix element from the same exact evolution.
- Shots are drawn as a binomial from the exact p1. For one clbit this has the same distribution as Aer's counts, but
  not the same random stream.

## 2. A whole scored run again, with the fast engine

[`std_compare.json`](std_compare.json): the 20 plans of the loop standard run
([`../loop-n6-standard-2026-10-15/`](../loop-n6-standard-2026-10-15/)), changed only by `"engine": "fast"`.

| | fast engine | Aer (the scored run) | engine difference, paired |
|---|---|---|---|
| PSF-Zero, final accuracy, noisy | 0.518 | 0.549 | -0.031 (p = 0.23) |
| Qiskit level 2, final accuracy, noisy | 0.479 | 0.471 | +0.008 (p = 0.74) |
| PSF-Zero, final accuracy, noiseless | 0.574 | 0.552 | +0.022 (p = 0.34) |
| Qiskit level 2, final accuracy, noiseless | 0.534 | 0.512 | +0.022 (p = 0.43) |
| wall time per seed, both arms | **41.5 s** (2 at a time, cloud) | 968 s (10 at a time, home); about 645 s alone (pilot) | |

**Reading.**

- No engine difference is distinguishable from the shot noise.
  - The shots differ, so SPSA follows another path from the first iteration.
  - Only the distributions can agree, and they do.
- **A run costs about 15 x less.** At 41.5 s per seed, 1,000 seeds of this run take about 70 minutes on ten
  processes.

**What the replicate says about the scored run.** It is not a new result: the scored run stands as scored. But it shows
how much a result moves with the shot stream alone.

| difference, PSF-Zero minus Qiskit | fast engine | Aer (scored) |
|---|---|---|
| noisy | +0.039 (better in 15 of 20) | +0.078 (better in 16 of 20) |
| noiseless | +0.040 | +0.040 |

- The noiseless difference is the same, +0.040.
- The noisy difference halves.
- So the scored run's split of its noisy difference into "half training, half evaluation" is not robust. With
  models near chance, many test points sit close to the decision boundary, and 400 shots flip them at random.

**Hence the next step:** many more seeds, which the fast engine now allows. The training settings will be chosen
first, on noiseless runs.

## Where the time goes now

Per arm of a 60-iteration run, about 22 s:

- simulation 12.5 s, about 10 ms per circuit (Aer's path: about 330 ms per circuit with its scheduling);
- the structure checks 4 s;
- compilation 2-3 s.

The structure checks (structural check, gates on failed elements, two-qubit count, duration) are computed for the
first three circuits of each structure, required equal, then reused. This is done only with the fast engine.
