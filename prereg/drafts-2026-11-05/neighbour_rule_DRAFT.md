# DRAFT (not declared; whether to test it is the owner's decision; workplace, 2026-11-05): avoid the neighbours of qubits our own measurements found unreadable

Status: draft only (task U3, home's instruction 05d). Home's view: the most direct fix. The owner decides whether to
test it.

## 0. Why (after the fact, 05b)

- On 11-04 the loss the mirror does not see sat next to the qubits rule R dropped: corrected residual at distance 1 of a
  dropped qubit, theta_x 0.53 / 0.3 / 0.8, marrakesh -0.23 / -0.18 / -0.07, fez -0.17 / -0.06 / -0.14 (home's
  recomputation); about 0 at distance 2 and beyond.
- A synthetic stuck qubit (sitting in |0>, a qubit that reads about 0.2 from t 1) reproduces that shape: through the
  problem's own RZZ it gives each neighbour a fixed Z rotation, which U^dagger undoes in the mirror and the forward
  circuit keeps.
- Rule R only drops such a qubit from the score; it stays in the circuit and keeps acting on its neighbours.
- P5's suspect-qubit rule (both ends of a failed coupler out of the lattice; HELPS 0.556 on 11-03) is the same idea
  for elements IBM flags. This rule extends it to qubits our own measurements find, and to their neighbours.

## 1. The rule (own measurements only; no calibration numbers)

- **Unreadable set U:** qubits rule R drops on a Z floor, or that the self-repair chain confirmed DEAD (rule (b): one
  job, a + 3 SE < line), within the chain's expiry (7 days). Taken from the ledger as it stands at the build.
- **B1, placement:** a copy (lattice2d order, translation only) is passed over if it contains a qubit of U **or a
  device neighbour of one** (as the suspect rule passes over the ends of failed couplers). The first copy that
  qualifies under the present rules and B1 is used; if none does, no job on that device (the next device by the
  existing rule).
- **B2, scoring (when a qubit of U is inside the copy anyway, e.g. found by rule R in the same job):** its patch
  neighbours at distance 1 are returned as "not readable" together with it (not corrected, not scored).
- Nothing else changes (compilation, floor, mirror, answer card).

## 2. What it costs (geometry and 11-04's own sets, after the fact)

| device (device record of 11-04 afternoon) | U (rule R, 11-04 morning) | copies of P6's patch qualifying now | qualifying under B1 |
|---|---|---|---|
| ibm_marrakesh | 23, 31, 48, 49 (13 qubits with neighbours) | (0,0), (0,4), (2,4) | **none**: every qualifying copy holds 4-11 of the 13; the two clean copies are refused already |
| ibm_fez | 27, 28 (5 with neighbours) | (0,0), (2,0), (4,0), (4,4) | (2,0), (4,0), (4,4): the copy moves two rows |

- So on marrakesh that day B1 would have refused P6 outright (the device rule then moves the job); B2 would have kept
  24 of 35 qubits readable (31 under rule R alone).
- U moves: marrakesh's rule-R set changed within 30-60 minutes on 11-04 (23, 29, 31 in the morning; 23, 31, 48, 49 an
  hour later). A U older than the job can be stale; B2 (same job) is not.
- 05b's after-the-fact O2 numbers for B2 (reference only, own recomputation): marrakesh MSE ratio 0.195 -> 0.104,
  0.111 -> 0.047, 0.159 -> 0.134 (still DIFFERS at 0.53 and 0.3); fez 0.082 -> 0.043, 0.018 -> 0.014, 0.41 -> 0.34.

## 3. The test (one job, A and B)

- A: today's rules (rule R scoring only). B: B1 for placement and B2 for scoring. Same device, same problem (P6,
  theta_x 0.53 and 0.8, t 1-9), same shots; A and B are placed separately (B's copy may differ from A's).
- If B1 leaves B on the same copy as A (U empty near A's copy), B differs from A only by B2; if B1 refuses B, the
  arm is recorded "refused" and the test is NOT TESTED that day.
- **Judged:** R = MSE_B / MSE_A of the raw forward <Z_q> against the sealed answers, t 1-9, over the qubits each arm
  returns as readable, HELPS / NO EFFECT / HURTS at 0.8 / 1.25.
- **Reported with it:** qubits returned as not readable per arm; the distance B's copy moved (rows, columns); B2 alone
  on A's data (the same job, no extra circuits); the floor of each arm.
- Honest note: B returns fewer qubits than A, so a lower MSE partly reflects what was left out; the count is always
  printed beside R.
- Cost: P6 at two theta_x, t 1-9, with floors (7) and no mirrors: 2 x (18 + 7) = 50 circuits at 2000 shots =
  1.8 + 27.0 + 3 = 31.8 s by the model (+ the sentinel).

## 4. Open for the owner

Whether to test it at all; B1 and B2 together or B2 alone (B2 needs no placement change and no older data); whether
a stale U (older than the expiry, or than one job) may move a copy.
