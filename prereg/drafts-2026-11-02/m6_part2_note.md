# OS plan M6, part 2: sentinels 60-90 minutes after the scan (home, 2026-11-02)

**Why.** Part 1 (`results/m6-practice-2026-11-02`) held: the sentinel read DEAD on the known run and CLEAN on the ring
placed around the registry. On 31 October a gray stretch came and went within about 90 minutes. Part 2 asks whether
the registry of the morning scan still describes the device when a user's job runs an hour or more later.

**What is run.** Jobs S and V exactly as in part 1 (`gpu/m6_practice.py`, psf-os eb20501; sh6 D = 12, cluster parity
and the sentinel on the standard n = 40 ring and on the ring placed around
`results/coverage-days-2026-11-02-day3/list_after.json`), built from a new fetch, submitted between 12:31 and
13:01 CET on 2 November, that is 60-90 minutes after the scan of that registry (job A of coverage day 3, submitted
11:31:02 CET). Job P is not run. 18.2 s by the time model.

**Reported, not judged** (as the workplace's draft set it).
- The sentinel verdict on S and on V (CLEAN / WEAK / DEAD, with positions and qubits), and every site signal beside
  part 1's.
- Whether the run on S is the same 18 qubits as at 12:03 CET; any new WEAK or DEAD stretch on V, which enters the
  registry as gray of that day (a run within 0.05 of the weak line is "borderline").
- sh6 and parity on both rings beside part 1's (same rings, about 30 minutes later).
- If the submission falls outside 12:31-13:01 CET, the time is reported and nothing else changes.

**Stop.** One run of the two jobs.
