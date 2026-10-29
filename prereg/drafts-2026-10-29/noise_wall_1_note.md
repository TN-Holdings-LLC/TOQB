# Noise wall, stage 1 (DRAFT by the workplace, 2026-10-29; owner's go pending): probe P1 (the weight-2 conserved charge) and probe P2 (<X_0>) of the kicked-Ising ring on ibm_kingston, n = 20 and 40, three map-free arms, device only. To be fixed by SHA-256 and CET time before the fetch

**Why.** Design: the workplace's r2 (`noise_wall_test_design_r2_2026-10-29.md`), reviewed at home. Two device points of
the kicked-Ising ring (D3 at L = 24, D4 at L = 100, n = 20) are both described by one uniform depolarizing rate,
p_eff = 0.00509 (0.00475-0.00548) and 0.00507 (0.00407-0.00696), recomputed at home with the actual inputs. This is a
post-hoc fit on one device and one day.

Stage 1 tests two things before any larger size:

- **P1.** Does a local probe follow that one number, unchanged from n = 20 to 40?
- **P2.** Do the spreading outputs agree with it?

## Arms (template mode; no arm reads a quality number)

| arm | placement |
|---|---|
| A | `fold:rule` |
| B | `fold:zipcyc`, where a cycle of n qubits exists. On the 2026-10-24 map it is refused at n = 40 ("no cycle of >= 40 qubits"); a refusal is recorded, not replaced. |
| D | `qiskit:2:blind:template`: level 2, `seed_transpiler = 0`; working couplers and basis only |

Map-aware Qiskit (arm C) is not in stage 1.

## Workload

The kicked-Ising ring, J = π/4, h = 0.6 (`toqb.kising`; one step S = (RX(2h) Z)^n CZ_ring). n = 20 and 40, as placed on
the day's calibration (home checks).

### P1, `toqb.kising_charge`

**Charge.** Q = Σ_j (Z_j Z_{j+1} + b Y_j Z_{j+1} + c Z_j Y_{j+1}), with **b = c = −1.2860758110631627**.

- **Choice of the combination.** It is the combination, in the two-dimensional space of weight-2 conserved charges at
  h = 0.6, with the largest ZZ share (0.232). This is a noiseless criterion only.
- **Checks.**
  - Commutes with S and with the model layer (A†QA), 1e-10 at n = 6 and 8.
  - The same coefficients at n = 6, 8, 10 and 20; the run script re-checks n = 20 and 40.

**Circuits.**

- All L steps.
- Inputs |0…0⟩, |1…1⟩, Néel, anti-Néel.
- Settings: all Z; Y on even and Z on odd qubits; the reverse.
- L = 24, 50, 100.
- Noiseless ⟨Q⟩ = Σ_j z_j z_{j+1}, exact and the same at every L.

**Readout reference.** Each (n, L, arm) record has its own: the four inputs prepared by X gates on the physical qubits
that record measures, read in Z.

- **Deviation from r2's single L = 0, and why.** The folded schedules and Qiskit read a logical qubit on a physical
  qubit that depends on L (checked at n = 8 for all three arms). A separate L = 0 circuit would not cancel readout.
- **Count.** 16 circuits per record (12 + 4).

### P2, `toqb.lam_device build --kind kising --twin none`

- Model 0 (seed 0).
- 64 X-basis inputs.
- L = 24 and 50.

## Jobs and time

There are two jobs, since a job has one shot count.

| job | content | shots | circuits | TOQB time model |
|---|---|---|---|---|
| job 1 | P1 | 1,000 | 240 (5 placements: 3 at n = 20, 2 at n = 40; × 3 L × 16) | about 76 s; `--max-seconds 120` |
| job 2 | P2 | 250 | 640 (5 placements × 2 L × 64) | about 69 s; `--max-seconds 120` |

**Caution on the time.** D4 (L = 100, 2,000 two-qubit gates) was billed 38 s, against about 10 s by the model.

- **D3/D4-based scenario.** An extra per-circuit cost of about 0.48 s × (two-qubit gates / 2,000)² gives about 240 s
  for job 1 and 220 s for job 2, about 8 minutes in total. This is a rough upper scenario, not a measurement.
- **Owner's alternative.** One job with everything at 250 shots: model 94 s, scenario about 410 s. P1's SE then
  doubles (table below).

**P1's shot-noise SE.** `kising_charge.se_model`, approximate; the score uses the measured shot variances.

| | n = 20 | n = 40 |
|---|---|---|
| 1,000 shots | 0.0074-0.0078 | 0.0052-0.0055 |
| 250 shots | 0.015 | 0.011 |

## Measures

**P1, per (n, L, arm).**

- **Four-input ratio:**

      ρ(L) = [Q(0..0) + Q(1..1) − Q(Néel) − Q(anti-Néel)]_L / [same]_reference

- SE by the delta method, from the shot variances.
- p_eff = 3(1 − √r)/4, with r = ρ^(1/L).
- **Also reported:** the |0…0⟩-only ratio, as the relaxation diagnostic.

**P2.** The device slope λ against the exact free-fermion z, as in D3/D4.

## Rules

1. **P1 against the prediction.** The predicted ρ is inside the measured ρ ± 2 SE, for arm A at each n and L.
2. **P1 n-independence.** For arm A at each L, |ρ(n = 40) − ρ(n = 20)| ≤ 2 SE: SAME, else DIFFERENT.
3. **P2.** `kising_formula`'s rule (AGREE, BELOW or ABOVE), using the formula slope at the declared p, with SE from
   its range.
4. **Arms, per n and L.** WIN, LOSS or TIE at 2 SE on ρ (P1) and on λ (P2), A against B and A against D, as D6.

## Predictions

These are made from the post-hoc p_eff = 0.0051 (range 0.00475-0.00548).

**P1, arm A, the same at n = 20 and 40.**

| L | predicted ρ |
|---|---|
| 24 | 0.721 |
| 50 | 0.505 |
| 100 | 0.256 |

**P2, arm A.** AGREE at n = 20 and 40.

**Arms (expectations, not rules).**

- **A against B at n = 20: WIN.** The zipper uses 2.3 times the two-qubit gates (46 against 20 per layer) and 2.3 times
  the duration.
- **A against D: WIN at both n.**
  - On the 2026-10-24 map, blind Qiskit finds a ring with as many or fewer two-qubit gates: 20 per layer at n = 20;
    40 per layer at n = 40, against the rule's 44.
  - Its duration is 6.4 times the rule's at n = 20 (150 against 23 µs at L = 100) and 6.3 times at n = 40 (286
    against 45 µs).
  - If the WIN appears, it comes from duration, not from gate count.

**Choice of p for P2 (owner).**

- **Primary:** the declared 0.0051, a true prediction for every cell.
- **Secondary, reported:** p from P1 (arm A, n = 20, L = 50). It tests whether P1 and P2 are consistent on the day.

## Limits

- **Relaxation.** The four-input ratio leaves a second-order bias: +0.005 at L = 30 for γ = 0.004 per step in the n = 6
  model; it grows with γ.
- **Noise model.** p_eff assumes uniform Pauli noise. P1 sees only weight-2 damping; P2 is the check on spreading.
- **Readout.** It cancels only to the extent that the matched reference and the circuit share the measured qubits and
  their readout. They do, by construction, within a record.
- **Arm D across L.** Qiskit's qubits differ between its L cells, so its ρ at different L are not on the same qubits.
- **Scope.** One device, one day, h = 0.6, n = 20 and 40.
- **Classical hardness.** Every reference is classically solvable; no classical-hardness claim is made.
