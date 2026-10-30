# Test 2: does the rule's lead survive a non-integrable ring? The mirror (echo) of the kicked-Ising ring with a longitudinal field hz (DRAFT by the workplace, 2026-10-30 00:57 CET; owner's confirmation pending; to be fixed by SHA-256 and CET time before any device run)

**Why.** The reviewer's objection "this is because the ring is integrable (free fermions)".

- hz = 0 is the free-fermion step of noise wall stage 1.
- hz = 0.1 is weakly non-integrable, hz = 0.3 strongly.
- **What is judged:** whether fold:rule still beats fold:zipcyc and map-free Qiskit, and whether zipcyc's κ moves with
  hz.
- **What it is not:** a test of quantum advantage.

**Order.** Twin (pod, n = 20, rule and zipcyc), then the device (home, all arms, n = 20 and 36).

## Circuit (toqb/kising_echo.py)

**The step.** S = (RX(2h) Z RZ(2 hz))^{⊗n} CZ_ring, with h = 0.6 (as stage 1).

- RZ(2 hz) commutes with the CZ ring and only shifts one Euler angle.
- So the two-qubit structure is the same at every hz, and a placement comparison sees only the change of integrability.

**The mirror.** L steps of S, a flip W = X^{⊗n}, then L steps of S'^{-1} with S' = W S W.

- U = S'^{-L} W S^L = W exactly, at any n and hz: the noiseless output is the input with every bit flipped.
- One-way L ∈ {12, 25, 50}, full depth D = 2L ∈ {24, 50, 100}.

**Change from home's instruction (for confirmation).** The instruction put a barrier at the turn; this draft puts the
flip W there.

- **Why the barrier does not work here.** TOQB's ring parser (`fold.read_ring`) drops barriers, and the single-qubit
  gates between two CZ rings are merged. Without W the turn's block merges to a diagonal, and CZ·RZ·CZ can cancel.
- **What W changes.** With W, the turn's merged block contains X, which does not commute with CZ.
- **What stays as instructed:** the acceptance rule, the inputs, the reading and the grid.

**Acceptance (from the instruction).** Every compiled echo circuit has exactly 2L × the arm's two-qubit gates for one
ring layer (`kising_echo.per_layer_q2`); otherwise the record is invalid and not replaced.

- Checked on FakeMarrakesh at n = 12: rule 24 → 2L × 12, zipcyc 2L × 26, blind Qiskit 2L × 12; noiseless return
  exact.
- The rule only means something when the arm places the ring without routing. At n = 8, holes or SWAP routing make
  layers differ, and a one-layer compile is not a per-layer count. At n = 20 and 36 on marrakesh and kingston every arm
  placed the ring natively on 10/29.

## Reading (as P1)

**Inputs.** |0…0⟩, |1…1⟩, Néel and anti-Néel; every qubit read in Z.

**Per input.** m = Σ_j (−z_j)⟨Z_j⟩, n without noise.

**Ratio.** ρ_E(D) = Σ_inputs m(D) / Σ_inputs m(ref).

- Each record has its own readout reference (X on the measured physical qubits).
- The sum over the four inputs cancels the first-order bias of relaxation and readout asymmetry.

**Weight 2.** m2 = Σ_j z_j z_{j+1}⟨Z_j Z_{j+1}⟩ is computed from the same counts and reported. No extra circuits.

**Readable depth.** L* per (arm, n, hz) is `kising_charge.decay_length` over D, in the noise wall's steps.

## Grid, shots, time

| item | value |
|---|---|
| arms | fold:rule, fold:zipcyc, qiskit:2:blind:template (map-free: failed elements only) |
| n | 20, 36 |
| hz | 0, 0.1, 0.3 |
| D (one-way L) | 24 (12), 50 (25), 100 (50) |
| circuits | 3 × 2 × 3 × 3 = 54 records × 8 = **432** |
| shots | 500 (1,000 would be 135 s: over 120 s) |
| time model | 432 × 0.036 + 432 × 500 × 0.00027 + 3 = **76.9 s**: one job per device, about 1.3 min (billed has been 0.72-1.0 of the model) |
| devices | home's choice; two devices about 2.6 min of the remaining Open Plan time |

## Rules (drafts from the instruction; the owner confirms)

| id | rule | judged where |
|---|---|---|
| A | rule beats zipcyc and blind Qiskit at 2 SE: WIN / LOSS / TIE per (hz, n, D) | cells where either arm's ρ_E exceeds 2 SE (else NOT JUDGED: noise floor) |
| B | zipcyc's κ = L*_rule / L*_zipcyc inside [3.3, 3.9] (10/29's fixed formula 2, L*_zipper = L*_rule / 3.6 ± 0.3, carried to the echo) | per (hz, n) |

**Predictions.**

- A: WIN against both arms in every judged cell, at every hz.
- B: INSIDE at every hz and n.

**Reported, not judged.**

- L*_rule against hz. Breaking integrability spreads the operator weight, so L* is expected to shrink.
- The n dependence.
- The weight-2 ratio.

**Not claimed.** The order of zipcyc and Qiskit: it reversed on marrakesh at n = 20.

## Twin rehearsal (pod)

`gpu/echo_hz_twin.sh`:

- n = 20, rule and zipcyc;
- hz and D as above;
- compiled on the published marrakesh snapshot, run on TOQB's stand-in (T1, T2, static ZZ; trajectories, T = 64).

**Not judged.** The twin's L* and κ are reported as the expectation, not judged against the rules.

**n = 36 has no twin.** Its noisy simulation is beyond reach, so it is device only.

## Limits

- **The sizes are home's choice.** hz values, depths and n are fixed by home's instruction. Nothing was chosen by
  simulation.
- **The echo tests a different observable.** It measures how well the circuit undoes itself (weight 1 and 2), not the
  conserved charge of stage 1.
- **κ may not carry over.** Its carry-over from the charge to the echo is a prediction, not a given.
- **One day per device.**
