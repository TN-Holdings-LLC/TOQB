# Declared: the standing rules of the daily record (owner's go of 2026-11-05 04:37 CET: "start today, the free devices")

Day 1 is 2026-11-05. These rules apply every night until the owner changes them; a change is a new declared file.
Built on the owner's idea (`prereg/drafts-2026-11-04/daily_record_IDEA.md`) and the owner's decisions of 2026-11-05
04:34, 04:35 and 04:39 CET recorded in `prereg/drafts-2026-11-05/daily_record_DRAFT.md`.

## Problems of a night

- **Fixed:** FX-A (P4 chain of 33 qubits, h 0.15, b = pi/4 - 0.3, t 12; the same circuit as the practice test's
  p4_b0.485_t12 of 2026-11-04; answers sealed 2026-11-04 in `results/bank-2026-11-04/pod/du_bank/answers.json`).
- **New:** the next unused problem of `daily/pool.py` in pool order, starting at D02 (D01 kept apart: the same problem
  as the practice circuit p4_b0.485_t08). A problem is used once it is built for a night, run or not; it is not
  taken again. The order of the pool was fixed in 12164be before any answer was seen.
- Answers: the files released in `results/daily-pool-2026-11-05/released/` (each matches the hash committed in 12164be,
  before the release 50e412e); FX-A as above. Written for a night by `gpu/daily_night.py`.
- SCALE problems (S01-S06) and the other fixed candidates are not part of these rules.

## Devices of a night

- Right before the fetch, read the pending jobs of ibm_marrakesh, ibm_fez, ibm_kingston (nothing else).
- Run on every device with at most 10 pending jobs; if none, on the one with the fewest; ties in that order.
  (`daily_fetch_2026-11-05.py` does this and fetches each with `psf-os fetch`: coupling graph and failed marks only.)

## Run

- One `psf-os run2d` batch per device with the night's two circuits (psf-os 7739365 or later with the same user2d and
  compile code as ac84182); each circuit placed by `lattice2d.place`, with its own floor and mirror; one ring
  sentinel; 4000 shots; no correction and no mitigation (owner, 04:35 CET: raw values until a proper correction
  exists). `psf-os submit` (the job's own device only) and `psf-os collect`.

## Judged (per problem and device; `gpu/daily_score.py`, fixed with this file; uses gpu/practice_score.judge)

- RUNS (built, sent and returned with no hand step), READS (MSE <= half the mean square answer), AGREES
  (|M - M_exact| <= 0.05), BEATS (MSE below the better trivial guess: every <Z> = 0, or every <Z> = 1).
- Reported, not judged: the share of qubits within 2 SE of the exact value; the floor; the mirror flags; the sentinel;
  "guessable" (|M_exact| >= 0.9 or <= 0.05) shown apart.

## Recorded

- Every night and device gets a line in `results/daily/RECORD.md` and a folder `results/daily/<date>/<device>/`
  (device record, circuits, answers, job, counts, scores): successes and failures alike. A refused placement, a
  failed job, a check that fails, a night not run: each is a line, never dropped.
- The answers are visible at home (owner, 04:34 CET); the order of the commits (answer hash, then device result) and
  the IBM job IDs are what make the record checkable by others.

## Before day 1 (no device)

- FX-A's circuit equals the practice circuit p4_b0.485_t12 (same gate list) and its answers equal that test's.
- D02 compiled by run2d on the 2026-11-04 marrakesh record, noiseless, on balls of radius 3: max 3.4e-6 against the
  released answer; on both 2026-11-04 records the batch is accepted (marrakesh: both at (0, 0); fez: FX-A at (4, 0),
  D02 at (0, 0)); 10 circuits, 14.2 s by the model per device.
