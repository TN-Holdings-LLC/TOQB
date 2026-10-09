# Amendment 1 to the pre-registration of TOQB standard run 1 (2026-10-09)

**Status: amendment to [`2026-10-08-standard-run-1.md`](2026-10-08-standard-run-1.md).** It is fixed by the commit
that adds it, pushed to the public repository before run 1c starts. Everything in the pre-registration stands except
what section 2 changes. The predictions T1-T6, their thresholds and the sample are unchanged; two definitions
change with the circuit breakers, and their effect is bounded (section 4). Times are given in CEST.

## 1. What happened

| run | started | stopped | measurements recorded | how it stopped |
|---|---|---|---|---|
| 1 (`standard-1`) | 2026-10-08 14:03 | 17:06 | 515 of 756 | the Linux of WSL stopped; Windows kept running |
| 1b (`standard-1b`), the one rerun the pre-registration allows | 17:59 | 21:07 | 537 of 756 | the same |

- **Order of the lock and the publication.** The lock commit `3a304f8` was pushed while the repository was still
  private (13:59). Run 1 started at 14:03, and the repository was made public at about 14:07.
- **Most likely cause: memory.** Both runs stopped about three hours in, at the same point of the run. At that point
  TKET was compiling the three largest circuits of the sample, three at a time:
  - bwt_n21 on the square and linear maps, and multiplier_n400 on the square map;
  - these circuits come out of the reference with 0.4-0.8 million two-qubit gates.

  During run 1 these TKET processes used 1.1-2.3 GB each after 30-45 minutes, and were growing. Linux under WSL had
  15 GB. This is not proven: the Linux system log is lost when WSL restarts.
- **Two records cut short in run 1b.** In `standard-1b/records.jsonl`, two records end early and the next record
  continues on the same line. Each is followed by a long gap in which nothing was written. The cause is not known.
  The other records are intact.
- **What was seen before this amendment.** The progress lines show each measurement's time and two-qubit count. The
  owner and Claude saw some of them, and examined TKET's errors and the records of both runs to find the cause.
  Nothing was scored.
- **And after its first draft.** On 2026-10-09, before this amendment was committed, two tools were run on the records
  of runs 1 and 1b: [`toqb/cap_effect.py`](../toqb/cap_effect.py) (section 3) and
  [`toqb/weakness.py`](../toqb/weakness.py). The weakness report lists, per compiler, its failures, the outputs over 3x
  the reference's time and those with over 10% more two-qubit gates than the reference. Claude and the owner saw
  both outputs. Nothing was scored; no prediction or threshold was changed after them.

## 2. Changes: circuit breakers

The runs measured far past what scoring needs. A compile was stopped only at 10 times the largest budget (100 times
the reference's time), and a measurement could make two such compiles. Whether an output is within 10x needs only
the first 10x. Both crashes happened in that unneeded part. The principle of this amendment: **nothing is measured
past what the score needs, every limit is fixed before the run, and a run that cannot finish within its budget does
not start.** [`toqb/runner.py`](../toqb/runner.py) implements it:

1. **The 10x tier is at most 600 s.** Budgets are min(t x max(0.05 s, reference), 600 s). A compiler that needs
   more than ten minutes for one circuit has failed it, whatever the reference took. This changes the tiers only on
   tests whose reference took more than 60 s (section 4).
2. **A compile stops at the largest budget.** The warm-up, which is cold, stops at the budget plus 30 s; the timed
   compiles at max(budget, 4 s), and the timed repeats end once their sum passes that. A stopped measurement fails
   ("time").
3. **The reference stops at 600 s.** A test without a reference time is left out of every score, as before; the
   other compilers are then not run on it, and their records say so ("not run").
4. **The equivalence check stops at 60 s.** The output is then recorded as unchecked, not as a failure.
5. **A memory cap of 3 GB per measurement.** The Linux of WSL has 15 GB: 3 GB are kept for the system, and 12 GB
   are shared by the four measurements running at a time. A measurement over the cap fails ("memory limit").
6. **A machine breaker.** If the machine's available memory falls below 1.5 GB, the running measurement with the
   most resident memory is stopped and run again alone after the others; the second result is the record, and the
   first is kept in `interrupted.jsonl`. The machine's limits are not counted against a compiler.
7. **A run budget of 10 hours.** Once the reference's times are known, a bound on the rest of the run is computed
   from the budgets. If it exceeds the run budget, the run stops there. No measurement starts after the run budget,
   or once a file named `STOP` is in the output directory. A stopped run is incomplete and is not scored.
8. **Memory is recorded:** each measurement's peak resident memory, a trace every 30 s for long ones, and the
   machine's available memory every 30 s (`memlog.tsv`). Each record is written to disk (fsync) before the next.
9. **Diagnostics, not scored.** Each record carries the input's features; a stopped measurement carries the stack
   its compiler was in just before the stop (dumped by Python's faulthandler, outside the timed compile's own work;
   paths are shortened to package and file). [`toqb/weakness.py`](../toqb/weakness.py) reads them after the run.
   They serve the authors' work on the compilers' weaknesses and change no number of the score.
10. **TKET adapter: a gate defined in the input is expanded before conversion.** In runs 1 and 1b, TKET failed on three
   tests because the adapter passed QASMBench's own gates (`ctu` in ipea_n2 on two maps, `add4` in bigadder_n18) to
   pytket-qiskit's converter, which does not take them. Benchpress's TKET gym reads these files with pytket's own QASM
   reader, which expands them. These were TOQB's failures, not TKET's.
11. **Classical control is still not supported by the TKET adapter.** Two tests (cc_n151 on all-to-all, cc_n64 on
    linear) fail in its conversion of the input or of the output. They are reported as failures of the adapter, not
    of TKET.
12. **Scoring** ([`toqb/score.py`](../toqb/score.py), [`toqb/verify.py`](../toqb/verify.py)). P0 also checks the
    breakers' settings and that the run is complete. Failures are split into time, memory, adapter and harness.
    T3 and T6 are reported with bounds (section 4).
13. **Run 1c.** The commands of the pre-registration, with `--mem-cap-gb 3` (the run budget is the default, 10 h) and
    the output in `~/toqb_runs/standard-1c`, started from a standalone WSL window that stays open:
    - **PSF-Zero at `79b70ad`** (release 2026-10-07.1, as the pre-registration names it), from a worktree
      (`PSF_ZERO_REPO=~/psf_zero_79b70ad`): the repository's main branch has moved on since, with records only; its
      compiler file is unchanged.
    - **The same environment** as runs 1 and 1b (Python 3.12.13, Qiskit 2.5.2, pytket 2.18.5, pytket-qiskit 0.78.0,
      qiskit-ibm-runtime 0.49.0, NumPy 2.5.3). pytest 9.1.1 was added to it for TOQB's tests; no run uses it.
    - If run 1c is interrupted or stopped, no scored result is claimed from this machine, and a further amendment
      decides.
14. **Runs 1 and 1b** are published with the results, as they are, and are not scored.

## 3. What the breakers would have changed in runs 1 and 1b

From [`toqb/cap_effect.py`](../toqb/cap_effect.py) on the records of runs 1 and 1b, made before this amendment was
committed:

- **Tests whose reference took more than 60 s:** one, multiplier_n400 on the square map (60.9 s in run 1, 74.3 s in
  run 1b). The cap of 600 s is below 10x the reference only there.
- **Measurements the breakers would have stopped** (time over the largest budget), among those recorded, run 1 / run
  1b:

  | compiler | run 1 | run 1b | the longest |
  |---|---|---|---|
  | tket:2 | 43 | 52 | square_root_n45 on square: 2,532 s against a largest budget of 130 s (run 1) |
  | qiskit:3:target | 2 | 2 | bv_n280 on square: 27-31 s against 1.8-2.7 s |
  | psf:recommended | 1 | 0 | cc_n64 on linear: 10.2 s against 8.3 s (run 1) |
  | psf:default, qiskit:1:target | 0 | 0 | |

- **The bound on run 1c** with these reference times: 6.0 h (run 1's) and 6.2 h (run 1b's), under the run budget of
  10 h. The bound assumes that every measurement reaches its limits.

## 4. Effect on the predictions

The predictions T1-T6, their thresholds and the sample are unchanged. Two definitions change with the breakers:
"within 10x" (item 1) and "fails" (item 2: a compile slower than its largest budget now fails, where the
pre-registration let it run to 10 times that). The breakers were decided after partial results of runs 1 and 1b had
been seen (section 1), so their effect is bounded rather than assumed:

- **T3** (PSF-Zero's default call within 10x): reported as measured, and with the bound obtained by counting as
  within 10x every one of its time failures on a test whose reference took more than 60 s.
- **T6** (its failures where the reference finished): reported as measured, and with the bound obtained by not
  counting its time failures.
- If the verdict is the same at both ends, it is the verdict. If not, it is "NOT DECIDED (the cap of amendment 1)".
- T1 is unaffected: a stopped measurement is a failure, not an invalid or a non-equivalent output.
- T2 and T5 count usable outputs whatever the time; an output the breakers stop is not usable, so it leaves Q_all
  rather than changing it. The number of such outputs is reported per compiler.
