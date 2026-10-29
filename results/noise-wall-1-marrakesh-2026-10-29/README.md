# Noise wall stage 1 on ibm_marrakesh (2026-10-29): probe P1 (weight-2 charge) and probe P2 (<X_0>) of the kicked-Ising ring, n = 20 and 36, three map-free arms, device only

- **Declaration:** `prereg/drafts-2026-10-29/noise_wall_1_second_device_note.md` r2, SHA-256 d963adb6… (0ee6343,
  fixed 11:13 CET, before any fetch). Run first of the two devices (owner: the emptiest queue first); ibm_kingston
  follows under `noise_wall_1_note.md` r3 (7415beca…).
- **Fetch (home, 11:13:17 CET):** ibm_marrakesh, calibration 11:03:12 CET, Target SHA-256 da19f889…. Used for the
  basis, the working couplers and the failed-element rule only.
- **Build (home, CPU, TOQB 0ee6343, 11:15-11:18 CET):** tests 40 passed; charge check PASS at n = 20 and 36; all 30
  cells valid (every arm placed at both n).
- **Jobs** (submitted with dynamical decoupling and twirling off, no mitigation):

  | job | id | content | submitted | time model | billed |
  |---|---|---|---|---|---|
  | 1 | `dbhhsncdgr2s73ctiung` | P1, 288 circuits × 1000 shots | 11:22 CET | 91.1 s | **92 s** (first time above the model) |
  | 2 | `dbhhuc9t9uhs73ca9t70` | P2, 768 circuits × 250 shots | 11:25 CET | 82.5 s | 62 s |

- **Files.** `fetch.json`, `times.txt`, `build.txt`, `cells.txt`, `assemble*.txt`, `check_tests.log`,
  `rehearse.txt`, `runs1/`, `runs2/` (records), `job1/`, `job2/` (manifest, submission, raw counts gzipped, scores),
  `score1_selfref.txt`, `score_p2_lam.txt`, `score_p2_selfref.txt`.
  - The circuit files (`circuits.qpy` 179 MB and 408 MB, `runs*/*.qpy`) are not committed; SHA-256 in
    `qpy_sha256.txt`. They are in the owner's `nw1_marrakesh_jobs_2026-10-29.zip` and `nw1_marrakesh_result/`.
- **Scoring:** `kising_charge score --self-ref-n 20 --self-ref-L 24` (the declared rule: p from this device's own
  rule cell at n = 20, L = 24, p = 0.00719) and `lam_device score` for P2.

## P1: the four-input charge ratio rho (± SE, 1000 shots)

| n | L | rule | zipcyc | blind Qiskit |
|---|---|---|---|---|
| 20 | 24 | 0.630 ± 0.009 | 0.204 ± 0.008 | 0.396 ± 0.009 |
| 20 | 50 | 0.426 ± 0.009 | 0.039 ± 0.008 | 0.156 ± 0.008 |
| 20 | 100 | 0.174 ± 0.008 | 0.012 ± 0.008 | 0.027 ± 0.008 |
| 36 | 24 | 0.646 ± 0.007 | 0.217 ± 0.006 | 0.217 ± 0.006 |
| 36 | 50 | 0.413 ± 0.007 | 0.042 ± 0.006 | 0.040 ± 0.006 |
| 36 | 100 | 0.178 ± 0.006 | −0.001 ± 0.006 | 0.001 ± 0.006 |

**Readable depth L\*** (1/e decay length, fit over L = 24, 50, 100):

| n | rule | zipcyc | blind Qiskit | ΔL against zipcyc | ΔL against blind Qiskit |
|---|---|---|---|---|---|
| 20 | 56.5 ± 0.9 | 15.1 ± 0.4 | 26.4 ± 0.5 | +41.3 ± 1.0 | +30.1 ± 1.0 |
| 36 | 56.6 ± 0.7 | 15.7 ± 0.3 | 15.7 ± 0.3 | +40.9 ± 0.7 | +40.9 ± 0.7 |

## P2: device slope lam of <X_0> (± SE, 64 inputs × 250 shots)

| n | L | rule | zipcyc | blind Qiskit | formula at p = 0.00719 |
|---|---|---|---|---|---|
| 20 | 24 | 0.046 ± 0.024 | 0.025 ± 0.023 | 0.040 ± 0.022 | 0.097 |
| 20 | 50 | 0.073 ± 0.051 | 0.088 ± 0.048 | −0.045 ± 0.045 | 0.037 |
| 36 | 24 | 0.004 ± 0.056 | 0.020 ± 0.041 | 0.146 ± 0.045 | 0.137 |
| 36 | 50 | 0.127 ± 0.039 | 0.049 ± 0.036 | −0.033 ± 0.038 | 0.031 |

## Predictions against results (declared, r2)

| # | declared | result | held? |
|---|---|---|---|
| 1 | the rule's rho at the other 5 cells from one p fixed at n = 20, L = 24 | INSIDE at n = 36, L = 24 only; OUTSIDE at L = 50 and 100 (both n): the device decays more slowly at depth than one p says | **no** (1 of 5) |
| 2 | the rule's rho independent of n (2 SE) | SAME at L = 24, 50, 100 | **yes** (3 of 3) |
| 3 | P2: AGREE in the rule's four cells at prediction 1's p | BELOW (n 20 L 24; n 36 L 24), AGREE (n 20 L 50), ABOVE (n 36 L 50) | **no** (1 of 4) |
| 4 | rule WIN against zipcyc and blind Qiskit, on rho and on lam | rho: WIN 12 of 12. lam: WIN 1 (n 36 L 50 against Qiskit), TIE 7 | **P1 yes; P2 no** |
| 5 | L\*_rule inside the prediction from p (51.9 ± 1.6) | 56.5 and 56.6: ABOVE | **no** |
| 6 | zipcyc κ inside its structure bracket (2.27-2.30; 2.25-2.39) | κ = 3.73 ± 0.11 and 3.60 ± 0.08: ABOVE | **no** |
| 7 | blind Qiskit φ the same at both n | 0.25 ± 0.01 and 0.31 ± 0.01: DIFFERENT | **no** |

## Reading

- **Vanity:** the rule won all 12 charge comparisons and kept a readable depth of 56-57 steps, against 15-26 for
  the zipper and blind Qiskit: about 30-41 steps deeper, on a device and day where no arm read a quality number.
- **Essential:**
  - **What held is the comparison and the size-independence, not the noise model.** The rule's charge decay is the
    same at n = 20 and 36 (L\* 56.5 and 56.6). But one uniform p does not describe it: the decay is faster up to
    L = 24 than beyond.
  - **Structure does not explain the zipper's loss.** It decays 3.6-3.7 times faster per step than the rule, where
    gate count and duration say 2.3. Per extra gate it costs more than the rule's gates do. The declaration said this
    rule was sharp and not safe; it failed.
  - **P2 is at the noise floor here.** Its slopes are 0.00-0.15 with SE 0.02-0.06, and the rule's n = 36 cells move
    the wrong way with depth (0.004 at L = 24, 0.127 at L = 50). P2 at 250 shots does not decide anything on this
    device.
- **Not used in the test, read afterwards (post-hoc diagnosis):** the rule's n = 36 output qubit (physical 11) has a
  10.5 % readout error on the day's calibration, about 5 times the median (2.0 %). Readout alone scales lam by about
  0.8, so it does not explain the n = 36, L = 24 cell. Not established.
- **Not established:** why the rule's decay is not one exponential; why the zipper's extra gates cost more than
  average; anything about kingston (run next) or other days.
