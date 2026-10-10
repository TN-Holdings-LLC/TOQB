# Pre-registration: TOQB standard run 2 (2026-10-10)

**Status: pre-registration.** It is fixed by the commit that adds it, together with TOQB v13 (below) and the scoring
script [`toqb/score_run2.py`](../toqb/score_run2.py). That commit is pushed to the public repository before the run
starts. The run is made once, under the interruption rule of standard run 1. Times are given in CEST.

## 1. Why a second run

Standard run 1c ([`results/standard-run-1/`](../results/standard-run-1/)) found two weaknesses.

- **The authors' compiler is slow on small circuits.** PSF-Zero's recommended call is slow on small circuits on
  FakeTorino: its time was a geometric mean of 2.53 times the reference's on 17 tests, up to 43 times. Within 1x it
  reached 64% of all tests, against 97% for the reference.
- **TOQB was at fault twice.**
  - Its structural check rejected classical control, refuting T1 on the reference's own outputs.
  - Its stack dump probably crashed two measurements.

Since then:

- PSF-Zero has a new release, 2026-10-10.2. It returns the previous release's circuits and spends less time on the
  recommended call's estimates (PSF-Zero record, Addenda 413-428).
- TOQB v13 fixes its two faults.

Run 2 measures both changes on the same sample.

## 2. What is run

**The same as run 1c** ([pre-registration](2026-10-08-standard-run-1.md) and
[amendment 1](2026-10-09-standard-run-1-amendment.md)), except what follows.

- **The sample.** The same 126 tests, drawn from the seed published with run 1
  ([`results/standard-run-1/seed.txt`](../results/standard-run-1/seed.txt)). The sample is therefore known in advance.
  PSF-Zero's changes since run 1 were tested for identity of output, not tuned on these tests.
- **The compilers.** The same six configurations and versions, except PSF-Zero: release **2026-10-10.2** (PSF-Zero
  commit `0b7f790`), with its optional module `psf_zero_core57` installed (2026-10-10.c30, package `psf-zero-core57`
  0.1.0), as the release's README installs it.
- **The circuit breakers.** Those of amendment 1, unchanged.
- **TOQB v13** (this commit):
  - **The structural check.** It accepts control flow (`if_else`, `while_loop`, `for_loop`, `switch_case`, `box`)
    and checks its bodies in the same way, on the qubits the instruction acts on.
  - **The two-qubit count and the count of gates on failed elements.** Both include the gates in such bodies, each
    body counted once as written. The two-qubit depth still counts a control-flow instruction as one layer.
  - **The stack dump before a compile's limit.** It is taken by a Python thread, with the interpreter's lock held,
    instead of `faulthandler.dump_traceback_later`. The dump on SIGUSR1, sent only just before a process is stopped,
    is unchanged.
  - **Exit codes.** Every record carries its process's exit code. A process that ends without a record is recorded
    as "no record (exit code N)".
  - **Versions.** The provenance records the version of `psf-zero-core57` as well.

  Tests: [`tests/test_v13.py`](../tests/test_v13.py), and the unchanged tests of amendment 1.
- **The machine and the commands.** As run 1c: the home PC, four measurements at a time, nothing else running. As
  in run 1c, PSF-Zero is loaded from a checkout of its release commit, and the seed file is the one run 1 used. Its
  content is the published `seed.txt`.

  ```bash
  cd ~/toqb
  export TOQB_BENCHPRESS=~/benchpress PSF_ZERO_REPO=~/psf_zero_0b7f790
  python -m toqb.runner run --plan plan_standard.json --seed-file ~/.toqb_seed_v01 --out ~/toqb_runs/standard-2 \
      --par 4 --lock --mem-cap-gb 3
  python -m toqb.score_run2 --out ~/toqb_runs/standard-2
  python -m toqb.verify --out ~/toqb_runs/standard-2
  ```

## 3. Predictions

Definitions as in run 1 (usable, within tier t, Q_all, families).

| ID | prediction | confirmed if | refuted if | basis |
|---|---|---|---|---|
| S1 | every output of every compiler is valid, and every checked one is equivalent | no invalid and no "not equivalent" output | any | run 1c: the only invalid outputs were the 20 with classical control, which v13 accepts |
| S2 | PSF-Zero's default call returns the same two-qubit counts as in run 1c | equal on every test where both runs' outputs are usable | one differs | the default call is unchanged by PSF-Zero's new items; BP-FINAL: across processes its circuits varied on 83 of 877 tests, its two-qubit counts on none |
| S3 | PSF-Zero's recommended call is faster on FakeTorino | geometric mean of its time / max(0.05 s, the reference's time), over the FakeTorino tests it returns, <= 2.2 | >= 2.53 (run 1c's value) | run 1c: 2.53 on 17 tests. In PSF-Zero's C30-ID (Addendum 427) the new release's recommended call took 0.656 of the previous release's time where it makes estimates, and alone 0.65-0.77 on seven tests (Addendum 425): about 1.9 expected |
| S4 | PSF-Zero's recommended call places no two-qubit gate on FakeTorino's failed elements | 0 of the FakeTorino tests it returns | at least one | run 1c: 0 of 17 |
| S5 | PSF-Zero's default call rarely fails | fails on <= 2% of the tests the reference finishes | > 5% | run 1c: 0% |

A value between the two thresholds is NOT DECIDED. P0 (integrity) is run 1's, with PSF-Zero's expected release and
head as above, and `psf-zero-core57` 0.1.0 installed.

## 4. Reported without prediction

- **Everything run 1 reported**, beside run 1c's values: per compiler, the shares within 1x, 3x and 10x, Q_all and
  the median time ratio.
- **The four tests with classical control**, now valid, and what each compiler returned on them.
- **The exit codes of all failed measurements.** In particular, whether tket:2 on 32 (all-to-all) and
  psf:recommended on hwb8 fail again, and how.
- **psf:recommended's two-qubit counts against run 1c on FakeTorino.** Its layout search stops by wall-clock time, so
  equal counts are expected but not predicted.

## 5. After the run

The records, `score.md`, `score.json`, the verify output, the run log and the memory log are committed under
`results/standard-run-2/` with a results note. Any deviation from this file is listed there.
