# Safe ladder: grow a verified-safe ring from n = 40 to n = 72 by scan, list, avoid, rescan (home, 2026-10-31; declared on the owner's go of 2026-10-31 12:17 and 12:18 CET)

**Why.** Clean depth (`results/clean-depth-2026-10-31`): on rings placed around the defect list, n = 40 read as deep as
n = 20 (L* 24.2-24.6) but n = 72 did not (20.4-20.8). Its ring held a weak stretch (35, 19, 15, 14; signal 0.10-0.18
against a median near 0.4) that the defect list's line (0.12) let through. The owner: a list that is not verified
safe sends us back to bad places, so build one and test until it succeeds, starting from what certainly succeeds.

**The strict list (`toqb/safe_loop.py`).** A site is weak if its echo signal at D = 24 is below max(0.12, 0.5 x the
ring's median). A weak run is at least 3 consecutive weak ring sites (cyclic). Its centre path (4 qubits) is listed
after one sighting, unless it shares 2 qubits with a path already listed (the same defect seen again). Placement: the
day's fetch with the middle coupler of each listed path marked failed, then the unchanged rule (`fold:rule`).
Seed list `results/safe-ladder-2026-10-31/seed_list.json` (SHA-256 7b62a4ca...7301): the defect list's [11, 10, 9],
[28, 29, 38, 49], [87, 86, 85], and [35, 19, 15, 14] from 31 October's job B (the only new path by the rule).

**A round (one job, ibm_kingston, a new fetch each round).** n = 20 (control), 40 (the start: on the seed list it is
the ring verified this morning), 48, 56, 64, 72; echo at hz = 0, one-way L = 12, 25, 50 (D = 24, 50, 100), h = 0.6,
500 shots; 18 cells, 144 circuits, 27.6 s predicted (`gpu/safe_ladder.sh`; dry run on the 11:39 CET fetch: all
accepted, n = 40 the verified ring).

**Judged per round and size (`safe_loop judge`).** SAFE: no weak run on the ring, and L* reaches the same job's
n = 20 within 2 combined SE (fit over D = 24, 50, 100). Else NOT SAFE. **SUCCESS** when every size 40-72 is SAFE in one
round.

**The loop.** After a round that is not a success, the weak runs of that round (sizes 40-72) enter the list
(`list_after.json`) and the next round is built on it. The list never loses a path during the loop.

**Stop (fixed in advance).** SUCCESS; or 4 rounds; or a round adds no new path while a size is NOT SAFE (the list can
no longer change that ring: its shortfall is not a weak run we can see); or a size cannot be placed.

**One sentence per outcome.**
- SUCCESS in round k: a strict self-measured list makes every ring from n = 40 to 72 read as deep as n = 20 on this
  device and day; the verified list and rings are recorded as the safe list of the day.
- Stopped without success: the largest n whose ring was SAFE in the last round is reported as the safe size of the
  day, with the reason the loop stopped.

**Reported.** Per round: the list, masked couplers, rings, weak runs, L* per size, rho_E, billed time.
Self-checked category. Not added to the coverage-days list.
