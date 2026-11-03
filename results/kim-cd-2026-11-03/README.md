# P5 stages C and D and the suspect-qubit rule, 2026-11-03: the suspect rule HELPS (error x 0.56); stage C READS at all three theta and AGREES at 0.8 and 1.0, DIFFERS at 0.4 (t = 8: 0.053 against the 0.05 line); stage D controls AGREE and t = 20 is recorded without an exact answer

- **Declaration:** `prereg/drafts-2026-11-03/kim_cd_note.md` (SHA-256 a07dad9f...11175006), fixed 11:13 CET, TOQB 41032f9;
  psf-os 9f773ff.
- **Build:** fetch of 11:14:47 CET (calibration 09:16:01 CET, target b031eb0c...), e55e98a: 54 circuits, lattice b
  151 qubits / 163 edges, s 125 / 134. CPU answers sealed in e55e98a; stage C answers (RunPod H200, 11:26-12:06 CET,
  checks K1 2.1e-6, K2 3.6e-6, K3 0) sealed in 639ff1a (answers_C.json SHA-256 b11c30e8...00797c09).
- **Job:** dbks20gnceqs73amhpmg, sent with `psf-os submit` at 12:09:51 CET, queued until 13:57 CET (about 40 jobs
  ahead on ibm_kingston), DONE, 59 s billed. Scored by `gpu/kim_cd_score.py`: `scores.json`.

## Judged

1. **Sentinel:** CLEAN.
2. **Suspect-qubit rule (same job):** mean squared error of <Z_q>, t = 1..5, mean over theta: b 0.0021 (151 qubits),
   s 0.0012 (125 qubits), ratio 0.556: **HELPS** (theta 0.4: 0.0032 -> 0.0014; 0.8: 0.0018 -> 0.0012; 1.0: 0.0012 ->
   0.0009). The price: 26 qubits (11 suspect, 15 cut off from the largest part).
3. **Stage C (answered qubits, t = 6, 7, 8):**

| theta | MSE (half the answer's mean square) | M measured / exact at t = 6, 7, 8 (answered qubits: 151, 122, 82) | verdict |
|---|---|---|---|
| 0.4 | 0.0058 (0.4031): READS | 0.867 / 0.904, 0.848 / 0.887, 0.849 / 0.902 | **DIFFERS** (largest miss 0.053 at t = 8) |
| 0.8 | 0.0027 (0.1078): READS | 0.427 / 0.441, 0.429 / 0.454, 0.441 / 0.469 | **AGREES** (0.028) |
| 1.0 | 0.0013 (0.0219): READS | 0.181 / 0.171, 0.178 / 0.179, 0.183 / 0.184 | **AGREES** (0.010) |

   The sentence fixed for READS and AGREES at all three theta does not hold: theta 0.4 misses by 0.003 beyond the line
   at t = 8 (and is within it at t = 6 and 7).
4. **Stage D controls (t = 20, 3,260 CZ):** theta 0: M 0.979 (exact 1): **AGREES**; theta pi/2: 0.001 (exact 0):
   **AGREES**.

## Reported, not judged

- **t = 20, no exact answer** (all 151 qubits, shot-noise SE 0.001): theta 0.4: M = 0.819; 0.8: 0.253; 1.0: 0.050.
  For comparison, all qubits at t = 6, 7, 8: 0.867, 0.843, 0.852 / 0.427, 0.421, 0.415 / 0.181, 0.168, 0.151.
- The theta-0.4 miss is a downward bias that grows slowly with depth (0.037, 0.039, 0.053). The readout floor
  (theta 0: 0.977 at every depth) accounts for about 0.02 of it.
- At t = 7 and 8 only qubits with causal cones of at most 33 qubits are answered; they lie towards the lattice's edges.
- Controls at t = 6-8: theta 0: 0.977; theta pi/2: 0.001-0.006.
