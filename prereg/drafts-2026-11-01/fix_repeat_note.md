# Fix repeat: does the two-qubit frame flip at 27, 29 still fix kingston's dead run a day later? (home, 2026-11-01; declared on the owner's go of 2026-11-01 03:01 CET)

**Why.** On 31 October (`results/black-fix-2026-10-31`, job dbivq656p51s73cjp9d0, calibration 14:58 CET) the frame
flip at qubits 27 and 29 (ring positions 6, 8 of the rule's standard n = 40 ring; couplers (17, 27) to (29, 38)) lifted
the dead block (38, 49-55, 59) from -0.193 to +0.129 at D = 24 (+0.322 +- 0.007), with the rest of the ring at +0.008.
Coverage day 2 (1 November, 01:49 CET) found the same 18-site dead run again. A repair worth keeping in a list must
work on another day without being searched again.

**Design (one job, ibm_kingston, after this note and a new fetch).** The standard n = 40 ring (unmasked fetch), hz 0,
h 0.6, 4 inputs and 4 references, 1000 shots, options off. Off, the global flip and the flip at 27, 29 (tag B3), at
D = 12 and 24: 6 records, 48 circuits, 17.7 s predicted (`gpu/fix_repeat.sh`; dry run on the 1 November 00:27 CET
fetch: all accepted, B3 the declared qubits, and the off and B3 circuits byte-identical to 31 October's).

**Judged at D = 24 (`toqb.ff_score`; block = 38, 49-55, 59; rest = the ring minus the 18-site run; 2 combined SE).**
- **R1:** B3 block minus off: HELPS / NO EFFECT / HURTS.
- **R2:** B3 rest minus off: NO COST (not below -2 SE) / COSTS.
- **PERSISTS** if R1 HELPS and R2 NO COST.

**One sentence per outcome (fixed in advance).**
- PERSISTS: the two-qubit flip at 27, 29 fixes the dead run on a second day with the same circuit; a repair entry
  (path -> flipped qubits) can be kept in the list like a dead path.
- Otherwise: the repair does not carry over; it must be found again on the day of use.

**Reported.** B3's gain beside 31 October's +0.322; D = 12; the global flip; RECOVERED (block >= 0.8 x rest); per
site. **Stop.** One job.
