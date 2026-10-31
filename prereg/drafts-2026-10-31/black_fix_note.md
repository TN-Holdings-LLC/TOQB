# Black fix: a frame flip on five qubits (3, 5, 7, 27, 29) as the per-path fix for kingston's dead run (home, 2026-10-31; declared on the owner's go of 2026-10-31 15:26 CET)

**Why.** The bisection (`results/black-bisect-2026-10-31`) stopped by its rule after round 2 (both arms HELPS at
2 SE: SPREAD). Post hoc, its arm A (local flip at ring positions 0, 2, 4, 6, 8 = qubits 3, 5, 7, 27, 29; couplers
(16, 3) to (29, 38)) lifted the dead block by +0.299 at D = 24, at least the global flip's +0.285 / +0.295, with the
rest of the ring at -0.007; arm B gave +0.019. That was seen after the run, so it is tested here as a new claim.

**Design (one job, ibm_kingston, after this note and a new fetch).** The rule's standard n = 40 ring (unmasked
fetch; off at D = 24 byte-identical to 30 October), hz 0, h 0.6, 4 inputs and 4 references, 1000 shots, options off.
Five arms at D = 12 and 24: off; global flip; A2 = local flip at positions 0, 2, 4, 6, 8; A3 = positions 0, 2, 4
(qubits 3, 5, 7; couplers (16, 3) to (7, 17)); B3 = positions 6, 8 (27, 29; couplers (17, 27) to (29, 38)). Local flips
keep the ideal circuit by virtual Z (operator-equality tests). 10 records, 80 circuits, 27.5 s predicted
(`gpu/black_fix.sh`; dry run on the 14:58 CET fetch: all accepted, A2 the declared qubits).

**Judged at D = 24 (`toqb.ff_score`; block = 38, 49-55, 59; rest = the ring minus the 18-site run; 2 combined SE).**
- **F1:** A2 block minus off HELPS, and A2 block minus global flip KEEPS (not below -2 SE).
- **F2:** A2 rest minus off: NO COST (not below -2 SE).
- **F3 (where in A2):** A3 and B3 gains (block minus off). CARRIED BY A3 (or B3) if that arm's gain is at least
  2/3 of A2's and the other's at most 1/3; otherwise SHARED.

**One sentence per outcome (fixed in advance).**
- F1 and F2 hold: a frame flip on five qubits (3, 5, 7, 27, 29) is a per-path fix for kingston's dead run: the global
  flip's gain without its cost. F3 names the smaller set if one carries it.
- F1 holds, F2 does not: the five-qubit flip keeps the gain but costs the rest; not used as is.
- F1 fails: the round-2 gain does not repeat; not used.

**Reported.** D = 12; the global flip's gain and cost (a third repeat); RECOVERED (block >= 0.8 x rest); per site.
**Stop.** One job.
