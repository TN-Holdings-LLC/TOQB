# Noise wall, stage 1, second device (r2, FIXED 2026-10-29 11:13 CET on the owner's go: the workplace's draft plus the readable depth carried over, added at home): the same test as the first device's declaration (noise_wall_1_note.md r3, SHA-256 7415beca7ee87eb33ba9d378841d9ecd2c885910735a10f34d82078786e74f3c) on ibm_marrakesh (the owner's choice, 2026-10-29: the emptiest queue), with predictions carried over from structure only. Run first (owner: emptiest queue first); ibm_kingston follows under the first declaration. Both fixed before either fetch

**Why.** One device on one day cannot tell a property of the method from a property of the machine.

- **The second device is a machine of the same generation.** The three Open Plan devices (kingston, fez, marrakesh)
  appear to be Heron r2; home checks.
- **The predictions are fixed before the first device's results are seen.** Then the second device tests them; it
  does not fit them.
- **Report.** Both devices' results are reported side by side. A prediction that fails on either device is reported
  as failed.
- **What is not claimed.** No product of p values is claimed. The statement is only: "the declared predictions did, or
  did not, fail on each of two independent devices".

## Identical to the first device's declaration

- **Circuits, arms and sizes.** The kicked-Ising ring (J = π/4, h = 0.6).
  - Arms: rule, zipcyc and `qiskit:2:blind:template`; no quality number read; map-aware Qiskit not included.
  - n = 20 and 36.
  - An arm that cannot be placed on the day's map is recorded and not replaced.
- **P1.** The charge Q with b = c = −1.2860758110631627.
  - Four inputs × three settings, L = 24, 50, 100.
  - Readout reference per record (step 1).
- **P2.** 64 inputs, L = 24 and 50.
- **Jobs.** Job 1: P1, 288 circuits × 1,000 shots. Job 2: P2, 768 circuits × 250 shots. `--max-seconds 120` each.
- **Run.** `gpu/noise_wall_1.sh` with `NOTE=prereg/drafts-2026-10-29/noise_wall_1_second_device_note.md DEVICE=ibm_marrakesh`.
  The fetch must be of ibm_marrakesh; the script checks it.

## Device-dependent numbers

**Time model.** The same for both devices: 91.1 s + 82.5 s, about 3 minutes per device (about 6 minutes for both;
"about 10 minutes" kept as a margin).

### ibm_marrakesh (the device of this declaration)

Its 2026-10-13 published calibration (`snapshot:marrakesh`) was checked at home and at the workplace. Every arm
places at both n.

| arm | n = 20: gates per layer | n = 20: duration L = 24 / 100 | n = 36: gates per layer | n = 36: duration L = 24 / 100 |
|---|---|---|---|---|
| rule | 20 | 8.1 / 25.2 µs | 36 | 8.3 / 26.0 µs |
| zipcyc | 46 | 16.4 / 59.6 µs | 86 | 16.7 / 60.8 µs |
| blind Qiskit | 20 | 38.3 / 150.8 µs | 36 | 65.1 / 262.4 µs |

The day's map is checked again before the build.

### ibm_fez (not chosen; kept for the record)

Home checks on the day's map.

**Caution.** On `FakeFez` (an old published snapshot, not today's map), n = 20 places for every arm (20 / 46 / 20 gates
per layer). At n = 36, however:

- rule refuses ("the zipper has the fewest extra gates");
- zipcyc refuses ("no cycle of >= 36 qubits");
- only blind Qiskit places (36 per layer).

If the day's map behaves the same, predictions 1 (at n = 36), 2 and the n = 36 arm comparisons cannot be judged on fez.
They would be recorded as NOT RUN. That is a reason to prefer marrakesh, unless fez's day map places n = 36.

## Predictions carried over (fixed now)

1. **P1, one p from the device's own reference.**
   - **How p is fixed.** p is fixed by this device's rule cell at n = 20, L = 24 alone: p = 3(1 − √r)/4 with
     r = ρ^(1/24). Its range comes from ρ ∓ SE.
   - **What it predicts.** The rule's ρ at n = 20, L = 50 and 100, and at n = 36, L = 24, 50 and 100:
     ρ_pred = (1 − 4p/3)^(2L).
   - **Rule.** INSIDE if |ρ − ρ_pred| ≤ 2 √(SE² + SE_pred²), where SE_pred is half the spread of ρ_pred over the p
     range (as `kising_formula`). `kising_charge score --self-ref-n 20 --self-ref-L 24`.
   - **Scale, if the device were like kingston on 10/28** (ρ(24) ≈ 0.72 ± 0.008): p range about 0.0049-0.0053, and
     SE_pred about 0.011 at L = 50 and 100.
2. **P1, n-independence.** For the rule at each L, |ρ(n = 36) − ρ(n = 20)| ≤ 2 SE: SAME, else DIFFERENT.
3. **P2.** The device slope λ against the formula slope at prediction 1's p (with its range), by
   `kising_formula`'s rule: AGREE, else BELOW or ABOVE. Predicted: AGREE in all four cells.
4. **Arms.** The signs of rule − zipcyc and rule − blind Qiskit, on ρ (P1) and λ (P2), by D6's rule (WIN, LOSS or TIE at
   2 SE). Predicted: WIN against both at both n, as on the first device.

5. **Readable depth** (r2, as rules 5-7 of the first declaration).
   - L\*_A against L\*_pred = −1 / (2 ln(1 − 4p/3)) at prediction 1's p (with its range): INSIDE, else BELOW or ABOVE.
   - Arm B: κ_B inside its structure bracket [min(g, t), max(g, t)] ± 2 SE, with g and t from this device's own
     build. This rule has no free parameter, so it carries over unchanged. Predicted: INSIDE. (marrakesh 10/13, from
     the table above: g = 2.30, t = 2.02-2.37 at n = 20.)
   - Arm D: φ_D the same at n = 20 and 36 (2 SE): SAME. The value of φ is not carried over.

## Not carried over (measured anew on each device)

- **The value of p_eff.**
- **The wall depth that follows from it** (L\* and ΔL themselves; only rule 5's form and the bracket carry over).
- **The value of φ.**

## Limits

The same as the first device's declaration:

- the second-order relaxation bias;
- the uniform Pauli assumption;
- readout cancelled within a record only;
- Qiskit's qubits may differ between its L cells;
- one day per device.

Two devices of the same generation say nothing about other architectures.
