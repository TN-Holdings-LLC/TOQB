# Declared: the Ohm 6-cycle job repeated on another device, raw (Heron)

Home, 2026-11-12. Owner 20:00 JST ("別の機種で確認"), after the ibm_fez run of `prereg/ohm_2026-11-12.md`
(`results/ohm-2026-11-12`). Declared with this commit, pushed before the device record of this run is fetched; a change
after the push is a new declared file.

## What is repeated, unchanged

The circuits, strings, shots, answers, pre-run check and verdicts of `prereg/ohm_2026-11-12.md`: 40 qubits, arms A0 /
A1 / A2, 3 and 6 cycles, m 0.5, K 14 strings and their complements, seed 20261112, 1000 shots, 508 circuits;
`gpu/ohm_build.py` (placement by the same rules), `gpu/ohm_check.py --mirrors first:4`, `gpu/ohm_score.py`.

Answers: the same file, `ohm_answers.json` sha256 5580b676ce5f0f81651f80b6d3a42923f7022324b70a6a1db7b080231f3ae038,
**already released** with the fez result (`results/ohm-2026-11-12/answers`). They cannot be sealed again; the exact
values were fixed before the first run, and the build writes them by chain label (126e99ba..., as on fez).

## Device

Not ibm_fez (the point is another device). Among ibm_marrakesh and ibm_kingston, in the order of fewest pending (tie:
marrakesh first), the first on which the job builds. On the 11:19 CET record of today, marrakesh did not build (the
ring sentinel did not land on the user's ring; 14 failed qubits) and kingston did.
Try-build on that kingston record (home, 11-12): 508 circuits, 158.4 s by the model; CZ 234 / 468 (A0) and 351 / 702
(A1, A2), CZ depth 12 / 24 and 18 / 36, A1 and A2 equal; circuits_sha256 771c3b0e.... Its pre-run check is run before
submission (`check_trybuild.txt`); if the job built from the fresh record has the same circuits_sha256, the PASS
carries over, otherwise the check is run on the new build before submission. FAIL anywhere: not run.

## Verdicts

As declared for fez (`gpu/ohm_score.py OUT ANS`): READS / AGREES of the transferred magnetization M per arm and cycle
count; beside: W, its exponent, the drift D, the per-qubit <Z> verdicts, floor, mirror, sentinel, CZ.

New beside quantity (never judged, never used to correct): the mixed share p = (W_device - W_exact) / (W_mixed -
W_exact) per arm and cycle count, with W_mixed = 5.5 (W when every Z is 0, for these strings). On fez, after the data:
p 0.26 / 0.28 / 0.28 at 3 cycles and 0.46 / 0.45 / 0.43 at 6 (A0 / A1 / A2).

## Prediction (before any data of this run; not rewritten if wrong)

- No arm READS M at 3 or 6 cycles (fez: none of the six).
- Every circuit's per-qubit <Z> READS (fez: 28 / 28 in every arm and cycle count).
- The W exponents keep the exact ordering A0 > A1 > A2 (fez: kept).
- A1 and A2 (same CZ) have nearly the same mixed share: |p(A1) - p(A2)| <= 0.05 at each cycle count (fez: 0.00 and
  0.02). No prediction of the size of p on this device.

## Limits

One more device-day; raw values only; the answers are public, so this run tests the device, not a sealed prediction
of the answers; p is a one-number description of how far W moved towards the mixed value, not a noise model.
