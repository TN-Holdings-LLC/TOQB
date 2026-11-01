# OS plan M3, second form: a shallow forward computation on ibm_marrakesh, standard ring against the ring placed around the defect list (home, 2026-11-01; declared on the owner's go of 2026-11-01 15:46 CET)

**Why.** M3 on kingston (`results/qca-m3-2026-11-01`) was INCONCLUSIVE: its computation is the identity only after n
layers, and 40 layers are beyond the readable depth (0.009 and 0.020 against the declared 0.05). The owner: redo it,
on ibm_marrakesh (kingston's queue was long).

**The computation.** (S on every qubit, CZ ring) then (H on every qubit, CZ ring), repeated. Its symplectic matrix
has order 6 for every ring length, so D = 6k layers return the input bit by bit (stabilizer simulation, n = 8, 20, 40,
72; `tests/test_qca.py`); in between, the output bits are random (e.g. <Z_0> = 0 after 3 layers at n = 72). Not a
mirror: no layer is undone by a later one. `toqb/qca_test.py --kind sh6`.

**Design (ibm_marrakesh, after this note and a new fetch; two jobs).**
- **Job S (standard, map-free):** the rule's n = 72 ring (it held a 5-site dead run, 37-25-26-27-28, in the M4 scan
  at 12:24 CET), D = 12 and 24.
- **Job V (self-checked):** the n = 72 ring placed when the fetch is masked by
  `results/two-devices-2026-11-01/marrakesh/avoid/list_after.json` (LISTED [17, 27, 28, 29]; masked (27, 28)),
  D = 12 and 24.
- 4 inputs and 4 readout references per record, 1000 shots, options off. 16 circuits per job, 7.9 s each
  (`gpu/qca_m3b.sh`; dry run on the 11:58 CET marrakesh fetch: all accepted; the standard ring holds (27, 28), the
  avoid ring does not; every compiled circuit returns every input without noise).

**Scored (`qca_test score`).** As in M3: per-site a_j = mean over inputs of <z_in,j Z_j>; ring mean and SE; usable
sites (outside runs of >= 3 sites below 0.12); per-bit right fraction; whole-string match.

**Judged at D = 12.**
- **Readable:** if V's mean is below 0.05: INCONCLUSIVE, nothing else judged.
- **Q1:** ring mean, V minus S, 2 SE: HELPS / NO EFFECT / HURTS.
- **Q2:** usable sites, V minus S: WIDER (>= +3) / SAME / NARROWER.

**One sentence per outcome (fixed in advance).**
- Q1 HELPS and Q2 WIDER: avoiding self-measured dead paths makes a forward computation right on more of the ring.
- Q2 WIDER, Q1 not HELPS: more sites carry a signal but the ring as a whole is not more right.
- Q1 HELPS, Q2 not WIDER: the ring as a whole is more right; the dead part was too small to count as a run.
- Neither: the allocator's gain does not carry to this computation on this device and day.

**Reported.** D = 24 the same way; per-bit right; whole-string match; dead runs; per site; billed time. The defect on
this ring is small (5 sites at 12:24 CET), so a small effect is expected if any. **Stop.** One run of the two jobs.
