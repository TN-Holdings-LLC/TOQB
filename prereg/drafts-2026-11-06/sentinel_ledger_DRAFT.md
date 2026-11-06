# DRAFT (not declared; workplace, 2026-11-06 CET; W3 plan A, owner 01:37 CET): reading the ring sentinel beside a ledger of known-dead stretches

Status: draft of a change to the daily record's standing rules (`prereg/daily/standing_rules.md`). Plan A adopted by
the owner: the circuits do not change; plan B (placing around the stretch) is not taken. Whether this re-reading
enters the record's judgements is a declaration change, decided by the owner.

## Why

ibm_fez's ring sentinel has been DEAD in all seven fez jobs from 2026-11-03 to 11-05, always on the same stretch
(41-43, 56, 63-67; often 36, 47, 57; sometimes 21), while marrakesh's was CLEAN in all three
(`notes/os2d_w_2026-11-06/ring2d_fez.json`). A sentinel that is always DEAD tells nothing about the day.

## The rule (proposed)

1. **Ledger** (`psf-os ringledger --jobs JOBS.json --out LEDGER.json`): for every committed job with a ring sentinel,
   the qubits in its DEAD runs, with the job's day. Built from committed records only; never overwritten (a new
   file per day).
2. **Known-dead qubits on day D:** qubits in a DEAD run in at least 3 jobs on at least 2 days **before D**
   (`report2d.known_dead`; only earlier days count, so a stretch cannot be declared known by the day it is read).
3. **Re-reading** (`psf-os result2d --extended --ring-ledger LEDGER.json --date D`): the known qubits take the ring's
   median signal, so they can neither make nor hide a run; the rest is judged by the registry's rules unchanged
   (dead: a_j < 0.12 on >= 3 consecutive sites; weak: below max(0.12, half the median)).
4. **Shown in the record:** the declared sentinel verdict, unchanged and first; beside it "beside the ledger:
   CLEAN / WEAK / DEAD" with the known qubits set aside and any new dead qubits.
5. **From when:** the first night after the owner declares it. Earlier nights are re-read after the fact and marked so.
6. **Release:** a qubit leaves the known set when it is absent from DEAD runs in 3 consecutive jobs on 2 days (the
   ledger's same counts, the other way); proposal, to be fixed with the rule (not implemented yet).

## What it showed after the fact (not a test)

- fez 2026-11-05 (daily): declared DEAD; beside the ledger (9 qubits known from 11-03 and 11-04: 41, 42, 43, 56,
  63-67) CLEAN, no new dead run.
- marrakesh 2026-11-05: CLEAN and CLEAN (nothing known).

## What it does not do

- It does not move any circuit or change any placement (the user's circuit, floor, mirror and ring are as declared).
- It does not tell whether the known stretch harms a user circuit placed on it (it may: P6's patch at (0,0) on fez
  holds 36, 41, 42, 43, 47); report2d's flags and the per-qubit residuals show that, not the sentinel.
- A stretch that dies only on some days is never "known" unless it meets the counts; the declared verdict still shows it.
