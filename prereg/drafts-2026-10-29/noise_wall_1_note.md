# Noise wall, stage 1 (r3, FIXED 2026-10-29 11:13 CET on the owner's go: the workplace's r2 plus the readable depth L* and Delta L added at home; rule 6 judged, owner's decision): probe P1 (the weight-2 conserved charge) and probe P2 (<X_0>) of the kicked-Ising ring on ibm_kingston, n = 20 and 36, three map-free arms, device only.

**Run order (owner, 2026-10-29).** The second device, ibm_marrakesh (`noise_wall_1_second_device_note.md`, fixed at the same time), is run first because its queue is empty; this device (ibm_kingston, 122 pending jobs at 11:08 CET) follows. Both declarations are fixed before either device is fetched, so neither device's result is seen before the other's predictions are fixed.

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

**Readable depth, per (n, arm)** (added in r3, owner's request 2026-10-29: the wall reported as a depth).

- **L\*.** The decay length (the 1/e depth) of the four-input ratio: a one-parameter fit ρ(L) = exp(−L/L\*) over
  L = 24, 50, 100, weighted least squares on the ρ scale (weights 1/SE²; ρ ≤ 0 points kept). ρ(0) = 1 by construction
  (each record's own readout reference), so there is no amplitude parameter. SE from the curvature of the fit.
  `kising_charge.decay_length`.
- **Why the 1/e depth.** It needs no shot budget and no threshold, and it lies inside the measured range (about 73
  layers at p = 0.0051, against L = 24-100). A depth "readable at S shots" follows from it by extrapolation and is
  reported only.
- **Against the rule (arm A), for X = B, D at the same n:** ΔL_X = L\*_A − L\*_X and κ_X = L\*_A / L\*_X (the ratio
  of per-step decay rates), SE by the delta method.
- **Structure ratios, from the records only (no error rate read).** g_X = ΣG_X / ΣG_A (two-qubit gates) and
  t_X = ΣT_X / ΣT_A (scheduled duration), summed over the common L cells.
- **Structure model.** κ = (1 − φ) g + φ t, where φ in [0, 1] is the share of the rule's decay that scales with
  duration rather than with gate count. φ_X = (κ_X − g_X) / (t_X − g_X), reported where |t − g| > 0.2.
- **What this is not.** L\* is the decay length of a weight-2 quantity. A wider observable decays faster (P2: λ ≈ 0.19
  at L = 24 where ρ ≈ 0.72). L\* measures the per-step error of the placement, not the depth at which an arbitrary
  output stays readable.

## Rules

1. **P1 against the prediction.** The predicted ρ is inside the measured ρ ± 2 SE, for arm A at each n and L.
2. **P1 n-independence.** For arm A at each L, |ρ(n = 36) − ρ(n = 20)| ≤ 2 SE: SAME, else DIFFERENT.
3. **P2.** `kising_formula`'s rule, using the formula slope at the declared p = 0.0051:
   - SE from the p range 0.00475-0.00548;
   - AGREE if |λ_device − λ_formula| ≤ 2 √(SE_device² + SE_formula²), else BELOW or ABOVE.
4. **Arms, per n and L.** WIN, LOSS or TIE at 2 SE on ρ (P1) and on λ (P2), A against B and A against D, as D6.
5. **L\* of arm A against the prediction.** INSIDE if |L\*_A − L\*_pred| ≤ 2 √(SE² + SE_pred²), SE_pred half the
   spread over the p range; else BELOW or ABOVE. (This is rule 1 written as a depth; it adds no independent test.)
6. **Arm B against its structure bracket (no free parameter).** κ_B inside [min(g_B, t_B) − 2 SE, max(g_B, t_B) + 2 SE]:
   INSIDE, else BELOW (the zipper loses less than its structure says) or ABOVE (more).
7. **Arm D, n-consistency of φ.** |φ_D(n = 36) − φ_D(n = 20)| ≤ 2 SE: SAME, else DIFFERENT. (Arm D has g = 1, so κ_D
   measures φ directly; this asks whether one φ describes the device at both sizes.)

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

**Readable depth** (r3; g and t from a home rehearsal build on the stored 2026-10-24 kingston map, summed over
L = 24, 50, 100; the run uses the day's build).

| | n = 20 | n = 36 |
|---|---|---|
| L\*_A, predicted (rule 5) | 73.3 (68.2-78.7) | 73.3 (68.2-78.7) |
| B: g, t | 2.30, 2.24 | 2.39, 2.22 |
| B: κ bracket (rule 6) | 2.24-2.30 | 2.22-2.39 |
| B: L\*, ΔL | 31.9-32.6, 40.6-41.4 | 30.7-33.0, 40.3-42.6 |
| D: g, t | 1.00, 6.04 | 1.00, 9.38 |

- **Prediction for rules 5-7:** INSIDE, INSIDE, SAME.
- **Rule 6 is a sharp test** (the bracket is narrow, because the zipper's gate and duration ratios nearly coincide).
  It is not a safe one: on D6 (classifier, L = 16) the zipper's loss against the rule scattered on both sides of its
  gate ratio.
- **Arm D, expectation only:** φ ≈ 0.8 (D6 at n = 20, post-hoc: κ = ln 0.49 / ln 0.83 = 3.8 at t = 4.6; plausible
  range 0.2-1.0). Then L\*_D ≈ 15 at n = 20 and ≈ 10 at n = 36, ΔL ≈ 59 and 64.

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
- **Readable depth.** The one-parameter exponential ignores the relaxation bias and any non-exponential decay; with
  three depths it cannot test the exponential form. The structure model has two terms only (gates and duration);
  single-qubit gates, crosstalk and per-coupler differences are not in it.
- **Scope.** One device, one day, h = 0.6, n = 20 and 36.
- **Classical hardness.** Every reference is classically solvable; no classical-hardness claim is made.
