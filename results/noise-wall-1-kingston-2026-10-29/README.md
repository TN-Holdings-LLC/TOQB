# Noise wall stage 1 on ibm_kingston (2026-10-29): probe P1 (weight-2 charge) and probe P2 (<X_0>) of the kicked-Ising ring, n = 20 and 36, three map-free arms, device only

- **Declaration:** `prereg/drafts-2026-10-29/noise_wall_1_note.md` r3, SHA-256 7415beca… (0ee6343, fixed 11:13 CET,
  before any fetch). The second of the two devices run (ibm_marrakesh first, `../noise-wall-1-marrakesh-2026-10-29`).
- **Fetch (home, 12:03:13 CET):** ibm_kingston, calibration 11:51:22 CET, Target SHA-256 f8b6889f…. Basis, working
  couplers and the failed-element rule only. Calibration at submission: 11:57:24 CET (newer than the fetched one).
- **Build (home, CPU, TOQB dbe6d8a; code identical to 0ee6343, only results added since):** tests 40 passed; charge check PASS at
  n = 20 and 36; all 30 cells valid.
- **Jobs** (dynamical decoupling and twirling off, no mitigation):

  | job | id | content | submitted | time model | billed |
  |---|---|---|---|---|---|
  | 1 | `dbhiji1t9uhs73cab78g` | P1, 288 circuits × 1000 shots | 12:11 CET | 91.1 s | 90 s |
  | 2 | `dbhil0kdgr2s73ctkd20` | P2, 768 circuits × 250 shots | 12:14 CET | 82.5 s | 61 s |

- **Files** as in the marrakesh folder. `score1_declared.txt` is the judged score (declared p = 0.0051, range
  0.00475-0.00548); `score_p1ref_reference.txt` is the reference only (p from P1's rule n = 20, L = 50, p = 0.00467;
  owner's decision: reported, not judged). Circuit files not committed; SHA-256 in `qpy_sha256.txt`.

## P1: the four-input charge ratio rho (± SE, 1000 shots)

| n | L | rule | zipcyc | blind Qiskit | predicted (p = 0.0051) |
|---|---|---|---|---|---|
| 20 | 24 | 0.731 ± 0.009 | 0.354 ± 0.008 | 0.354 ± 0.008 | 0.721 |
| 20 | 50 | 0.536 ± 0.009 | 0.100 ± 0.008 | 0.077 ± 0.008 | 0.505 |
| 20 | 100 | 0.304 ± 0.008 | 0.008 ± 0.008 | 0.012 ± 0.008 | 0.256 |
| 36 | 24 | 0.790 ± 0.007 | 0.395 ± 0.007 | 0.249 ± 0.006 | 0.721 |
| 36 | 50 | 0.577 ± 0.007 | 0.141 ± 0.006 | 0.044 ± 0.006 | 0.505 |
| 36 | 100 | 0.314 ± 0.006 | 0.014 ± 0.006 | −0.009 ± 0.006 | 0.256 |

**Readable depth L\*:**

| n | rule | zipcyc | blind Qiskit | ΔL against zipcyc | ΔL against blind Qiskit |
|---|---|---|---|---|---|
| 20 | 81.3 ± 1.3 | 22.6 ± 0.4 | 22.0 ± 0.4 | +58.7 ± 1.4 | +59.3 ± 1.4 |
| 36 | 89.7 ± 1.1 | 25.6 ± 0.3 | 17.0 ± 0.3 | +64.1 ± 1.2 | +72.7 ± 1.1 |

## P2: device slope lam of <X_0> (± SE, 64 inputs × 250 shots)

| n | L | rule | zipcyc | blind Qiskit | formula at p = 0.0051 |
|---|---|---|---|---|---|
| 20 | 24 | 0.061 ± 0.031 | −0.004 ± 0.020 | 0.012 ± 0.018 | 0.185 |
| 20 | 50 | 0.027 ± 0.055 | −0.024 ± 0.048 | 0.015 ± 0.055 | 0.069 |
| 36 | 24 | 0.236 ± 0.060 | 0.063 ± 0.053 | 0.049 ± 0.045 | 0.190 |
| 36 | 50 | −0.008 ± 0.049 | 0.012 ± 0.040 | −0.044 ± 0.043 | 0.047 |

## Predictions against results (declared, r3)

| # | declared | result | held? |
|---|---|---|---|
| 1 | the rule's rho inside the prediction at p = 0.0051 (± 2 SE), each n and L | INSIDE at n 20 L 24 only; elsewhere the device is above the prediction (slower decay) | **no** (1 of 6) |
| 2 | the rule's rho independent of n | DIFFERENT at L = 24 and 50 (n = 36 higher by 0.06 and 0.04), SAME at L = 100 | **no** (1 of 3) |
| 3 | P2: the rule AGREE in all four cells at p = 0.0051 | BELOW at n 20 L 24; AGREE at the other three (two of them with SE about as large as the prediction) | **no** (3 of 4) |
| 4 | rule WIN against zipcyc and blind Qiskit, on rho and on lam | rho: WIN 12 of 12. lam: WIN 2 (n 36 L 24, both), TIE 6 | **P1 yes; P2 no** |
| 5 | L\*_rule inside 73.3 ± 5.3 (2 SE combined) | 81.3: INSIDE; 89.7: ABOVE | **no** (1 of 2) |
| 6 | zipcyc κ inside its structure bracket (2.24-2.30; 2.22-2.39) | κ = 3.60 ± 0.09 and 3.50 ± 0.06: ABOVE | **no** |
| 7 | blind Qiskit φ the same at both n | 0.54 ± 0.02 and 0.51 ± 0.01: SAME | **yes** |

## Reading

- **Vanity:** the rule won all 12 charge comparisons again, with L\* = 81-90 steps against 17-26: 59-73 steps deeper.
- **Essential:**
  - **The comparison held on both devices; the noise model did not.** Kingston decays more slowly than the declared
    p = 0.0051 (from D3/D4 on 10/28) at depth, as marrakesh did against its own p.
  - **n-independence held on marrakesh (SAME 3/3) but not here (1/3).** The n = 36 ring is better than the n = 20
    ring at L = 24 and 50. Different rings on different qubits; one day.
  - **The zipper's per-step penalty against the rule is about the same on both devices:** κ = 3.73, 3.60
    (marrakesh) and 3.60, 3.50 (kingston), against 2.2-2.4 from gate count and duration. Observed after the run; not
    a declared prediction.
  - **P2 at 250 shots is near the noise floor here too.**

## Two devices side by side (P1, the rule)

| | marrakesh n 20 | marrakesh n 36 | kingston n 20 | kingston n 36 |
|---|---|---|---|---|
| L\* | 56.5 | 56.6 | 81.3 | 89.7 |
| κ zipcyc | 3.73 | 3.60 | 3.60 | 3.50 |
| φ blind Qiskit | 0.25 | 0.31 | 0.54 | 0.51 |
| rule WIN on rho | 6/6 | 6/6 | 6/6 | 6/6 |
