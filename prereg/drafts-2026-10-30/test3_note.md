# Test 3: the mirror at n = 40 and 72, and the size wall read by the ring's own parity (DRAFT at home, 2026-10-30 05:30 CET; owner's go pending; to be fixed by SHA-256 and CET time before any fetch)

**Why.** Test 1 (`fold.band_shapes`) found rings up to 88 (kingston 10/24) and 96 (marrakesh 10/13). Noise wall stage 1
showed that a weight-2 charge decays at a per-step rate independent of n (L* 56.5 / 56.6 on marrakesh). That makes
the depth wall L*, but no size wall: a local quantity does not see n. The owner asked for the size limit measured as
L* measured the depth limit. Two parts:

- **E. The mirror at large n.** Test 2 (`echo_hz_note.md`, SHA-256 1308cf9b...7503696, fixed by the workplace
  2026-10-30 03:30:50 CET) at n = 40 and 72, nothing else changed.
- **P. The size wall.** The global parity P = X_1 ... X_n of the kicked-Ising ring (hz = 0) is conserved by the circuit
  (checked by statevector at n = 6, 7, 8 and after compilation by all three arms, `tests/test_kising_parity.py`). It has
  weight n, so it decays with the product n L: the readable volume V* is the n L at which its ratio falls to 1/e.

**What is not new.** Layer fidelity and errors per layered gate (McKay et al. 2023) measure how a layer's error grows with
size; mirror circuits are an established benchmark. The claim is limited to a map-free comparison of placements, and to
predicting V* from the charge's L* before the parity is measured.

## Part E (as test 2, n = 40 and 72)

- `gpu/echo_hz.sh` with `NS="40 72"` and `NOTE=prereg/drafts-2026-10-30/test3_note.md`; arms, hz (0, 0.1, 0.3), one-way
  L (12, 25, 50), inputs, acceptance rule (two-qubit gates = 2L x one layer; a failing record is void, not replaced),
  500 shots: as test 2. 432 circuits, time model 76.9 s, one job.
- Rules A and B of test 2, applied at n = 40 and 72. No twin (noisy simulation beyond reach).
- If an arm cannot place n = 72 on the day's map, that is recorded and nothing replaces it.

## Part P (`toqb.kising_parity`)

| item | value |
|---|---|
| circuit | the kicked-Ising ring, J = pi/4, h = 0.6, hz = 0, all L steps, every qubit read in X |
| inputs | \|+..+>, \|-..-> (P = +1), \|-+..+>, \|+-..-> (P = -1) |
| readout reference | per record, on the measured physical qubits: Neel, anti-Neel and each with its first bit flipped (X gates only) |
| estimate | rho_P = signed mean of the four inputs / signed mean of the four references (1 noiselessly); SE by the delta method |
| n | 20 and 36 (judged); 40 and 72 (reported only: the readout loss, about (1 - 2e)^n, leaves little signal at 72) |
| L | n = 20: 2, 4, 8; n >= 36: 1, 2, 4 |
| arms | fold:rule, fold:zipcyc, qiskit:2:blind:template (map-free) |
| shots | 1000 |
| circuits | 4 n x 3 arms x 3 L x 8 = 288; time model 288 x 0.036 + 288 x 1000 x 0.00027 + 3 = 91.1 s, one job |
| V* | per (arm, n): one-parameter fit rho_P = exp(-n L / V*) over its L (`kising_charge.decay_length` on n L) |

**Prediction (from the charge, before any parity is measured).** Under uniform Pauli noise the charge decays as
(1 - 4p/3)^(2L) and the parity as (1 - 4p/3)^(nL), so V* = 2 L*. With the rule's L* of 2026-10-29 (the mean of n = 20
and 36 on each device):

| device | L*_rule (10/29) | V*_rule predicted | V*_zipcyc predicted (= V*_rule / 3.6) |
|---|---|---|---|
| ibm_kingston | 85.5 | 171 | 47.5 |
| ibm_marrakesh | 56.6 | 113 | 31.4 |

## Rules (P)

| id | rule | where |
|---|---|---|
| P-A | V*_rule inside [0.8, 1.2] x predicted, widened by 2 SE: INSIDE, else BELOW / ABOVE | n = 20 and 36, each device |
| P-B | V*_zipcyc inside [V*_rule / 3.9, V*_rule / 3.3] (measured V*_rule; 10/29's fixed formula 2), widened by 2 SE | n = 20 and 36 |
| P-C | rule against zipcyc and blind Qiskit at 2 SE on rho_P: WIN / LOSS / TIE | cells where either arm's rho_P exceeds 2 SE |

- **Expected direction if P-A fails: BELOW.** The parity multiplies the sites' damping while the charge averages them,
  and dephasing damps X but not ZZ. Both make the parity decay faster than V* = 2 L* says. This is a stated risk, not a
  second prediction.
- **Reported, not judged:** V* at n = 40 and 72; V* of blind Qiskit; the readout factor (the reference's signed mean) per n.

## Time

Per device: part E 76.9 s + part P 91.1 s = 168 s by the time model (billed has been 0.72-1.0 of the model). Two devices
about 5.6 min.

## Limits

- One day per device; one ring per n; the band is the 10/29 rate scatter only.
- The readout reference corrects to first order; a strongly asymmetric qubit leaves a bias that grows with n.
- Every reference is classically computable; no classical-hardness claim.
