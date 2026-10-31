# Defect days: does the kingston defect persist, and does avoiding it help? (DRAFT, home, 2026-10-31; NOT FIXED — the owner confirms every item before it is fixed by SHA-256 and CET time)

**Why.** Paper 5 found an 18-site dead run on ibm_kingston's n = 40 ring, the same in three runs on 30 October and
invisible to the calibration. Two questions decide whether a defect list (`defect_list_design_DRAFT.md`) is worth
keeping: does a listed path stay dead over days, and does a ring that avoids it read better?

**Frozen inputs (fixed with this note).** The list `results/defect-list-replay-2026-10-31/observations.json`
(its SHA-256 recorded at fixing), read with the draft parameters: dead run = at least 3 consecutive sites below 0.12
at D = 24; LISTED after 2 jobs; expiry not applied during the test. Listed on kingston: [28, 29, 38, 49],
[11, 10, 9], [87, 86, 85]. The list is not updated during the three days.

**Design (per day, three consecutive days, ibm_kingston only).**
- A new fetch each day, after this note is fixed. Rule only; the echo at D = 24 (one-way L = 12), hz = 0, h = 0.6,
  4 inputs and 4 references, 1000 shots.
- **Job A (standard, map-free):** n = 20 (control), 40 and 72 on the rule's usual rings. 24 circuits; time model
  3 + 0.036 x 24 + 0.00027 x 24,000 = 10.3 s.
- **Job B (self-checked):** n = 40 and 72 on the rings the rule places when the day's fetch is masked by the frozen
  list (`defect_list mask`). 16 circuits; 7.9 s. If the masked placement gives the same ring as job A for a size,
  that size is dropped from job B and reported.
- About 18 s by the model per day, 55 s in all.

**Judged.**
- **P (persistence), per day:** the listed path [28, 29, 38, 49] is PRESENT if a dead run on job A's n = 40 ring
  contains at least 2 of its qubits, else ABSENT. Over the three days: PERSISTENT (3 of 3), INTERMITTENT (1-2),
  GONE (0). The same for the two n = 72 paths, reported.
- **A (avoidance), per day and size:** rho_E of job B's ring minus rho_E of job A's ring at the same n, at 2 SE:
  HELPS / NO EFFECT / HURTS; and the number of dead runs on job B's ring.
- **Control:** job A's n = 20 ring has no dead run (as on 30 October); if it has, that day is reported with the note.

**One sentence per outcome (fixed in advance, nothing else is added after the data).**
- PERSISTENT: the defect stays for days without showing in the calibration; a list with a multi-day expiry is useful.
- INTERMITTENT: it comes and goes; a list must be refreshed by a scan on the day of use.
- GONE: it was a one-day state; a standing list is not useful for this device.
- A = HELPS on most days: placing around a self-measured list reads better than the standard placement.

**Stop.** Three days, then the test ends whatever the result. The cause of the defect is not pursued.

**Open for the owner.** The three-day length; kingston only (or also marrakesh and fez); the thresholds; whether
self-checked placement is accepted as a labelled third category beside the map-free standard.
