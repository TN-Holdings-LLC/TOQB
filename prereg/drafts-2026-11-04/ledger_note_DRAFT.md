# DRAFT (not declared): the reliability ledger v0 on a device, the suspect-qubit lattice against the same lattice minus the ledger's exclusions (workplace, 2026-11-04)

Status: a draft for home and the owner. `psf_os.ledger` exists (psf-os, this workplace commit) with tests; the after-
the-fact numbers below are reference only.

**What the ledger is, and is not.** Per device, per qubit, counts of DEAD / HEALTHY / UNCERTAIN readings from the OS's
own checks, kept apart by kind: ring (the existing registry, unchanged; a LISTED or same-day gray path masks the same
middle coupler, tested), floor (the theta = 0 <Z_q> of each job), mirror (the mirror sentinel's d_q). Each job is read
with its own line (rule R's form) and the three-valued rule (line +- 3 SE). The ledger is used for one thing: leaving a
qubit out when, in one kind, two different jobs read it DEAD within 7 days. UNCERTAIN is reported, never acted on.
**Not adopted** (owner, 10/14, and the data): fine scores, ranking, a "most reliable route", automatic search. And the
kinds are by check, not by task: the premise "dead for the echo but working for sh6" was wrong (M6: sh6 0.780 on the
dead run, 0.825 avoiding it).

## The test (one job)

- Device by queue (P6's rules: fewest pending jobs among fez, marrakesh, kingston; ties marrakesh, fez, kingston).
- The ledger file and the registry file in force at the fetch are hashed and committed before the build.
- Two lattices in the same job, P5's circuit (RZZ(-pi/2) as one CZ, RX(theta)), theta 0, 0.4, 0.8, 1.0, t = 1..5:
  - **A:** the suspect-qubit lattice (`kim.region(suspect=True)`, after the registry's mask).
  - **B:** A without the ledger's EXCLUDED qubits (`ledger.apply`, then the same region rule).
  - If the ledger excludes nothing on the chosen device, B = A: the test is **NOT TESTED** and is reported so (B is
    not built; the job runs A only, as a ledger update).
- Answers: CPU light cones (t <= 5, cones <= 19 qubits as stage B), sealed before sending.
- Ring sentinel; 4000 shots; no mitigation; "stay".

## Judged

1. Sentinel.
2. **The ledger's exclusions (B against A):** mean squared error of <Z_q> over the qubits both lattices answer,
   theta 0.4, 0.8, 1.0 pooled, t = 1..5: **HELPS** if MSE_B / MSE_A <= 0.8, **NO EFFECT** between 0.8 and 1.25,
   **HURTS** at 1.25 or more. Reported with it: **the price** (qubits left out, and qubits cut off from the largest part
   by them).
3. The answer card for both lattices (value +- 2 SE, floor, sentinel).

After the job, its floor readings are appended to the ledger (a new file; the old one is kept).

## After the fact (reference only): the ledger on 3 November

`notes/ledger_2026-11-04/ledger_posthoc.py` -> `out/ledger_posthoc.json`. Floor kind only (no mirror data yet).

| job (CET) | line | DEAD | UNCERTAIN | DEAD qubits |
|---|---|---|---|---|
| kingston stage B (06:08) | 0.932 | 5 | 9 | 72, 87, 125, 127, 131 |
| kingston stage C/D (12:09) | 0.928 | 6 | 4 | 35, 43, 69, 78, 119, 138 |
| fez stage E X (17:04) | 0.924 | 15 | 1 | 21, 23, 41, 43, 51, 55, 61, 65, 83, 113, 126, 131, 141, 148, 149 |
| kingston stage E K (17:04, run 20:20) | (K's own) | 3 | | 7, 51, 72 |

What this says:
- **Before K, the ledger excluded nothing on kingston:** the DEAD sets of the morning and midday jobs do not overlap.
  Applied to K, it changes nothing (MSE ratio 1.00 at all three theta; price 0). The readout faults that rule R would
  drop inside one job are mostly not the same qubits a few hours later.
- **After K, qubit 72 would be excluded** (DEAD in the morning and in the evening; 0.91 and 0.51).
- **fez could not be helped on its first day:** with one job, the two-job rule excludes nothing, and stage E's misses
  (qubits 23, 51, 83) came on fez's first day. Within-job rule R (P6's pre-set sub-analysis) is the check for that case;
  the ledger is for faults that persist.
- So the honest expectation for the test above is NOT TESTED or NO EFFECT unless a device has a persistent readout
  fault; the test is still worth running as the ledger's first prospective use, because its cost is a few circuits in a
  job that runs anyway.
