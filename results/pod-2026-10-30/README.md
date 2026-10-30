# GPU pod of 2026-10-30 (workplace): the twin of test 2 and the stand-in of QELM task A — simulations, not device results

- **Pod:** one H100 SXM (Secure Cloud), operated by the workplace's PC-side Claude by API and SSH. TOQB b82f321;
  declarations `echo_hz_note.md` (1308cf9b...) and `qelm_A_note.md` (8c26afd7...) as fixed 03:30:50 CET; tests 8
  (echo) and 7 (qelm) passed; no STOP, no error. Echo twin 04:20-04:58 CET; QELM stand-in 04:19-08:18 CET (rule
  5,565 s, zipcyc 8,736 s; home's estimate of about 2 h was half the real time).
- **Files** (SHA-256 as computed at the workplace, checked at home): `echo_twin.zip` 9ff10518..., `qelmA.zip`
  6886686b..., `echo_smoke.zip` 4470fd8b..., `qelm_smoke.zip` f2ef6a93..., logs `echo_twin.txt`, `qelmA.txt`; the
  workplace's readings `報告_テスト2_twin_2026-10-30.md` (its section 6 is corrected by section 3 of the next),
  `報告_POD結果_2026-10-30.md`, `記録_規則B追補_2026-10-30.md`; the diagnostic `echo_twin_se_diag.py` (not part of TOQB).

## Test 2 twin (n = 20, rule and zipcyc, marrakesh 2026-10-13 snapshot, T = 64)

| arm | hz | rho_E D 24 | D 50 | D 100 |
|---|---|---|---|---|
| rule | 0 / 0.1 / 0.3 | 0.084 / 0.095 / 0.099 | about 0 | about 0 |
| zipcyc | 0 / 0.1 / 0.3 | 0.001 / 0.002 / 0.003 | about 0 | about 0 |

- The echo decays far faster than the charge (L* about 10 against 56.5 on the device). The workplace's per-trajectory
  diagnostic: trajectories with any error give about 0, error-free ones carry the signal; SE of rho_E at D = 24 about
  0.04. Read at home: rho_E ~ exp(-n D / V*) with V* about 194, the volume picture of test 3 (post-hoc, simulation).
- Consequence fixed before any fetch: test 2 addendum 1 (rule B not judged on the floor), test 3 addendum 1 (part E
  dropped).

## QELM A stand-in (n = 20, L = 19, rule and zipcyc)

| arm | lambda median (X, Y, Z) | declared lambda | acc S 64 | acc S 250 |
|---|---|---|---|---|
| rule | 0.578, 0.576, 0.729 | 0.714 | 0.695 | 0.840 |
| zipcyc | 0.222, 0.214, 0.444 | 0.284 | 0.690 | 0.785 |

- McNemar rule vs zipcyc: S 64 35 / 34 (p 0.50), S 250 31 / 20 (one-sided p 0.080): Q3a on the "not WIN" side.
- Both accuracies inside their declared (marrakesh-row) bands at S = 250.
- **Correction recorded:** the workplace's warning (and home's, 2026-10-30 05:42 CET) that QELM's features would decay
  like the echo (lambda about 0.1, accuracy near chance) was wrong on the stand-in. The echo and the parity are
  "any error destroys it" quantities; the forward features are not.
- Consequence: QELM A runs on ibm_kingston only (addendum 1, 08:45 CET).
