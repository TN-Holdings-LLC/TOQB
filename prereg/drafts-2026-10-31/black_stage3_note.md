# Black stage 3: the frame flip only around the dead block — the gain without the cost? (home, 2026-10-31; declared on the owner's go of 2026-10-31 13:52 CET)

**Why.** Black stage 2 (`results/black-stage2-2026-10-31`, job dbiu78nbipls73bdqi70): the frame flip on all even ring
positions lifted kingston's dead block (38, 49-55, 59) from -0.197 to +0.098 at D = 24 and from 0.272 to 0.550 at
D = 12, and removed the inversion at every block site (HELPS, not RECOVERED). It cost the healthy n = 20 ring 0.11
(0.350 -> 0.239) and the rest of the n = 40 ring 0.03. The owner: go on.

**The operation.** `kising_echo build --flip-sites 9,11,13,15,17`: X on ring positions 9, 11, 13, 15, 17 (physical 38,
50, 52, 54, 59 on the rule's standard n = 40 ring; the build stops if they are not) just before and just after the CZ
ring of every even layer, and Z (virtual) on positions 8 and 18, which have one flipped neighbour. Every coupler
touching the block, (29, 38) to (59, 75), has exactly one flipped end, so a coherent ZZ phase on it changes sign in
alternate layers; no other coupler is touched. The ideal circuit is unchanged (`tests/test_kising_echo.py`: operator
equality for local flips at n = 8; the compiled n = 20, D = 8 echo with a local flip reads 1.000 on every site
without noise). In simulation (n = 10, `results/black-stage3-2026-10-31/sim/local_fix.txt`) the local flip cancels
RZZ errors on couplers touching the block exactly, like the global flip, and leaves far sites as they are. No
parameter, no extra two-qubit gate.

**Design (one job, ibm_kingston, after this note and a new fetch).** The standard n = 40 ring (unmasked fetch), hz =
0, h = 0.6, 4 inputs and 4 references, 1000 shots, options off; off, global flip and local flip at D = 12 and 24. 6
records, 48 circuits, 17.7 s predicted (`gpu/black_stage3.sh`; dry run on the 13:13 CET fetch: all accepted, one
ring, the flip positions the declared qubits, off at D = 24 byte-identical to 30 October).

**Judged at D = 24 (`toqb.ff_score`; block = 38, 49-55, 59; rest = the ring minus the 18-site run; 2 combined SE).**
- **L1:** block, local minus off: HELPS / NO EFFECT / HURTS.
- **L2:** rest, local minus off: NO COST (not below -2 SE) / COSTS.
- **L3:** block, local minus global: KEEPS (not below -2 SE) / LOSES.

**One sentence per outcome (fixed in advance).**
- HELPS, NO COST, KEEPS: a flip placed only around a listed dead path gives the whole gain of the global flip without
  harming the rest; it is a per-path fix the compiler can key on the defect list.
- HELPS, NO COST, LOSES: the local flip helps without cost, but part of the gain needed the flip beyond the block.
- HELPS and COSTS: the local flip still harms the rest; not used as is.
- NO EFFECT or HURTS: the stage 2 gain is not reproduced locally; not used.

**Reported.** D = 12 the same way; global minus off (a repeat of stage 2); RECOVERED (block >= 0.8 x rest); per site.
**Stop.** One job.
