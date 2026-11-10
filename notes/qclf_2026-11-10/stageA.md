# Classifier follow-up to paper 3, stage A: inventory of the 2026-10-30 kingston run (home, 2026-11-10)

For the workplace's blueprint of 2026-11-10 (quantum classifier compared raw, answers sealed). Read from the committed
records only; nothing run. Corrections to the blueprint are marked **Correction**.

## 1. Where the records are

**Correction:** they are in TOQB, not in psf-zero.

| what | where |
|---|---|
| declaration | `prereg/drafts-2026-10-30/qelm_A_note.md` (SHA-256 8c26afd7..., fixed 03:30:50 CET, `FIXED.md`) |
| addendum (kingston only) | `prereg/drafts-2026-10-30/qelm_A_addendum1.md` (fixed 08:45 CET) |
| task and noiseless features | `results/qelm-A-2026-10-30/noiseless.json` (32a6d656...b38d) |
| bands | `results/qelm-A-2026-10-30/predict_kingston.json` |
| code | `toqb/qelm.py` (task, predict, depth formula), `toqb/qelm_device.py` (build one job per arm, score) |
| device run | `results/device-2026-10-30/qelmA/kingston/` (jobs per arm, `score.txt`, `times.txt`) |

## 2. The 10-30 design

| item | value |
|---|---|
| circuit | ring, n = 20; per layer RY(pi/2 x_q), RZ(pi/2 x_q) on every qubit, then CZ on every ring edge |
| depth | L = 19, by formula from the arms' decay lengths (not by simulation) |
| features | <X_q>, <Y_q>, <Z_q>: 60 per input, 3 circuits per input |
| classifier | least squares with intercept to +-1, sign; 61 weights; no training of the circuit |
| data | synthetic: x uniform in [-1, 1]^20; random teacher w on the centred noiseless features; margin cut; 128 train, 200 test; class share 0.508 / 0.510 |
| arms | fold:rule (20 CZ per layer, 380 CZ), fold:zipcyc (46 per layer, 874 CZ), qiskit:2:blind:template (380 CZ) |
| shots | 250; 16 / 32 / 64 / 125 subsampled from the same counts |
| bands | lambda_arm = exp(-19 / L*_arm), L* from the **noise wall's own device records of 10-29** (charge decay), read with binomial shots; mean and central 99 % of 400 draws |
| rules | G (native compile) gate; Q1 model a_j + lambda_j f0_j, chi2/dof median <= 2; Q2 accuracy at S 250 inside band; Q3a rule > zipcyc, one-sided McNemar at S 64 and 250, Holm; Q3b rule vs Qiskit reported, not judged; R baselines |
| time (model) | 984 circuits per arm, 104.8 s per arm |

## 3. Result (kingston, 10-30 11:56-12:03 CET)

| arm | lambda X / Y / Z | acc S 64 | acc S 250 | band (S 250) | Q1 |
|---|---|---|---|---|---|
| fold:rule | 0.703 / 0.656 / 0.878 | 0.740 | 0.810 | 0.745-0.900 INSIDE | FAILS (chi2 2.87) |
| fold:zipcyc | 0.349 / 0.377 / 0.683 | 0.650 | 0.715 | 0.690-0.845 INSIDE | HOLDS (1.73) |
| qiskit blind | 0.567 / 0.488 / 0.806 | 0.695 | 0.750 | 0.680-0.855 INSIDE | FAILS (3.45) |

Ceiling 0.840, raw x 0.555, majority 0.510. Q3a rule vs zipcyc: S 64 p 0.025, S 250 p 0.0072, both pass Holm.
Q3b rule vs Qiskit: p 0.18 / 0.067 (not judged). The stand-in (pod) had put Q3a on the other side (p 0.080).

**Correction:** the 0.810 against 0.715 is rule against zipcyc (two formula placements whose signal differs by about
2x), not rule against Qiskit.

## 4. The four confounds in the 10-30 design

| confound | 10-30 |
|---|---|
| answer at the starting point | removed by design: no trained circuit, one least-squares solve |
| readout bias | removed by design: least squares with intercept is invariant to per-feature affine maps, so offsets and scales are absorbed |
| shot weakness from shrinking outputs | tested: S_eff = lambda^2 S; subsampled S; Q3a |
| model right in shape, wrong in scale | tested: Q1 (shape) and Q2 (bands) |

## 5. Mismatches with the psf-os flow

1. **Bands.** **Correction:** the bands did not use IBM calibration or a twin; they came from L* measured on the device
   the day before (own records). That is inside "no map". The stand-in rehearsal used a calibration model, but it was
   reported, not judged. Open: whether a new run takes L* from the previous day's own records again (needs those
   records per device), or reports the bands beside only.
2. **Arms.** The comparison that carried paper 3 is rule against zipcyc. A SABRE arm (blueprint) does not repeat it,
   and comparing with search is settled (owner). Open for the owner.
3. **Time.** 104.8 s per arm by the model; two arms about 210 s. The blueprint's 60 s per job does not hold without
   fewer points or shots (each test point costs 0.31 s per arm).
4. **Size.** n = 20, L = 19 (the blueprint's 10 qubits / 16 layers is not the 10-30 circuit). Statevector at 20 qubits
   runs on a CPU.
5. **Controls.** The 10-30 jobs had the gate G but not psf-os's floor, mirror and sentinel. Through psf-os they are
   added; how the ring is placed by psf-os rules (fold rule and zipcyc as psf-os layouts) is to be checked in stage B.
6. **Readout order.** The sealed answers are labels of test points, not per-qubit values, so per-label sealing is not
   needed; the feature-to-logical-qubit map must be recorded per arm (stage B).
