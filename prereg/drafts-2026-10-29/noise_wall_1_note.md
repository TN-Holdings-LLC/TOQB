# Noise wall, stage 1 (DRAFT r2 by the workplace, 2026-10-29; owner's go pending): probe P1 (the weight-2 conserved charge) and probe P2 (<X_0>) of the kicked-Ising ring on ibm_kingston, n = 20 and 36, three map-free arms, device only. To be fixed by SHA-256 and CET time before the fetch

**Why.** Design: the workplace's r2 (`noise_wall_test_design_r2_2026-10-29.md`), reviewed at home. Two device points of
the kicked-Ising ring (D3 at L = 24, D4 at L = 100, n = 20) are both described by one uniform depolarizing rate,
p_eff = 0.00509 (0.00475-0.00548) and 0.00507 (0.00407-0.00696), recomputed at home with the actual inputs. This is a
post-hoc fit on one device and one day.

Stage 1 tests two things before any larger size:

- **P1.** Does a local probe follow that one number, unchanged from n = 20 to 36?
- **P2.** Do the spreading outputs agree with it?

**What is claimed, and what is not new.**

- **The claim is limited to two things:**
  - an effective error read from a conserved quantity of this circuit itself, without calibration data;
  - a test of whether it is independent of n.
- **Prior work.**
  - Reading noise from conserved quantities: Maruyoshi et al. 2023 (arXiv:2208.00576); Oliva del Moral et al. 2026
    (arXiv:2603.13060).
  - Depth limits and size-independent layer errors: McKay et al. 2023, layer fidelity and EPLG (arXiv:2311.05933).
  - The exact solution of noisy free fermions, of which our recursion is a special case: Pocklington and Clerk
    (arXiv:2604.18996).
  - The circuit type itself (J = π/4 kicked Ising, free fermions at zero longitudinal field) has run on IBM devices:
    Fischer et al. (arXiv:2411.00765). It is not claimed as a new check circuit.

## Arms (owner's decision; template mode; no arm reads a quality number)

| arm | placement |
|---|---|
| A | `fold:rule` |
| B | `fold:zipcyc` |
| D | `qiskit:2:blind:template`: level 2, `seed_transpiler = 0`; working couplers and basis only |

- Map-aware Qiskit is not in stage 1.
- **If an arm cannot be placed on the day's map,** that is recorded and nothing replaces it.
- **Sizes and the 2026-10-24 map.** n = 20 and 36 (owner's decision; n = 40 dropped, because `fold.shapes` finds cycles
  only up to 36 there, while a real 40-cycle exists).

| L = 16, 10/24 map | n = 36: two-qubit gates per layer | n = 36: duration |
|---|---|---|
| rule (bare ring) | 36 | 6.1 µs |
| zipcyc | 86 | 11.5 µs |
| blind Qiskit | 36 | 43.5 µs |

## Workload

The kicked-Ising ring, J = π/4, h = 0.6 (`toqb.kising`; one step S = (RX(2h) Z)^n CZ_ring), at n = 20 and 36 as placed on
the day's calibration.

### P1 (`toqb.kising_charge`)

**Step 1, the readout reference (done for every record).** The four inputs are prepared with X gates only, on the
physical qubits that record's circuit measures, and read in Z.

- **Why.** The folded schedules and Qiskit read a logical qubit on a physical qubit that depends on L (checked at n = 8
  for all three arms). A separate L = 0 circuit would not cancel readout.

**Charge.** Q = Σ_j (Z_j Z_{j+1} + b Y_j Z_{j+1} + c Z_j Y_{j+1}), with **b = c = −1.2860758110631627**.

- **Choice of the combination.** It is the combination, in the two-dimensional space of weight-2 conserved charges at
  h = 0.6, with the largest ZZ share (0.232). This is a noiseless criterion only.
- **Checks.**
  - Commutes with S and with the model layer, 2e-15 at n = 6 and 8.
  - The same coefficients at n = 6 to 40 (1e-14); the run script re-checks n = 20 and 36.

**Circuits.**

- All L steps.
- Inputs |0…0⟩, |1…1⟩, Néel, anti-Néel.
- Settings: all Z; Y on even and Z on odd qubits; the reverse.
- L = 24, 50, 100.
- Noiseless ⟨Q⟩ = Σ_j z_j z_{j+1}, exact and the same at every L.
- 16 circuits per record (12 + 4 references).

### P2 (`toqb.lam_device build --kind kising --twin none`)

- Model 0 (seed 0).
- 64 X-basis inputs.
- L = 24 and 50.

## Jobs and time (owner's decision: two jobs)

| job | content | shots | circuits | TOQB time model |
|---|---|---|---|---|
| job 1 | P1 | 1,000 | 288 (6 placements × 3 L × 16) | 91.1 s; `--max-seconds 120` |
| job 2 | P2 | 250 | 768 (6 placements × 2 L × 64) | 82.5 s; `--max-seconds 120` |

- **Track record of the model.** Billed time so far has been 0.72-0.95 times the model (D1-D3, D4, D5 part A, D6). It
  has never exceeded the model, deep circuits included.
- **P1's shot-noise SE.** `kising_charge.se_model`, approximate; the score uses the measured shot variances.

  | | n = 20 | n = 36 |
  |---|---|---|
  | SE | 0.0074-0.0078 | 0.0055-0.0058 |

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
2. **P1 n-independence.** For arm A at each L, |ρ(n = 36) − ρ(n = 20)| ≤ 2 SE: SAME, else DIFFERENT.
3. **P2.** `kising_formula`'s rule, using the formula slope at the declared p = 0.0051:
   - SE from the p range 0.00475-0.00548;
   - AGREE if |λ_device − λ_formula| ≤ 2 √(SE_device² + SE_formula²), else BELOW or ABOVE.
4. **Arms, per n and L.** WIN, LOSS or TIE at 2 SE on ρ (P1) and on λ (P2), A against B and A against D, as D6.

## Predictions

These come from the post-hoc p_eff = 0.0051, with range 0.00475-0.00548.

**P1, arm A, the same at n = 20 and 36.**

| L | ρ | range |
|---|---|---|
| 24 | 0.721 | 0.703-0.737 |
| 50 | 0.505 | 0.480-0.530 |
| 100 | 0.256 | 0.231-0.281 |

**P2, the formula slope at p = 0.0051** (actual inputs; the same for every arm, since it is a property of the logical
circuit).

| n | L | λ | range |
|---|---|---|---|
| 20 | 24 | 0.185 | 0.164-0.207 |
| 20 | 50 | 0.069 | 0.060-0.079 |
| 36 | 24 | 0.190 | 0.177-0.204 |
| 36 | 50 | 0.047 | 0.043-0.050 |

- **Prediction for arm A:** AGREE in all four cells.
- **Expected device SE at 250 shots:**

  | | L = 24 | L = 50 |
  |---|---|---|
  | n = 20 | about 0.02 | about 0.05 |
  | n = 36 | about 0.05 | about 0.04 |

  The L = 50 cells therefore decide only coarsely.

**Arms (expectations, not rules).**

- **A against B: WIN at both n.** The zipper uses 2.3-2.4 times the two-qubit gates and about twice the duration.
- **A against D: WIN at both n.** Blind Qiskit finds the same bare ring at both n (equal gate counts), with about 5-10
  times the duration. If the WIN appears, it comes from duration, not from gate count.

**Reference only (owner's decision).** The P2 slope predicted at P1's own p_eff (arm A, n = 20, L = 50) is reported, not
judged.

## Limits

- **Relaxation.** The four-input ratio leaves a second-order bias: +0.005 at L = 30 for γ = 0.004 per step in the n = 6
  model; it grows with γ.
- **Noise model.** p_eff assumes uniform Pauli noise. P1 sees only weight-2 damping; P2 is the check on spreading.
- **Readout.** It cancels only within a record, where the reference and the circuit share the measured qubits.
- **Arm D across L.** Qiskit's qubits may differ between its L cells.
- **Scope.** One device, one day, h = 0.6, n = 20 and 36.
- **Classical hardness.** Every reference is classically solvable; no classical-hardness claim is made.
