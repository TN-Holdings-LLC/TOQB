# Declared: depth scan of IBM's 2023 utility observables, raw, on the published Eagle graph embedded in Heron

Home, written 2026-11-11 (owner 14:28 JST: "Aから順番に進めて", task A = where raw reading stops as the steps grow).
DRAFT until the owner's OK and the push; declared before any device record of this run is fetched; a change after the
push is a new declared file. Paper 9, part A.

## Question

On 11-10 (ibm_fez, `results/utility-2026-11-10`) Z_106 after 4 steps and the weight-10 product after 5 steps read raw.
With the exact region widened (`notes/reach_2026-11-11`), the same observables are run at more steps: up to which
number of steps does each still read, on one device and day?

## Circuits (unchanged from prereg/utility_2026-11-11.md)

Kim et al. (2023): |0...0>, t steps of R_X(theta_h) on every qubit then R_ZZ(-pi/2) on every edge, theta_h = k pi / 32,
k = 0..16; each R_ZZ(-pi/2) as RZ(-pi/2) x RZ(-pi/2) then one CZ; the whole embedded circuit (gates on failed elements,
outside every cone used, left out). Observables:
- `z106_t4` ... `z106_t8`: Z_106 after 4, 5, 6, 7, 8 steps (4 = the 11-10 point, repeated as the anchor);
- `w10_t5`, `w10_t6`: X13 X29 X31 Y9 Y30 Z8 Z12 Z17 Z28 Z32 after 5 (the 11-10 point) and 6 steps.
Weight-17 is not run (it did not read at 5 steps on 11-10).

## Device and placement (no quality number)

- Right before the fetch, pending jobs of ibm_marrakesh, ibm_fez, ibm_kingston (`gpu/daily_fetch.py`). In the order of
  fewest pending (ties: that order), the first device on which every one of the seven cones avoids every failed
  element; none: the first on which `z106_t4` to `z106_t6` and `w10_t5` do (the rest not built); none: not run.
- Per observable the first of the two embeddings (rustworkx VF2, fixed order) whose backward light cone holds no failed
  qubit or coupler; floor and mirror at k = 8 per observable; one ring sentinel; 4000 shots. A device on which the ring
  sentinel does not land counts as one on which the job cannot be built.
- Build: `gpu/utility_build.py DEV OUT ANS SEALED_DIR --obs z106_t4,z106_t5,z106_t6,z106_t7,z106_t8,w10_t5,w10_t6
  --max-seconds 160`.

## Answers (sealed)

Z_106 at 4 steps by `utility_exact.tn_value` at build time (as on 11-10); w10_t5 as released on 11-10
(`results/utility-2026-11-10/answers/w10_t5.jsonl`); the others by `gpu/reach_tn.py` (diagonal light-cone network,
sliced tree), kept outside the repository until the verdicts, sha256:
- z106_t5.jsonl 61bbd0c8a1a170a70aebbf421c37d937d8ceac62b87681a7ae1116bc986d0d04
- z106_t6.jsonl 2d347813f7960ce0d59e981c563b585a5175b53fa50f7ba3b20f78a7b4e1f4e5
- z106_t7.jsonl 2a31b3603ccbe85223bd51aaee7302f0e6797bf63e9f2390bd611de37491481a
- z106_t8.jsonl ff9c96734412177502baa69a791602bfdbeba75d4770ff7b8f8bd2467db93645
- w10_t6.jsonl 92b0f61eb39e984f86fe994c35b1db96a37d8dd4e7010e5f83d26a6cc5a15741
Checks of these values: theta_h = 0 and pi/2 against Aer's stabilizer method on the whole 127-qubit circuit (all
|diff| <= 4.4e-16); the network code is the code that matched `utility_exact.tn_value` at all 17 k at 4 steps
(1.0e-13); and, through the pre-run check below, k = 5 and 11 against quimb on the compiled job circuit. The build's
answers file (by tag) is hashed and printed at build time; it must equal these values.
Disclosure: while the quimb check was being written (11-11, about 15:40 JST), one sealed value (Z_106, 5 steps, k = 5)
was printed once on the home screen; the check now prints differences only. The prediction below was written before.

## Pre-run check (before submission): `gpu/utility_check.py OUT ANS`

On the job's own compiled circuits (whole device), FAIL anywhere means not run:
- every built observable at k = 0 and 16: Aer's stabilizer method, sampled (400 shots, as on 11-10) and, new on 11-11,
  the exact stabilizer expectation (0 or +-1 exactly) within 1e-9, so an exact value of 0 is checked strictly;
- Z_106 at 4 and 5 steps: all 17 k by the pruned cone's statevector (17 and 25 qubits; the limit raised from 20 to 25,
  Aer above 20 qubits), within 1e-9;
- deeper cones (31 to 43 qubits), new on 11-11: k = 5 and 11 by quimb's light-cone contraction of the compiled job
  circuit (generic gates, independent of the diagonal network that made the answers), within 1e-9.

## Verdicts (`gpu/utility_score.py OUT ANS`, unchanged)

Per observable and number of steps over its 17 points: READS if MSE <= mean square of the exact values / 2; per point
AGREES if |z - e| <= 0.05 (counted). Readable depth per observable: the largest number of steps that READS (reported;
a step that does not read below one that does is reported as it is). Beside, never judged: floor and mirror parity,
sentinel, CZ, and the 11-10 values of `z106_t4` and `w10_t5` against today's.

## Prediction (before any data; not rewritten if wrong)

- Z_106 READS at 4, 5 and 6 steps (on 11-10 its MSE was 0.05 of the mean square at 4 steps, far inside the line of 0.5);
  7 and 8 steps uncertain.
- The weight-10 product does not READ at 6 steps (at 5 steps its MSE was 0.135 of the mean square and its mirror
  parity 0.12; one more step adds 141 CZ to the circuit).

## Device time

Try-build on the 11-10 ibm_fez record (13:44:34 CET): all seven placed on embedding 0; CZ per circuit 564 / 705 / 846 /
987 / 1128 (Z_106, 4 to 8 steps) and 705 / 846 (weight-10); 137 circuits, 155.9 s by the model; answers sha256
81f46f24d665229491a3b9b53739b479c4c651f36c0fd3a44e486e72f49852a1 (the try-build's; the night's build hashes its own).
Pre-run check on the try-build: ALL PASS (stabilizer sampled and exact at k = 0, 16 for all seven; Z_106 4 and 5 steps
all 17 k by the cone, worst 1.2e-13 and 3.5e-12; the five deeper ones at k = 5, 11 by quimb, worst 2.9e-11, 4.3e-11,
7.0e-12, 6.0e-13, 3.6e-13).
Owner (14:47 JST): MAX 160 s with all seven (`z106_t4` kept as the anchor against 11-10). A build over 160 s by the
model on the night's record: the deepest Z_106 left out one step at a time until it fits (recorded).

## Limits

Heron, not Eagle; one device-day; raw values only, no comparison with IBM's mitigated values; intermediate angles at
the new depths are checked independently at k = 5 and 11 only (quimb); the other angles rest on the same network code.
