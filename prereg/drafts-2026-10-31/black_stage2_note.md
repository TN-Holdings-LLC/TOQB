# Black stage 2: does a parameter-free frame flip bring back kingston's dead run? (home, 2026-10-31; declared on the owner's go of 2026-10-31 13:33 CET)

**Why.** Black stage 1 (`results/black-stage1-2026-10-31`, job dbitu9mne4hc73bfab6g): the dead block 38, 49-55, 59
on the standard n = 40 ring does not lose its signal at once; its Z signal turns over with depth (+0.96 at D = 2,
+0.27 at D = 12, -0.20 at D = 24; CROSSES ONCE), its single-site vector keeps 0.68 of the rest's length at D = 12
(MIXED), and it hardly tilts into X-Y. On 30 October gate twirling made the block random (coherent error) and
dynamical decoupling did nothing (not idle crosstalk). The owner: go to stage 2 on black.

**The operation (no parameter, nothing fitted).** `toqb.kising_echo build --frame-flip`: X on the even ring qubits
just before and just after the CZ ring of every even layer. On an even ring each CZ (q, q+1) has exactly one flipped
end and X_q CZ X_q = Z_a CZ, so every odd qubit gets Z twice and X_E (CZ ring) X_E = CZ ring: the ideal circuit is
unchanged (`tests/test_kising_echo.py`: operator equality at n = 6; the compiled n = 20, D = 8 echo reads 1.000 on
every site without noise). A coherent ZZ phase on any CZ changes sign in the flipped layers, so alternate layers
cancel it; in simulation (n = 10, the rule's echo, RZZ errors of 0.2 and 0.4 on couplers touching a 3-qubit block,
`results/black-stage2-2026-10-31/sim/`) the flip restores the block to 1.00 at every depth; it does nothing for a
single-qubit RX error. No extra two-qubit gate.

**Design (one job, ibm_kingston, after this note and a new fetch).** The rule's standard rings (unmasked fetch), hz
= 0, h = 0.6, 4 inputs and 4 references, 1000 shots, options off. n = 40: off and flip at D = 12 and 24; n = 20
(control, no dead run): off and flip at D = 24. 6 records, 48 circuits, 17.7 s predicted (`gpu/black_stage2.sh`; dry
run on the 13:13 CET fetch: all accepted, off and flip on the same ring, n = 40 D = 24 off byte-identical to
30 October, 42376e3f...).

**Judged (`python -m toqb.ff_score`; block = 38, 49-55, 59; rest = the ring minus the 18-site run).**
- **J (D = 24, primary):** block mean signal, flip minus off, against 2 combined SE: HELPS / NO EFFECT / HURTS; and
  RECOVERED if with the flip the block reaches 0.8 x the rest.
- **Control:** n = 20, flip minus off (the flip's own cost on a healthy ring), 2 SE.

**One sentence per outcome (fixed in advance).**
- HELPS and RECOVERED: the dead run was a coherent two-qubit phase error, and a parameter-free frame flip brings its
  information back; a candidate for the compiler (its cost from the control).
- HELPS, not RECOVERED: part of the dead run is such an error; the flip brings part back.
- NO EFFECT or HURTS: the dead run is not an error the flip cancels; the flip is not used and the run stays avoided.

**Reported.** D = 12 the same way; the rest of the n = 40 ring flip minus off; block A (3-7, 17, 27-29); per site.
**Stop.** One job.
