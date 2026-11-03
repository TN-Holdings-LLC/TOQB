# P5 stage B, 2026-11-03: the utility-form kicked Ising circuit on ibm_kingston's whole lattice (151 qubits, 815 CZ at t = 5), without error mitigation: READS, and the magnetisation AGREES within 0.05 raw at every depth and theta

- **Declaration:** `prereg/drafts-2026-11-03/kim_lattice_note.md` (SHA-256 37699e33...b42a17a7), fixed 06:01 CET, TOQB
  4fd6574; psf-os 7faa7ab (`psf_os/kim.py`).
- **Job:** dbkmocl6p51s73cmvno0, built by `gpu/kim_lattice.py` from the fetch of 06:02:30 CET (calibration 05:25:48
  CET, target 815520ec...); answers sealed before sending in ce12ae1 (answers.json SHA-256 a0f55b4b...a41ff27d).
  Sent with `psf-os submit` at 06:08 CET, options off, "stay"; DONE, 38 s billed. 34 circuits x 4000 shots.
  Lattice: 151 qubits, 163 edges, 3 colour layers (failed (9, 10), (29, 38), (112, 113), (121, 122), (130, 131),
  (145, 146), (146, 147); masked (85, 86)). Scored by `gpu/kim_score.py`: `scores.json`.

## Judged

| theta | 2. MSE (half the answer's mean square) | 3. raw max \|M - M_exact\| | 4. normalised by theta 0 |
|---|---|---|---|
| 0.4 | 0.0030 (0.4239): **READS** | 0.042: **AGREES** | 0.021: **AGREES** |
| 0.8 | 0.0020 (0.1713): **READS** | 0.024: **AGREES** | 0.013: **AGREES** |
| 1.0 | 0.0011 (0.0710): **READS** | 0.007: **AGREES** | 0.009: **AGREES** |

1. Sentinel: **CLEAN**.

**Sentence fixed in advance (READS and AGREES raw at all three theta):** *psf-os reads the utility-form circuit on the
whole lattice without error mitigation, to depth 5.*

## Reported

- Magnetisation, measured raw against exact (t = 1..5):
  theta 0.4: 0.899 0.898 0.864 0.906 0.865 / 0.921 0.928 0.901 0.948 0.903;
  theta 0.8: 0.684 0.624 0.507 0.501 0.441 / 0.697 0.639 0.532 0.526 0.464;
  theta 1.0: 0.537 0.415 0.292 0.253 0.200 / 0.540 0.419 0.299 0.254 0.196.
  The largest raw miss (0.042, theta 0.4, t = 4-5) is the closest to the 0.05 line.
- theta = 0: M = 0.976-0.977 at every t (the readout floor, flat in depth: CZ on |0> adds almost nothing).
  theta = pi/2 (exact 0): |M| <= 0.007.
- Worst qubits at t = 5: 130 and 131 (theta 0.4: 0.60 and 0.47 against 0.92), the two ends of the coupler (130, 131)
  that IBM marks failed; the lattice uses both qubits through their other couplers.
- Scale against IBM's 2023 run: 151 qubits and 815 CZ at t = 5 here, without mitigation; IBM: 127 qubits, up to 20
  steps, zero-noise extrapolation. The depths here are those whose answers are exact by causal cones of at most 19
  qubits; t = 6-8 (cones up to 31-55 qubits) and t = 20 come next.
