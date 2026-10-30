# Test 2, addendum 1 (home, FIXED 2026-10-30 06:10 CET on the owner's go, before any fetch): rule B is not judged on the noise floor

Applies to `echo_hz_note.md` (SHA-256 1308cf9bec09d25cae977688baae6c16431f1f32c5dcbd6cfcae07b7d8503696, fixed by the
workplace 2026-10-30 03:30:50 CET). Nothing else changes: arms, n, hz, depths, shots, rule A.

**Change.** Rule B (zipcyc's kappa inside [3.3, 3.9]) is judged at a (hz, n) only if zipcyc has at least one depth whose
rho_E exceeds 2 SE. Otherwise B is NOT JUDGED there, and the computed kappa is reported with the note "zipcyc below
2 SE at every depth: kappa carries no information".

**Why.** The same principle as rule A's floor clause. The workplace's twin (2026-10-30, report of 05:34 CET) put
zipcyc below the floor at every depth, where kappa would be a ratio of noise. The echo's Z_j is not conserved and
spreads over the ring, so it decays like a weight-n quantity (the volume picture of test 3: rho_E ~ exp(-n D / V*)).

**Not changed by the twin.** No depth, hz or n is chosen from the twin's numbers.
