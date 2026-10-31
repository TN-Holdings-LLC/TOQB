# Coverage days: how much of the device stays usable when dead runs are removed, and does placing around a self-measured list widen it? (home, 2026-10-31; declared on the owner's go of 2026-10-31 11:23 CET)

**Direction (the owner, 31 October).** PSF's strength is its range. Parts of a device from which no information comes
back are left out and not chased; what remains should be as wide as possible. So the judged number is the usable part
of a ring, not the quality of what is read there. The search for where a dead run's signal goes
(`coherent_stage1_DRAFT.md`) is on hold; its tools stay, it is not run.

**Changes from `defect_days_DRAFT.md`.** (1) The primary judged item is the number of usable sites, not rho_E (rho_E
on the usable sites is reported). (2) The list is not frozen: each day uses the list as it stands that morning,
which includes the earlier days' jobs, as an operating system keeps its bad list.

**Definitions (fixed).** Echo signal per ring site a_j = mean over the 4 inputs of <-z_in,j Z_j> (Z, D = 24). Dead
run = at least 3 consecutive ring sites (cyclic) with a_j < 0.12. Usable sites = the ring's sites outside every dead
run. List (`toqb/defect_list.py`): the centre 4 qubits of each dead run; sightings sharing 2 qubits are one entry;
LISTED after 2 jobs on the same device; expires 7 days after it was last seen. Placement around the list: the
day's fetch with the middle coupler of each LISTED path of that device marked failed (`defect_list mask`), then the
unchanged rule (`fold:rule`).

**Design (per day; ibm_kingston; three runs on three different days within 7 days of the first).**
- A new fetch each day (VPN off), then `gpu/defect_days.sh` with the day's list: day 1 the replay list
  `results/defect-list-replay-2026-10-31/observations.json` (SHA-256 b1fe9fe7...6765; LISTED on kingston
  [28, 29, 38, 49], [11, 10, 9], [87, 86, 85]); day k the `list_after.json` of day k-1 (`gpu/defect_days_score.sh`).
- Job A (standard, map-free): the rule's echo at n = 20, 40, 72; D = 24 (one-way L = 12), hz = 0, h = 0.6, 4 inputs
  and 4 references, 1000 shots; 24 circuits, 10.3 s by the time model.
- Job B (self-checked): n = 40 and 72 on the rings placed around the list; 16 circuits, 7.9 s. A size whose ring
  equals job A's is dropped from job B and reported. Options off. About 18 s per day.
- Dry run on the 30 October fetch: 3 couplers masked, all 5 records accepted, A 10.3 s, B 7.9 s; scoring and the
  next day's list checked on made-up counts.

**Judged.**
- **C (coverage, primary), per day and n = 40, 72:** usable sites on job B's ring minus usable sites on job A's
  ring. WIDER (>= +3), NARROWER (<= -3), SAME otherwise; a size dropped from job B counts as SAME (nothing to avoid).
- **P (persistence), per day:** the path [28, 29, 38, 49] is PRESENT if a dead run on job A's n = 40 ring holds at
  least 2 of its qubits, else ABSENT. Over the three days: PERSISTENT (3), INTERMITTENT (1-2), GONE (0).

**One sentence per outcome (fixed in advance; nothing else is concluded).**
- C WIDER in at least 4 of the 6 verdicts and NARROWER in none: placing around a self-measured list widens the usable
  part of the device; the list joins the procedure as the self-checked category, always labelled.
- C NARROWER in at least 2: avoiding the list moves onto worse places; the list is not used, and dead sites are only
  removed after the run.
- Otherwise: removing dead sites after the run is enough at these sizes; the list adds nothing measurable.
- P PERSISTENT: the defect stays for days without showing in the calibration; a list with a multi-day expiry is
  sound. INTERMITTENT: a list must be refreshed by a scan on the day of use. GONE: it was a one-day state.

**Reported, not judged.** Mean signal on the usable sites (A and B) and rho_E; the dead runs of every ring; the
n = 72 paths [11, 10, 9] and [87, 86, 85] on job A's ring; the n = 20 ring (no dead run on 30 October); the list
after each day; billed time.

**Any device.** The scripts take DEVICE and work on any device the rule can place n = 72 on. This note covers
kingston only; another device needs its own note (its first day is a scan, since nothing is listed there yet).

**Stop.** Three days, then the test ends whatever the result. The cause of the dead runs is not pursued.
