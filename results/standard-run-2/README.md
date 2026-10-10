# TOQB standard run 2: results

**Status: the result of TOQB's second scored run**, as pre-registered in
[`prereg/2026-10-10-standard-run-2.md`](../../prereg/2026-10-10-standard-run-2.md) (commit `42a49e2`, pushed at
07:12:19 CEST, before the run). Scored by [`toqb/score_run2.py`](../../toqb/score_run2.py), re-scored independently
by [`toqb/verify.py`](../../toqb/verify.py). Times in CEST.

## The run

| started | ended | records | status |
|---|---|---|---|
| 2026-10-10 07:12:37 | 08:03:18 | 756 of 756 | scored |

- **Versions.** TOQB `42a49e2` (v13); PSF-Zero `0b7f790` (release 2026-10-10.2) with `psf-zero-core57` 0.1.0;
  Benchpress `b695f30`; Qiskit 2.5.2, pytket 2.18.5, pytket-qiskit 0.78.0. No uncommitted change in any of the three
  repositories.
- **Machine.** The home PC (WSL2, 12 CPUs, Python 3.12.13), four measurements at a time, nothing else running.
- **Time.** 51 minutes. The bound computed after the references was 6.0 h.
- **Interruptions.** None by the machine breaker. None at the memory cap of 3 GB. The largest peak was 2.2 GB
  (Qiskit level 3 on bwt_n21, linear). The machine never had less than 9.5 GB available (`memlog.tsv`).

**Files.** [`records.jsonl`](records.jsonl), [`score.md`](score.md), [`score.json`](score.json),
[`summary.md`](summary.md), [`weakness.md`](weakness.md), [`memlog.tsv`](memlog.tsv) and the run's log
[`run.log`](run.log) (the runner's output, the score and the re-scoring), all as the run wrote them. The records hold
no local path except in the form `/home/<user>`, which the runner writes.

## Score ([`score.md`](score.md))

**P0 (integrity): PASS.** **Independent re-scoring: PASS** (756 records, 0 differences).

| ID | prediction | value | verdict |
|---|---|---|---|
| S1 | every output of every compiler is valid, and every checked one is equivalent | no invalid output and no checked output not equivalent, for any compiler | **CONFIRMED** |
| S2 | psf:default's two-qubit counts equal run 1c's | equal on all 122 tests where both runs' outputs are usable | **CONFIRMED** |
| S3 | psf:recommended on FakeTorino: geometric mean of time / max(0.05 s, reference) <= 2.2 (REFUTED >= 2.53) | 2.128 on 17 tests | **CONFIRMED** |
| S4 | psf:recommended places no two-qubit gate on FakeTorino's failed elements | 0 of 17 | **CONFIRMED** |
| S5 | psf:default fails on <= 2% of the tests the reference finishes (REFUTED > 5%) | 0.000 | **CONFIRMED** |

## Reading

**S1: v13's structural check fixes T1's fault.** The four tests with classical control (ipea_n2 on square and
heavy-hex, cc_n151 on all-to-all, cc_n64 on linear) are valid for all five Qiskit-based outputs. As in run 1c,
TKET's adapter fails on all four (exit code 1). None of these outputs could be checked for equivalence.

**S3: PSF-Zero's recommended call is faster, but less than expected.**

- The value is 2.128, against 2.53 in run 1c. The pre-registration expected about 1.9.
- On the 17 FakeTorino tests, PSF-Zero's own time was 0.854 of run 1c's (geometric mean). The reference's time was
  1.009 of run 1c's.
- It reached the reference's time on 4 of 17 tests (3 in run 1c).
- Its worst case is still a small HamLib circuit:

  | test | reference (s) | psf:recommended (s) | ratio, run 2 (run 1c) |
  |---|---|---|---|
  | ham_JW-8 | 0.073 | 1.416 | 19.4 (42.8) |
  | ham_mu_y_prime_enc_gray_dvalues_16-16-16 | 0.016 | 0.228 | 4.6 (6.3) |
  | gf2^5_mult | 0.037 | 0.196 | 3.9 (4.0) |

- Its two-qubit counts equal run 1c's on all 17 tests. Equal counts were expected but not predicted, since its
  layout search stops by wall-clock time.

The release's gain is in the estimates. On circuits that compile in under a second most of the time goes to other
steps, which remain (PSF-Zero, Addendum 427).

**The shares within each tier rose for every Qiskit-based compiler only because of S1's fix.** The four tests with
classical control now count as valid. On the other 122 tests, psf:default and psf:recommended reached the
reference's time on the same number of tests as in run 1c (87 and 81).

## Failed measurements

| compiler | failed | how (exit code) |
|---|---|---|
| qiskit:3:target | 2 | time (3): bv_n280 and bv_n140 on square, as in run 1c |
| tket:2 | 52 | time (3) 42; the runner's backstop (-9) 6; the adapter (1) 4 |
| psf:recommended | 1 | hwb8: "no record (exit code 3)", see below |

**tket:2 on 32 (all-to-all)**, a failure "without a record" in run 1c, is now an ordinary stop by time (exit code 3).
Run 1c's attribution to the stack dump fits this.

**A third fault of TOQB, found after the run.** psf:recommended on hwb8 ended with exit code 3, the runner's own
stop by time.

- The process ran 31.7 s, less than the warm-up's limit of 42.2 s. So the stop must be a timed compile's limit of
  12.2 s, the largest budget (10 times the reference's 1.22 s).
- The stop came inside Qiskit's `SabreLayout`, which PSF-Zero calls (`stack_at_stop`).
- Its record was lost, so it shows as "no record".

The cause is in TOQB:

- The PSF-Zero adapter sends the compiler's standard output to a buffer (`contextlib.redirect_stdout`) while it
  compiles.
- The runner's watchdog writes the stop's record to standard output from another thread. During a PSF-Zero compile
  that is the buffer, and the record is discarded with it.

Only PSF-Zero's adapter does this. hwb8 is the only PSF-Zero measurement stopped by time in either run. Run 1c's
hwb8 probably ended the same way; it has no exit code to show it.

**Effects.**

- No verdict changes. S5 concerns the default call, which did not fail. S3 averages over the tests the recommended
  call returns.
- The failure is not counted as "time" in `score.md` ("1 (0, 0, 0, 0)").
- The fix (the runner writes its record to the process's original standard output) is for the next version. The
  records are published as written.

## Reported without prediction (beside run 1c)

| compiler | within 1x (1c / 2) | within 3x | within 10x | Q_all | median time / reference | failed |
|---|---|---|---|---|---|---|
| qiskit:2:target (reference) | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 1.000 / 1.000 | 1.00 / 1.00 | 0 / 0 |
| qiskit:1:target | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 1.239 / 1.265 | 0.54 / 0.56 | 0 / 0 |
| qiskit:3:target | 0.532 / 0.556 | 0.929 / 0.960 | 0.952 / 0.984 | 0.972 / 0.973 | 1.22 / 1.16 | 2 / 2 |
| tket:2 | 0.071 / 0.071 | 0.143 / 0.143 | 0.254 / 0.254 | 1.145 / 1.145 | 47.3 / 44.4 | 52 / 52 |
| psf:default | 0.690 / 0.714 | 0.921 / 0.952 | 0.968 / 1.000 | 1.012 / 1.012 | 1.20 / 1.16 | 0 / 0 |
| psf:recommended | 0.643 / 0.667 | 0.873 / 0.905 | 0.952 / 0.984 | 1.012 / 1.012 | 1.21 / 1.17 | 1 / 1 |

On the 32 tests every compiler returned within 10x, two-qubit gates relative to the reference: qiskit:1 1.363,
qiskit:3 1.002, tket:2 1.147, psf:default 0.998, psf:recommended 0.998.

**For the authors' compiler, PSF-Zero** ([`weakness.md`](weakness.md)):

- Its quality matches the reference (Q_all 1.012), and its default call did not fail.
- Its weakness is still time on small circuits: within 1x on 71% (default call) and 67% (recommended call) of the
  tests, against 100% for the reference itself.
- Its recommended call took up to 19 times the reference's time on small HamLib circuits on FakeTorino.

## Deviations from the pre-registration

None in how the run was made or scored. The one finding about TOQB itself (the lost record) is described above.
