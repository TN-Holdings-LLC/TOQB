# DRAFT (not declared; the owner decides; workplace, 2026-11-05 02:35 CET): the standing rules of the daily record

**Owner's decisions, 2026-11-05 04:34 CET (relayed at the workplace):** fixed problem **FX-A**; the answers may be seen at
home so that each run is scored at once: the blind protocol below is **not adopted** (kept for the record). The values
are released in `results/daily-pool-2026-11-05/released/` (they match the hashes committed in 12164be).

Builds on the owner's idea (`prereg/drafts-2026-11-04/daily_record_IDEA.md`, 11-04 14:33 CET) and the owner's
instruction of 11-05: make the problems so that solving them raises the record's value. Nothing here is fixed.

## What the record is worth, and what it is not

- Worth: one run a day, every day, on two or three devices; the answers sealed before the run, and kept from the side
  that runs and scores the device until its results are committed; failures counted the same as successes; job IDs
  so anyone can check with IBM; circuits published so anyone can recompute the exact answers.
- Not: a quantum advantage. Every answer here is computed exactly on a classical machine (light cones of at most 33
  qubits). Each problem states its largest light cone and 2^(cone), so the classical cost is in the record.

## Pool and order

- Pool `daily/pool.py` (POOL D01-D32, SCALE S01-S06), answers sealed on 11-05 (hashes in TOQB; values withheld).
- **Day k** (k = 1 on the first day the owner names, then every calendar day) uses **D_k**. A day without a run is
  recorded as "not run" and D_k is not used again (no moving a hard problem to a better day).
- **SCALE:** one S problem a week, in the order S01, S02, ..., on the first run day of each week, as a third problem.
  No substitute if B102 has no qualifying copy on the day's devices: recorded "refused" (B102 has only two copies).
  On the device records of 11-04 (afternoon), B102 qualifies on ibm_fez at (0,0) and nowhere on ibm_marrakesh (B87
  would not either; B72 does at (0,4)): the SCALE problem is expected to run on fez only, refused on marrakesh.
- **Fixed problem:** one of
  - FX-A: P4 chain, h 0.15, b = pi/4 - 0.3, t 12 (33 q, 24 CZ layers; answers sealed 11-04; read on both devices 11-04);
  - FX-B: P5 rule on B72, theta 0.8, t 5 (72 q, 15 CZ layers; sealed 11-05);
  - FX-C: the Qedma tutorial's P6, theta_x 0.53, t 5 (35 q; sealed 11-04): the one problem with a published outside
    reference (the tutorial's own unmitigated and mitigated values), so the daily series can be compared with it.
    Raw P6 missed by -0.08 to -0.21 on 11-04: expected to DIFFER without correction; that is what it would measure.
  Its answers are known after day 1 (the same problem daily); it is not blind and is not counted as a blind result.

## The blind protocol (the part that makes a success worth more)

1. Workplace: computes the answers on a pod, commits only their SHA-256 (per problem and combined) and the circuits;
   keeps the values in the sealed folder. Home receives circuits and hashes, not values.
2. Home (night): fetch, `psf-os run2d` batch, submit, collect; commits the raw counts, the answer cards' estimates
   (M and every <Z_q> with 2 SE) and the job IDs **before** it has the day's answer values.
3. Workplace (next day): releases that day's answer file; anyone checks it against the hash committed in step 1.
4. Scoring by the fixed scorer, from the committed counts; the verdicts are what the scorer says.
Order of the commits (answer hash < device result < answer release) is the proof; dates and job IDs pin it.

## Judgements per problem and device (as 11-04 practice, plus two)

- RUNS (no hand step), READS (finite answer card), AGREES (|M - M_exact| <= 0.05), BEATS (MSE below the trivial guess).
- Per-qubit: MSE over qubits against the trivial guess (M alone hid a site in P4 on 11-04).
- Calibration: the share of qubits with |<Z_q> - exact| <= 2 SE (shot noise only; expected far below 95 % because
  device error is not in SE; reported so the gap is visible, not judged).
- Problems marked "guessable" (|M_exact| >= 0.9 or <= 0.05, rule fixed on 11-05 before any answer was seen) stay in the
  pool and are scored, but are shown apart: an AGREES there says little.

## Failures counted

Refused placement, job failed, sentinel dead, a check failed, not run: each is a line in the record, never dropped.

## Open for the owner

Start day; devices per night (two or three) and how chosen (queue as 11-04?); whether SCALE runs weekly or not;
which fixed problem; whether a correction (11-04's or another) is applied in the record or only raw; where the
released answer files live (a ZIP per day, or the takehome).
