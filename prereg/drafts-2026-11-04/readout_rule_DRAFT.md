# DRAFT (not declared): the readout-check rule for P5, from the job's own theta = 0 circuit (workplace, 2026-11-04)

Status: draft written at the workplace for home and the owner. Nothing here is fixed; no device job is attached. The
numbers in the last section were computed after the fact on jobs already run and must not be read as a test.

**Why.** Stage E on ibm_fez (`results/kim-e-2026-11-03`) missed at theta 0.4 because of qubits whose readout is broken
while IBM marks nothing failed (23 reads <Z> = -0.79 at theta 0, 51 reads 0.23, 83 reads 0.68). P5's job already holds
a readout scan of every lattice qubit: the theta = 0 circuit (ideal <Z_q> = 1 at every depth), taken in the same job,
from the device's own counts. psf-os reads no calibration number; this rule keeps to that.

**The rule (R).** Before any theta != 0 cell is scored:
1. z0_q = mean over the job's theta = 0 depths of the measured <Z_q>, for every lattice qubit q.
2. floor = median of z0 over the lattice; sigma = 1.4826 x the median absolute deviation of z0 from the floor.
3. A qubit is **left out of scoring** if z0_q < floor - max(5 sigma, 0.05).
4. Scoring (READS, AGREES, magnetisation) then uses the kept qubits, for the measurement and for the exact answer
   alike. The circuit, the lattice and the job do not change: R acts on scoring only.

**Why these numbers (choices, stated as such).**
- The median and the MAD do not move when a few qubits are broken, so the line is set by the healthy majority.
- 5 sigma: for a Gaussian spread of healthy qubits, about 3e-7 one-sided per qubit, so fewer than 1e-4 false drops on
  150 qubits. Real spreads have tails; this number is a guide, not a guarantee.
- The 0.05 floor on the margin: no qubit is dropped for less than the declared magnetisation line (0.05), so on a
  very uniform device R drops nothing for small differences.
- Shot noise: with 4000 shots per depth and 3-8 depths, the standard error of z0_q is about 0.002-0.004, small
  against the margin.

**What R is not.** It is not a correction (dividing by z0_q would be readout mitigation, which P5 does not use). It
does not use IBM's readout numbers. It does not change which qubits the circuit acts on, so the dropped qubits still
take part in the dynamics; only their readings are not scored.

## Proposed judgement for a future job (to be fixed by home with the owner)

On the next P5 job (any device), score with and without R from the same counts:
- R **HELPS** if the mean squared error over answered qubits (theta 0.4, 0.8, 1.0 pooled) falls to at most 0.8 of the
  full lattice's; **NO EFFECT** between 0.8 and 1.25; **HURTS** at 1.25 or more (the suspect-rule thresholds of
  kim_cd_note.md).
- Reported with it: the dropped qubits, their z0, the line, and the price (number dropped).

## After the fact (reference only; R was written after fez's 23, 51 and 83 had been seen)

`notes/readout_rule_2026-11-04/readout_rule.py` -> `out/readout_rule_posthoc.json`. Max |dM| is over the depths
answered in that job; MSE pools them.

| job | qubits | floor, sigma, line | dropped by R | theta 0.4 max \|dM\| | 0.8 | 1.0 | MSE ratio (0.4 / 0.8 / 1.0) |
|---|---|---|---|---|---|---|---|
| fez X (stage E, t 1-8) | 153 | 0.988, 0.013, 0.924 | 16 (23: -0.80, 51: 0.21, 83: 0.70, 13 between 0.85 and 0.93) | 0.079 -> 0.049 | 0.044 -> 0.024 | 0.012 -> 0.014 | 0.13 / 0.13 / 0.11 |
| kingston K (stage E, suspect lattice, t 6-8) | 125 | 0.986, 0.014, 0.915 | 4 (72: 0.51, 7: 0.86, 51: 0.90, 35: 0.91) | 0.031 -> 0.027 | 0.012 -> 0.012 | 0.007 -> 0.007 | 0.52 / 0.88 / 0.90 |
| kingston b (stage C, t 6-8) | 151 | 0.989, 0.012, 0.928 | 9 (138: 0.74, 119: 0.82, 43: 0.87, 6 between 0.91 and 0.93) | 0.053 -> 0.047 | 0.028 -> 0.023 | 0.010 -> 0.012 | 0.83 / 0.78 / 0.92 |

Read with care:
- The headline is fez theta 0.4, 0.079 -> 0.049 (inside the line). The essential numbers: R drops 16 of 153 qubits
  (10 %), not only the three broken ones, and the line sits at 0.924, so qubits a few percent below the floor go too;
  the new value 0.049 is 0.001 inside a line that was fixed for another purpose.
- Most of fez's MSE drop comes from qubit 23 alone (its reading is inverted: an error of about 1.6 on every theta-0.4
  value), so the MSE ratio overstates what R does for the other qubits; the magnetisation change is the better guide.
- On kingston R changes little (largest change 0.006) and drops 4 and 9 qubits.
- theta 1.0 gets slightly worse on two of the three jobs (+0.002): with M near 0.18 the readout scale matters little,
  and dropping qubits changes which qubits are averaged.
- Sensitivity (information only, k is not chosen from it): on fez k = 3 or 4 drops 18, k = 6 drops 15.
