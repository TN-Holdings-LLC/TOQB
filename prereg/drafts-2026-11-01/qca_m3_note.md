# OS plan M3: does avoiding the listed dead paths make a forward (non-mirror) computation more right? (home, 2026-11-01; declared on the owner's go of 2026-11-01 11:46 and 12:32 CET)

**Why.** The defect list widened the usable part of the rule's rings on three devices (coverage days; M4). All of
that was measured with the mirror echo. An OS has to help computations that do not undo themselves. M2 (the repair
on such circuits) is not run: in simulation the frame flip gains nothing on a non-mirror circuit
(`results/qca-m3-2026-11-01/sim/`), so the OS repairs only mirror-type circuits and avoids everywhere.

**The computation.** n layers of (H on every qubit, then CZ on every ring coupler) on an n-ring. Its symplectic
matrix has order exactly n (n = 20, 40, 72), so the circuit is the identity: the output must equal the input bit by
bit (stabilizer simulation on the four inputs, `tests/test_qca.py`; the compiled n = 20 and n = 40 circuits return
every input on every site without noise). No layer is undone by a later one. `toqb/qca_test.py`.

**Design (ibm_kingston, after this note and a new fetch; two jobs).**
- **Job S (standard, map-free):** the rule's rings at n = 20 (D = 20; control) and n = 40 (D = 40; the ring with the
  18-site dead run).
- **Job V (self-checked):** n = 40 on the ring placed when the fetch is masked by
  `results/coverage-days-2026-11-01-day2/list_after.json` (`defect_list mask`).
- 4 inputs (zero, one, neel, antineel) and 4 readout references per ring, 1000 shots, options off. S: 16 circuits,
  7.9 s; V: 8 circuits, 5.4 s (`gpu/qca_m3.sh`; dry run on the 1 November 00:27 CET fetch: all accepted; the avoid
  ring leaves [28, 29, 38, 49]).

**Scored (`qca_test score`).** Per site a_j = mean over the inputs of <z_in,j Z_j> (1: always the right bit; 0:
random); mean over the ring and its SE; usable sites (outside runs of >= 3 sites below 0.12); per-bit right
fraction (1 + mean) / 2; whole-string match.

**Judged at n = 40.**
- **Q1:** mean signal over the ring, V minus S, 2 SE: HELPS / NO EFFECT / HURTS.
- **Q2:** usable sites, V minus S: WIDER (>= +3) / SAME / NARROWER.
- **Readable:** if V's mean signal is below 0.05 the computation is too deep to read on this device: INCONCLUSIVE,
  nothing else is judged.

**One sentence per outcome (fixed in advance).**
- Q1 HELPS and Q2 WIDER: avoiding self-measured dead paths makes a forward computation right on more of the ring; the
  allocator helps computation, not only the echo.
- Q2 WIDER, Q1 not HELPS: more sites carry a signal but the ring as a whole is not more right.
- Otherwise: the allocator's gain does not carry to this computation.

**Reported.** Per-bit right fraction, whole-string match, the n = 20 control, dead runs, per site, billed time.
**Stop.** One run of the two jobs.
