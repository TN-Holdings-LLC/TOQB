# Black bisection: where is the error that the global frame flip cancels? (home, 2026-10-31; declared on the owner's go of 2026-10-31 15:04 CET)

**Why.** On kingston's standard n = 40 ring the global frame flip lifts the dead block (38, 49-55, 59) by +0.295 and
+0.285 at D = 24 (black stages 2 and 3), but the same flip on the couplers touching the block does nothing (stage 3:
-0.007). So the error it cancels sits on couplers elsewhere on the ring and reaches the block through the circuit.
The owner: bisect.

**One round (one job; `gpu/black_bisect.sh`).** The rule's standard n = 40 ring (unmasked fetch; off at D = 24
byte-identical to 30 October), hz 0, h 0.6, 4 inputs and 4 references, 1000 shots, options off. Off, arm A and arm B
at D = 12 and 24: 6 records, 48 circuits, 17.7 s predicted. Arms are local frame flips (`kising_echo build
--flip-sites ... --flip-tag A|B`): X on the arm's even ring positions around the CZ ring of every even layer, virtual
Z on positions with an odd number of flipped neighbours; the ideal circuit is unchanged (operator-equality tests). A
flip on even positions e0, e0+2, ..., e1 covers the couplers from (e0-1, e0) to (e1, e1+1).

**Round 1 (fixed).** A = positions 0, 2, ..., 18 (qubits 3, 5, 7, 27, 29, 49, 51, 53, 55, 75; couplers (16, 3) to
(75, 74), the half with the dead run); B = positions 20, 22, ..., 38 (73, 71, 69, 67, 65, 63, 43, 41, 21, 23; the
other half). Together they cover every coupler once (the global flip).

**Later rounds (fixed by rule, no new note).** Judged at D = 24 (`toqb.ff_score`, block = 38, 49-55, 59): each arm's
block minus off, HELPS / NO EFFECT / HURTS at 2 SE.
- Exactly one arm HELPS: the next round splits that arm's positions in two, in ring order, the first half taking the
  extra position when the count is odd (10 -> 5 + 5 -> 3 + 2 -> 2 + 1 or 1 + 1).
- Both arms HELP: stop, SPREAD. Neither: stop, NOT IN ONE HALF.
- At most 4 rounds; stop when the helping arm has one position (LOCATED). Each round has its own fetch; a round's
  arms are written in its `times.txt` before its fetch is used.

**One sentence per end (fixed in advance).**
- LOCATED (or down to 2 positions after 4 rounds): the error the flip cancels sits on the couplers of that arm; a
  flip there alone is the candidate per-path fix (its cost and gain are a separate test).
- SPREAD or NOT IN ONE HALF: the error is not in one place; only the global flip helps, at its cost.

**Reported.** D = 12; each arm's rest minus off; per site.
