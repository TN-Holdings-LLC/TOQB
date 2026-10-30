# Device runs of 2026-10-30: test 2 (echo, n = 20, 36), test 3 (echo n = 40, 72; parity size; longest ring) and QELM task A

- **Devices:** ibm_marrakesh and ibm_kingston (Open Plan). QELM A on ibm_kingston only (owner's decision).
- **Declarations** (all fixed before any fetch; `prereg/drafts-2026-10-30/`): `echo_hz_note.md` 1308cf9b...,
  `echo_hz_addendum1.md` a206c81a..., `test3_note.md` 8b13773f..., `test3_addendum1.md` 1c484fa8...,
  `test3_addendum2.md` 78986cf3... (part E restored), `qelm_A_note.md` 8c26afd7..., `qelm_A_addendum1.md` 4cfff876....
  Code TOQB e36fe83. Map-free standard; no setting chosen from a simulation.
- **Fetch** (calibration snapshot): marrakesh 10:20 CET, kingston 11:02 CET. At submission the device's calibration
  had moved on (marrakesh 11:47 / 12:08, kingston 11:54 / 12:17); the placement reads no map, so this changes no
  circuit, only the noise the circuits met.
- **Billed time:** marrakesh 67 + 71 + 81 + 54 = 273 s; kingston 65 + 69 + 78 + 53 + 69 + 71 + 70 = 475 s; total
  748 s (time model about 900 s).
- **Files** per test and device: `fetch.json`, `build.txt`, `rehearse.txt`, `assemble.txt`, `times.txt`,
  `check_tests.log` (where run), `runs*/` (per-circuit records), `job*/` (`manifest.json`, `submission.json`,
  `raw_counts.json.gz`, score JSON), `score*.txt`. The compiled circuits (`*.qpy`, some over 100 MB) are not
  committed; their SHA-256 are in `qpy_sha256.txt`. `Device_2026-10-30_raw.xlsx`: every cell in one workbook.
  The manifests of all 11 jobs matched the submitted circuits.

| job | ibm_marrakesh | ibm_kingston |
|---|---|---|
| test 2 (echo n 20, 36) | dbi7pmg1h92s7382ubkg | dbi7r45ep8hs73anb5q0 |
| test 3E (echo n 40, 72) | dbi7qg6ne4hc73be2nf0 | dbi7rtene4hc73be2p8g |
| test 3P (parity n 20, 36, 40, 72) | dbi7qig1h92s7382ucn0 | dbi7rvune4hc73be2pcg |
| test 3P longest ring | dbi7qkmne4hc73be2njg | dbi7s1tep8hs73anb72g |
| QELM A fold:rule | - | dbi7sjg1h92s7382ufbg |
| QELM A fold:zipcyc | - | dbi7ti6ne4hc73be2rd0 |
| QELM A qiskit:2:blind:template | - | dbi7u5mne4hc73be2s80 |

## Test 2 and test 3E: the mirror echo with hz = 0, 0.1, 0.3 (non-integrable for hz > 0)

| | kingston n 20, 36 | marrakesh n 20, 36 | kingston n 40, 72 | marrakesh n 40, 72 |
|---|---|---|---|---|
| rule A duels (WIN / TIE / LOSS / NOT JUDGED) | 24 / 2 / 0 / 10 | 16 / 3 / 0 / 17 | 14 / 2 / 0 / 20 | 17 / 4 / 0 / 15 |
| rule rho_E at D = 24 (range over hz) | 0.37-0.44 | 0.20-0.25 | 0.17-0.25 | 0.20-0.24 |
| rule B (zipcyc kappa in [3.3, 3.9]) | BELOW in 6 / 6 | BELOW in 6 / 6 | BELOW in 6 / 6 | 5 NOT JUDGED (floor), 1 ABOVE |

- **Overall:** 71 WIN, 11 TIE, **0 LOSS**, 62 NOT JUDGED (both arms on the noise floor, mostly D = 50 and 100).
  The rule's lead holds at every hz: breaking integrability did not remove it.
- **Rule B's floor clause** (`echo_hz_addendum1.md`, applied to part E by `test3_addendum2.md`): B is judged at
  (hz, n) only if zipcyc's rho_E exceeds 2 SE at some depth. On kingston and on marrakesh's test 2 it does
  everywhere (at D = 24), so the BELOW verdicts stand (kappa 1.7-2.7). On marrakesh's part E zipcyc is below 2 SE
  everywhere except hz 0.1, n 40 (2.2 SE, at D = 100 only), where kappa 5.4 +- 12 is ABOVE; the script's raw
  verdicts for the other five (ABOVE / INSIDE) are ratios of noise and are NOT JUDGED.
- **Failed prediction (reported):** the volume picture read from the pod's twin (rho_E ~ exp(-n D / V*), V* about
  194) predicted the rule's echo below 2 SE at n = 40, 72 and about 0.08-0.10 at n = 20, D = 24. On the device it is
  0.17-0.44 at D = 24 and does not shrink with n up to 72 (kingston n 36 is higher than n 20). Our reading
  (post-hoc, not tested): the echo's weight is bounded by the light cone of D layers, not by n, so no size wall
  appears for a local echo at these depths. The twin's noise model under-estimates both devices.

## Test 3P: the global parity P = prod X_j (weight n), size probe

- **P-A** (rule's V* inside the declared band): **1 / 4 INSIDE**. V*_rule kingston 72.6 +- 3.9 (n 20), 105.8 +- 11.2
  (n 36) against 171 declared (BELOW, BELOW); marrakesh 59.8 +- 4.4, 76.4 +- 13.9 against 113 (BELOW, INSIDE).
  zipcyc's V* is INSIDE in 4 / 4 (kingston 38.9, 63.2 vs 47.5; marrakesh 29.6, 29.4 vs 31.4).
- **P-B** (kappa = V*_rule / V*_zipcyc in [3.3, 3.9]): **1 / 4 INSIDE** (kingston 1.87, 1.67; marrakesh 2.02, 2.59).
- **P-C** (duels at the judged n = 20, 36): kingston 11 WIN / 1 TIE; marrakesh 8 WIN / 4 TIE; no LOSS.
- **n = 40, 72 (reported):** unreadable. The readout reference (half-filled strings, used to divide out readout
  loss) falls with n: about 0.4-0.6 at n = 20, 0.1-0.3 at n = 40, about 0 on marrakesh at n = 72. The parity's size
  wall on these devices is set by readout, not by the circuit.
- **Longest ring** (exact ring of the day, searched from 120 down): kingston n = 88, fold:rule L = 1 rho_P
  0.22 +- 0.10 (2.2 SE; WIN against both arms at L = 1, TIE at L = 2); marrakesh n = 96, reference about 0,
  unreadable. Reported, not judged.

## QELM task A on ibm_kingston (n = 20, L = 19, search-free classifier)

| arm | G | lambda (X, Y, Z) | Q1 (chi2) | acc S 64 | acc S 250 | Q2 band | Q2 |
|---|---|---|---|---|---|---|---|
| fold:rule | PASS | 0.703, 0.656, 0.878 | 2.87 FAILS | 0.740 | 0.810 | 0.745-0.900 | INSIDE |
| fold:zipcyc | PASS | 0.349, 0.377, 0.683 | 1.73 HOLDS | 0.650 | 0.715 | 0.690-0.845 | INSIDE |
| qiskit:2:blind:template | PASS | 0.567, 0.488, 0.806 | 3.45 FAILS | 0.695 | 0.750 | 0.680-0.855 | INSIDE |

- **Q3a** (rule against zipcyc, one-sided McNemar with Holm): S 64 47 / 29, p 0.025; S 250 37 / 18, p 0.007:
  **WIN**. **Q3b** (rule against Qiskit): p 0.18, 0.067: not (reported, not judged).
- **R:** raw-input baseline 0.555; noiseless ceiling 0.840; majority 0.510. The rule's 0.810 at S = 250 is 96 % of
  the ceiling.
- **Q1 fails for rule and Qiskit:** the single-lambda model (effective shots lambda^2 S) does not fit the accuracy
  curve for those arms; it holds for zipcyc. The rule's lambda on the device (Z 0.88) is above the declared 0.714.

## What the day says (read at home; the verdicts above are the record)

1. The rule's lead in the echo survives non-integrability and size up to n = 72: 0 LOSS in 144 duels.
2. The declared fixed numbers missed again: rule B (echo kappa) and P-A / P-B (parity V*, kappa) came out BELOW in
   most cells. The rule's advantage on the device is about 2-2.5 times zipcyc, not 3.3-3.9.
3. At D = 24 the rule's echo does not shrink with n up to 72, but its L* does: about 23 at n = 20, 36, about 13-16 at
   n = 40, 72 (runs of near-random sites at n = 40, 72; see `rerun-rule-only/`, which repeats the pattern). The
   parity's wall on marrakesh is readout; on kingston n = 40 the readout reference was healthy and the parity was
   still lost (same ring as the echo's near-random runs).
4. QELM A: all arms inside their declared accuracy bands; the rule beats zipcyc at both shot counts.
