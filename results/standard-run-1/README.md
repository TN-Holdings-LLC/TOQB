# TOQB standard run 1: results

**Status: the result of the first scored run of TOQB**, as pre-registered in
[`prereg/2026-10-08-standard-run-1.md`](../../prereg/2026-10-08-standard-run-1.md) and amended in
[`prereg/2026-10-09-standard-run-1-amendment.md`](../../prereg/2026-10-09-standard-run-1-amendment.md) (commit
`3bfc666`, public before the run). Scored by [`toqb/score.py`](../../toqb/score.py), re-scored independently by
[`toqb/verify.py`](../../toqb/verify.py). Times in CEST.

## The runs

| run | directory | started | ended | records | status |
|---|---|---|---|---|---|
| 1 | [`run-1/`](run-1/) | 2026-10-08 14:03 | 17:06 (the Linux of WSL stopped) | 515 of 756 | not scored (amendment 1) |
| 1b | [`run-1b/`](run-1b/) | 2026-10-08 17:59 | 21:07 (the same) | 537 of 756 | not scored (amendment 1) |
| **1c** | [`run-1c/`](run-1c/) | **2026-10-09 12:31** | **13:23** | **756 of 756** | **scored** |

Run 1c ran on TOQB `3bfc666`, PSF-Zero `79b70ad` (release 2026-10-07.1), Benchpress `b695f30`, on the home PC (WSL2,
12 CPUs, Python 3.12.13), four measurements at a time, with nothing else running. It took 52 minutes; the bound
computed after the references was 6.0 h. No measurement was interrupted by the machine breaker, and none hit the
memory cap of 3 GB (the largest peak was 2.2 GB, Qiskit level 3 on bwt_n21); the machine never had less than 9.5 GB
available (`memlog.tsv`).

In runs 1 and 1b, four error texts carried a local path; it is replaced by `/home/<user>` in the published records.
Nothing else in any record is changed.

**The seed.** The sample was drawn from the seed in [`seed.txt`](seed.txt), published now as the pre-registration
says. `python -m toqb.runner commit --seed-file results/standard-run-1/seed.txt` prints the commitment that
`plan_standard.json` carried before run 1.

## Score of run 1c ([`run-1c/score.md`](run-1c/score.md))

**P0 (integrity): PASS.** **Independent re-scoring: PASS** (756 records, 0 differences).

| ID | prediction | value | verdict |
|---|---|---|---|
| T1 | every output of every compiler is valid, and every checked one is equivalent | 4 outputs "invalid" for each of qiskit:2, qiskit:1, qiskit:3, psf:default and psf:recommended; none for tket:2; no checked output not equivalent | **REFUTED** |
| T2 | psf:default Q_all <= 1.07 (REFUTED > 1.10) | 1.012 (95% 1.004-1.021) | **CONFIRMED** |
| T3 | psf:default within 10x >= 0.90 (REFUTED < 0.80) | 0.968; the same under the pre-registration's own stopping | **CONFIRMED** |
| T4 | psf:recommended places no two-qubit gate on FakeTorino's failed elements | 0 of 17 | **CONFIRMED** |
| T5 | tket:2 Q_all >= 1.05 (REFUTED < 1.00) | 1.145 (95% 1.073-1.244) | **CONFIRMED** |
| T6 | psf:default fails on <= 2% of the tests the reference finishes (REFUTED > 5%) | 0.000; the same under the pre-registration's own stopping | **CONFIRMED** |

The one test whose reference took more than 60 s (multiplier_n400 on the square map) changed no verdict: the bounds
of amendment 1 are equal at both ends for T3 and T6.

## Two things the score does not show

**1. T1 was refuted by TOQB's own structural check, not by a compiler.** The 20 "invalid" outputs are the same four
measurements for each of the five Qiskit-based outputs: ipea_n2 on the square and heavy-hex maps, cc_n151 on
all-to-all and cc_n64 on linear. Their inputs use classical control (gates conditioned on measured bits). Qiskit
and PSF-Zero keep it as `if_else`, and the structural check rejects `if_else` as "not in the basis": it rejects the
reference's own outputs. T1 is REFUTED as defined, and stays so. On the other 123 tests every output of every
compiler was valid, and no checked output was not equivalent. Amendment 1 named two tests with classical control
(cc_n151, cc_n64); ipea_n2 has it too: TKET's adapter now converts its input (the gate defined in it is expanded)
but fails on TKET's output (`RangePredicate`). The next version of the structural check accepts control flow whose
bodies are in the basis.

**2. Two measurements probably failed because of TOQB's diagnostics.** tket:2 on 32 (all-to-all) and
psf:recommended on hwb8 ended without a record and without being stopped, just after the stack dump that amendment
1's diagnostics take shortly before a compile's limit (Python's faulthandler, reading other threads' stacks). That
dump can crash a process. Both were within a fraction of a second of their warm-up's limit, far over their largest
budget, so they would have failed by time: the verdicts do not depend on them, but they are counted as "other"
failures, not "time". The next version records each process's exit code and takes the stack with the interpreter's
lock held instead.

## Reported without prediction

| compiler | within 1x | within 3x | within 10x | Q_all (95%) | failed (time, memory, adapter, other) | median time / reference |
|---|---|---|---|---|---|---|
| qiskit:2:target (reference) | 0.968 | 0.968 | 0.968 | 1.000 | 0 | 1.00 |
| qiskit:1:target | 0.968 | 0.968 | 0.968 | 1.239 (1.171-1.324) | 0 | 0.54 |
| qiskit:3:target | 0.532 | 0.929 | 0.952 | 0.972 (0.958-0.985) | 2 (2, 0, 0, 0) | 1.22 |
| tket:2 | 0.071 | 0.143 | 0.254 | 1.145 (1.073-1.244) | 52 (47, 0, 4, 1) | 47.3 |
| psf:default | 0.690 | 0.921 | 0.968 | 1.012 (1.004-1.021) | 0 | 1.20 |
| psf:recommended | 0.643 | 0.873 | 0.952 | 1.012 (1.004-1.021) | 1 (0, 0, 0, 1) | 1.21 |

(The shares within each tier count the four "invalid" measurements as misses, for every compiler.)

On the 32 tests every compiler returned within 10x, two-qubit gates relative to the reference: qiskit:1 1.355,
qiskit:3 1.002, tket:2 1.143, psf:default 0.998, psf:recommended 0.998.

**For the authors' compiler, PSF-Zero** ([`run-1c/weakness.md`](run-1c/weakness.md)): its quality matches the
reference (Q_all 1.012) and its failures are none (default call), but it is slower than the reference on small
circuits: within 1x on 69% of the tests (default call) and 64% (recommended call), against 97% for Qiskit level 2.
On small HamLib circuits on FakeTorino the recommended call took up to 43 times the reference's time.
