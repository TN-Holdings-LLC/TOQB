# Test 3, addendum 2 (home, FIXED 2026-10-30 09:03 CET on the owner's go, before any fetch): part E restored, with rule B's floor clause; a correction to addendum 1

Applies to `test3_note.md` (8b13773f...) and `test3_addendum1.md` (1c484fa89df49eb19399870fdd915d5b83d2e2559a75c7cc7363c12d3c2fd2b3).

1. **Correction to addendum 1, item 1.** It said the echo at n = 40 and 72 stays below 2 SE "even if the device were
   twice as good". That is wrong. With the same formula and test 2's shot model (500 shots; checked by the workplace,
   2026-10-30 08:56 CET):

   | V* | n = 40, D = 24 (2 SE) | n = 72, D = 24 (2 SE) |
   |---|---|---|
   | 113 | 0.0002 (0.0071) | 0.0000 (0.0053) |
   | 171 | 0.0036 (0.0071) | 0.0000 (0.0053) |
   | 342 (twice 171) | 0.060 (0.0071) | 0.0064 (0.0053) |

   At the predicted V* the echo is below 2 SE at every depth; at twice V* the n = 40, D = 24 cell is clearly above and
   the n = 72 cell just above. The pod's twin (marrakesh snapshot, simulation) implies V* about 194-208 at n = 20, so
   "twice" is not remote.
2. **Part E is restored as declared in `test3_note.md`:** the mirror at n = 40 and 72, hz 0, 0.1, 0.3, one-way L 12,
   25, 50, three arms, 500 shots, 432 circuits, 76.9 s, one job; rules A and B of test 2.
3. **Rule B's floor clause applies to part E as to test 2** (`echo_hz_addendum1.md`, a206c81a...): B is judged at
   (hz, n) only if zipcyc exceeds 2 SE at some depth; otherwise NOT JUDGED, kappa reported with the note.
4. **Part P and the longest ring (addendum 1, items 2-4) are unchanged.**

**Time per device:** test 2 76.9 s + part E 76.9 s + part P 91.1 s + longest ring 56.6 s = 301.5 s (about 5.0 min);
QELM A on kingston adds 314.4 s. Both devices about 15 min.
