# Pre-registration: TOQB standard run 1 (2026-10-08)

**Status: pre-registration.** This file, the scoring script [`toqb/score.py`](../toqb/score.py) and the independent
re-scoring [`toqb/verify.py`](../toqb/verify.py) are fixed by the commit that adds them. That commit is pushed to the
public repository before the run starts. The run is made once. Times are given in CEST.

The run measures six compiler configurations on TOQB's standard compilation set (layer 1: compilation). It is the
first scored run of TOQB. It is also the first time the authors' compiler, PSF-Zero, is measured on time budgets.

## 1. What is run

### Circuits

- **Population.** Benchpress's transpilation tests with results published by its authors, at Benchpress commit
  `b695f30`, minus the 152 that PSF-Zero's development used: 880 tests ([`toqb/benchpress_source.py`](../toqb/benchpress_source.py)).
- **Sample.** 126 tests, drawn per stratum by `sample()` from a secret seed.
  - The seed's commitment, `sha256("TOQB-seed|" + seed)`, was committed in
    [`plan_standard.json`](../plan_standard.json) by commit `1624363`:
    `01edf8fa0dcb16f96354c7d28bf7374e3dd861ff6639984c9e50f02091459e29`.
  - The seed is published with the results, so anyone can redraw the sample.
  - Per stratum: QASMBench small 8, medium 6 and large 6 on each of four maps; HamLib 7 on each of four maps;
    HamLib on FakeTorino 10; Feynman on FakeTorino 8.

### Compilers

| adapter | what it is | version |
|---|---|---|
| `qiskit:2:target` | the reference: Qiskit's preset pass manager at level 2, with the device's Target on FakeTorino | Qiskit 2.5.2 |
| `qiskit:1:target` | the same at level 1 | Qiskit 2.5.2 |
| `qiskit:3:target` | the same at level 3 | Qiskit 2.5.2 |
| `tket:2` | pytket-qiskit's IBM default compilation pass, optimisation level 2, built offline | pytket 2.18.5, pytket-qiskit 0.78.0 |
| `psf:default` | PSF-Zero's default call | release 2026-10-07.1 (PSF-Zero commit `79b70ad`) |
| `psf:recommended` | PSF-Zero's recommended call (its default call on maps without a Target) | the same |

### Settings and machine

- **Runner.** As [`toqb/runner.py`](../toqb/runner.py) is committed here:
  - one process per measurement, on one thread;
  - one warm-up compile, then five timed compiles, the fastest and slowest dropped (one timed compile after a
    warm-up longer than 2 s);
  - budgets 1x, 3x and 10x the reference's time, which is taken as at least 0.05 s;
  - a measurement is stopped at 10 times its largest budget;
  - `--lock`: the run stops if TOQB, PSF-Zero or Benchpress has an uncommitted change.
- **Machine.** The owner's home PC: Windows with WSL2, Python 3.12.13, 12 logical CPUs, NumPy 2.5.3,
  qiskit-ibm-runtime 0.49.0. Four measurements at a time (`--par 4`). Nothing else runs on the machine during the run.
- **Commands.**

  ```bash
  cd ~/toqb
  export TOQB_BENCHPRESS=~/benchpress PSF_ZERO_REPO=~/psf_zero_fresh_test
  python -m toqb.runner run --plan plan_standard.json --seed-file ~/.toqb_seed_v01 \
      --out ~/toqb_runs/standard-1 --par 4 --lock
  python -m toqb.score --out ~/toqb_runs/standard-1
  python -m toqb.verify --out ~/toqb_runs/standard-1
  ```

- **If the run is interrupted** (the machine sleeps, restarts or loses power), its partial records are kept and
  published. The whole run is started once more from the beginning, into a new directory, with the same commands.
  The second run is scored. This rule depends only on the interruption, not on any result.

## 2. Disclosures

1. **The population is the one PSF-Zero's last test used.** BP-FINAL (PSF-Zero record, Addenda 407 and 408) ran
   release 2026-10-07.1 on all 880 tests. PSF-Zero was not changed after it. So the sample is held out from tuning,
   not from evaluation, and BP-FINAL's public results ground prediction T2. A PSF-Zero version changed after
   BP-FINAL will not be held out from these tests in the same way.
2. **The authors of TOQB wrote PSF-Zero.** PSF-Zero takes part as one participant. The reference is Qiskit.
3. **Timing differs from BP-FINAL's.** BP-FINAL timed one cold compile, twelve at a time. TOQB times warm compiles on
   one thread, four at a time. The timing prediction (T3) is therefore loose.
4. **TKET reads a `PauliEvolutionGate` its own way.** The adapter builds TKET's own product formula
   (`gen_term_sequence_circuit`), with Qiskit's conventions for the gate. pytket-qiskit's own converter reads the gate
   with half the time and the Pauli qubit order reversed (found and checked on 2026-10-08). TKET's HamLib outputs are
   checked against TKET's own formula.
5. **Equivalence is checked only where the output touches at most 12 qubits.** Larger outputs count as usable
   unchecked.
6. **The sample is small.** 126 tests; 18 of them on FakeTorino.

## 3. Definitions

- **usable**: no error, structurally valid (every gate in the device's basis, every two-qubit gate on a coupled
  pair), and not "not equivalent". An unchecked output is usable.
- **within tier t**: usable, and its time is at most t times max(0.05 s, the reference's time on that test).
- **Q_all(A)**: the geometric mean of (two-qubit gates of A + 1) / (two-qubit gates of the reference + 1), over the
  tests where both outputs are usable, whatever the time. **Q_t(A)**: the same over the tests A returned within
  tier t.
- **Families**: QASMBench; HamLib on the four abstract maps; HamLib on FakeTorino; Feynman on FakeTorino.

## 4. Predictions

| ID | prediction | confirmed if | refuted if | basis |
|---|---|---|---|---|
| T1 | every output of every compiler is valid, and every checked one is equivalent | no invalid and no "not equivalent" output | any | the smoke runs of 2026-10-08 (all six compilers, after the checker's fixes) |
| T2 | PSF-Zero's default call uses a little more two-qubit gates than the reference | Q_all(psf:default) <= 1.07 | > 1.10 | BP-FINAL: 1.046 on the 880; 5,000 simulated draws of this sample from BP-FINAL's records give 1.035 (95% 1.020-1.056) |
| T3 | PSF-Zero's default call returns within 10x on almost every test | share within 10x >= 0.90 | < 0.80 | BP-FINAL's times give 0.97 on the population (simulated sample 0.968, 95% 0.937-0.992), with cold timings |
| T4 | PSF-Zero's recommended call places no two-qubit gate on FakeTorino's failed elements | 0 of the FakeTorino tests it returns | at least one | BP-FINAL F5: 0 of 105 |
| T5 | TKET uses more two-qubit gates than the reference | Q_all(tket:2) >= 1.05 | < 1.00 | the smoke run on five development tests (1.455); weak |
| T6 | PSF-Zero's default call rarely fails | fails on <= 2% of the tests the reference finishes | > 5% | BP-FINAL F6: 0.1% |

A value between the two thresholds is NOT DECIDED. Every "not equivalent" output is examined after the run. If the
checker is at fault, that is reported, and the verdict on T1 stands.

## 5. Reported without prediction

- For every compiler: the share within 1x, 3x and 10x; Q_all with a bootstrap 95% interval; Q_1x, Q_3x and Q_10x;
  the two-qubit depth ratio; the median time ratio to the reference; invalid, not equivalent, checked and failed
  counts; FakeTorino tests with gates on failed elements; trailing gates after the measurements.
- Q_all per family.
- Every compiler's ratio on the tests that all six returned within 10x.
- The run's wall time, against the target of 2 hours in the README.

## 6. After the run

- The records, `score.md`, `score.json`, the verify output, the run log and the seed are committed under
  `results/2026-10-08-standard-run-1/`, with a results note.
- Any deviation from this file is listed in the results note.
- Weaknesses the run shows, in any compiler including PSF-Zero, are listed there as findings.
