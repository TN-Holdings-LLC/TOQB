# Test 3, addendum 1 (home, FIXED 2026-10-30 06:10 CET on the owner's go, before any fetch): part E dropped; the longest ring of the day added to part P

Applies to `test3_note.md` (SHA-256 8b13773f0dc7545ce0446d8fbbe1769f89e46fb0ed81f69ef5f3c4ea72896922, fixed 05:32 CET).

1. **Part E (the mirror at n = 40 and 72) is not run.** By the volume formula (V* = 2 L*, 113-171 from 10/29), the echo
   at n = 40 and 72 sits below 2 SE at every depth, even if the device were twice as good (n = 72, D = 24: about
   0.006). The decision is made from this formula, not from the twin's numbers.
2. **Part P adds the longest exact ring of the day's map** (`fold.fold_place` with m = n, even n, searched from 120
   down; kingston 2026-10-24: 88). At that n: L = 1 and 2, all three arms, 4000 shots (the readout loss at about 90
   qubits leaves roughly a tenth of the signal at depth 0), its own job: 48 circuits, time model 48 x 0.036 +
   48 x 4000 x 0.00027 + 3 = 56.6 s. **Reported only, not judged** (n is set by the day's map).
   - Expectation (kingston, V* = 171): rho_P about 0.6 at L = 1 and 0.36 at L = 2; SE about 0.1.
3. **Part P otherwise unchanged:** n = 20 and 36 judged (P-A, P-B, P-C), 40 and 72 reported, 288 x 1000 shots, 91.1 s.
4. **A note on the expected direction.** The declaration says that if P-A fails, BELOW is expected. On a fake device
   (FakeFez, n = 8, rule with holes; home, 2026-10-30) the charge gave L* = 25.0 (so V* = 50 predicted) and the parity
   V* = 65.0 +- 1.5: ABOVE by 30 %. One case; the direction of a miss is not known in advance. The rule is unchanged.

**Time per device:** test 2 76.9 s + part P 91.1 s + longest ring 56.6 s = 225 s (about 3.8 min); two devices about
7.5 min.
