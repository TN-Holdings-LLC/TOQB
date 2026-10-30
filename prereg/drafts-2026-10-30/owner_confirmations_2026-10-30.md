# Owner's confirmations of the workplace's changes (2026-10-30 03:24 CET)

The workplace's report of 2026-10-30 (w72) listed three changes from the instructions, each pending confirmation.
The owner confirmed all three. The two declaration drafts below are still drafts (not fixed); their rules are not
changed by this note.

1. **Test 2 (`echo_hz_note.md`, SHA-256 1308cf9b...7503696): the flip W = X^n at the turn in place of a barrier.**
   TOQB's ring reader drops barriers, and in `model_circuit` form the turn would merge into diagonal gates that can
   cancel (CZ, RZ, CZ). With W the turn holds X gates, which do not commute with CZ, so nothing cancels; the ideal
   output is the flipped input. The acceptance rule (two-qubit gates = 2L x one layer) is unchanged.
2. **QELM task A (`qelm_A_note.md`, SHA-256 8c26afd7...d50f3b8): the centred teacher sign(w . (f0 - mu)).** Without
   centring, 81 % of the points fell in one class (ceiling 0.845 against a majority of 0.81). The change was made on the
   noiseless features only, not by looking at arms or noise; the uncentred computation is kept in the record.
3. **Ring extension (`fold.band_shapes`): bands are used only for n > 36.** The placements and refusals at n <= 36 are
   unchanged (so FakeFez still refuses n = 36 while it places n = 40).

Checked at home before this note: the workplace bundle (SHA-256 53cc6243...) fast-forwards from 95832c5; tests
test_kising_echo, test_fold, test_kising_charge, test_kising, test_kising_formula, test_lam_device_blind and test_qelm:
55 passed.
