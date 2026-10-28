# Device test D6 (2026-10-28): rule, zipper and blind Qiskit at L = 16, n = 13-24 on ibm_kingston, no quality number read by any arm, no simulator

- **Declaration:** `prereg/drafts-2026-10-28/device_d6_note.md`, SHA-256 85b358b7… (30da96a, 15:24 CET).
- **Fetch (home, 15:26:12 CET):** ibm_kingston, calibration 14:37:55 CET, Target SHA-256 dd62d353…. It was used only
  for the basis, the working couplers and the failed-element rule.
- **Pod step (TOQB 30da96a, psf-zero 2cc4f7b6):** 15:39:03 to 15:46:56 CET.
  - Tests: 15 passed.
  - Declared check PASS: the GPU noiseless reference equals Qiskit's to 2.0e-15.
  - 30 cells, no twin; time model 201.7 s.
- **Job:** `dbh0s6sdgr2s73csfnrg`.
  - Submitted 16:00:03 CET; queued until 16:25:25; done 16:32:49.
  - Calibration at submission: 15:26:22 CET, newer than the fetched 14:37:55.
  - 1920 circuits × 250 shots. **145 s billed.**
- **Files:** `fetch.json`;
  - `times.txt`, `build.txt`, `cells.txt` (qubits used and measured qubit per cell), `assemble.txt`,
    `check_tests.log`, `runs/*.json`, `job/` (manifest, submission, raw counts gzipped, lam_score), `score.txt`.
  - The circuit files (`job/circuits.qpy` 350 MB and `runs/*.qpy`) are too large for GitHub. They are not committed;
    their SHA-256 values are in `qpy_sha256.txt` and the files are in the owner's `d6_result.zip` (SHA-256
    63c83f09…).
- **Scoring:** `lam_device score` at TOQB 30da96a.

## Result (device lam ± SE; 64 inputs × 250 shots each)

| n | rule (2Q, µs) | zipper, same qubits (2Q, µs) | blind Qiskit (2Q, µs) | rule − zipper | rule − Qiskit |
|---|---|---|---|---|---|
| 13 | 0.78 ± 0.11 (224, 9.2) | – | 0.38 ± 0.11 (271, 22.3) | – | **WIN** +0.40 (2.6 SE) |
| 14 | 0.75 ± 0.08 (256, 9.2) | 0.61 ± 0.10 (496, 10.6) | −0.08 ± 0.22 (533, 50.6) | TIE +0.14 | **WIN** +0.83 |
| 15 | 0.90 ± 0.08 (288, 9.3) | – | 0.00 ± 0.07 (906, 88.0) | – | **WIN** +0.89 |
| 16 | 0.85 ± 0.09 (320, 9.3) | 0.48 ± 0.09 (576, 10.6) | −0.02 ± 0.11 (460, 41.9) | **WIN** +0.37 | **WIN** +0.87 |
| 17 | 0.91 ± 0.08 (352, 9.3) | – | −0.07 ± 0.10 (821, 78.5) | – | **WIN** +0.98 |
| 18 | 0.58 ± 0.09 (352, 6.7) | 0.50 ± 0.09 (656, 10.6) | 0.05 ± 0.14 (789, 74.7) | TIE +0.08 | **WIN** +0.53 |
| 19 | 0.78 ± 0.11 (336, 6.2) | – | 0.37 ± 0.14 (751, 70.4) | – | **WIN** +0.42 (2.3 SE) |
| 20 | 0.83 ± 0.07 (320, 5.6) | 0.69 ± 0.06 (736, 10.6) | 0.49 ± 0.11 (320, 25.9) | TIE +0.14 | **WIN** +0.35 (2.6 SE) |
| 21 | 0.85 ± 0.09 (352, 9.2) | – | 0.08 ± 0.10 (926, 83.8) | – | **WIN** +0.77 |
| 22 | 0.69 ± 0.12 (384, 9.2) | 0.32 ± 0.13 (816, 10.6) | 0.09 ± 0.10 (1216, 107.7) | **WIN** +0.37 | **WIN** +0.60 |
| 23 | 0.37 ± 0.15 (400, 6.2) | – | 0.00 ± 0.21 (1034, 92.6) | – | TIE +0.37 |
| 24 | 1.00 ± 0.13 (384, 5.6) | 0.38 ± 0.11 (896, 10.6) | 0.41 ± 0.14 (384, 30.0) | **WIN** +0.62 | **WIN** +0.59 |

- **Rule against blind Qiskit:** WIN 11, TIE 1 (n = 23), LOSS 0.
- **Rule against the zipper on the same qubits:** WIN 3 (n = 16, 22, 24), TIE 3 (n = 14, 18, 20), LOSS 0. The rule's
  lam was the larger one at all 6 even n.

## Predictions against results

| declared | result | held? |
|---|---|---|
| WIN against the zipper at all 6 even n | 3 WIN, 3 TIE | **no** (3 of 6) |
| WIN against blind Qiskit at every n where Qiskit needs more gates (all but 20 and 24) | WIN at 9 of 10, TIE at n = 23 | **no** (9 of 10) |
| n = 20 and 24 against Qiskit: no claim | WIN at both | – |

## Reading

- **Vanity:** the rule won 14 of 18 comparisons and lost none, on a device day where no arm read a quality number.
- **Essential:**
  - Blind Qiskit kept no measurable signal (|lam| < 0.1) at 8 of 12 n. Its circuits ran 22-108 µs against the rule's
    5.6-9.3 µs.
  - Where Qiskit found the cycle by itself (n = 20, 24: the same gate count, 4.6-5.4 times the duration), it kept
    about half of the rule's lam.
  - In shots for a fixed precision (1/lam²), Qiskit needs about 2.9 times the rule at n = 20 and 6 times at n = 24;
    elsewhere it cannot be read at all.
  - The zipper on the same qubits kept 0.38-0.86 of the rule's lam. With 250 shots, half of these differences fell
    within 2 SE.
- **Compared with D5 part A** (n = 20, a different calibration hour, 1000 shots): Qiskit with the Target's error
  rates kept 0.77; blind it kept 0.49. Calibration-driven placement is worth about 0.3 in lam here. That is a
  between-job comparison, not a declared one.

## Not established

- **Why the rule's lam varies between n** (0.37 at n = 23, 1.00 at n = 24). There is one model per n, 250 shots, and
  different cycles and readout qubits.
- **Whether the zipper TIEs are real ties or lack of shots.** A difference of 0.1-0.15 needs about 4 times the shots
  to decide.
- **Anything for other models, other days or other devices.**
