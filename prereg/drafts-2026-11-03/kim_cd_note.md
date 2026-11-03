# P5 stages C and D and the suspect-qubit rule: the utility-form circuit on ibm_kingston's lattice at t = 6-8 (answers from a GPU server for the qubits whose cone allows it) and t = 20 (no exact answer), and a lattice without the ends of failed couplers (home, 2026-11-03)

**Why.** Stage B (`results/kim-lattice-2026-11-03`) read the exact answers on the whole lattice to t = 5 without error
mitigation. Its two worst qubits were the ends of IBM's failed coupler (130, 131). This note takes three steps in one
job: (1) the same lattice deeper, t = 6-8, where the exact answer of a qubit needs a GPU server and exists only for
qubits whose causal cone has at most 33 qubits; (2) t = 20, where no exact answer exists; (3) a psf-os rule that leaves
out both ends of every failed or masked coupler.

**Code.** psf-os 9f773ff (`psf_os/kim.py`: `region(dev, suspect=True)`; records with a list of t):
`gpu/kim_cd.py` builds the job and the CPU answers; `gpu/kim_answers.py` and `gpu/kim_answers_pod.sh` compute stage
C on one GPU (80 GB or more); `gpu/kim_cd_score.py` scores. Tests: tests/test_kim.py (psf-os),
tests/test_kim_answers.py (the GPU code's numpy path equals psf_os.kim's answers).

**The job** (one fetch, the registry `results/coverage-days-2026-11-02-day3/list_after.json`, no new scan; 4000 shots,
options off, "stay", `psf-os submit`; dry run on the fetch of 06:02 CET: 54 circuits, 63 s by the time model,
accepted):

| tag | lattice | theta | t | answers |
|---|---|---|---|---|
| b | stage B's (151 qubits, 163 edges in the dry run) | 0.4, 0.8, 1.0 | 1-5 | CPU cones (as stage B) |
| s | without the ends of failed or masked couplers (125 qubits, 134 edges: 11 suspect qubits and 15 cut off from the largest part) | 0.4, 0.8, 1.0 | 1-5 | CPU cones |
| c | stage B's | 0, 0.4, 0.8, 1.0, pi/2 | 6, 7, 8, 20 | theta 0: 1; pi/2: stabilizer (CPU); 0.4-1.0 at t = 6-8: pod, qubits with cones of at most 33 qubits (dry run: 151, 122, 82 qubits at t = 6, 7, 8); t = 20: none |

then the sentinel (echo D = 24 on the n = 40 ring).

**Order.** Fetch, build (the CPU answers and lattice.json are written by the build), the pod computes stage C's answers
from lattice.json, then all answers are sealed (SHA-256 committed), then the job is sent. The pod stops before any
answer if a check fails: K1 GPU = the CPU answers of the build (theta 0.8, t = 5, every qubit) within 1e-4; K2 single
= double on the five largest cones at t = 6 within 1e-4; K3 GPU = stabilizer at theta pi/2, t = 6 and 7, within 1e-4.
If the device's failed marks change between the fetch and the sending, `psf-os submit` refuses and the build is
repeated from a new fetch (and the pod run with it).

## Judged

1. **Sentinel:** CLEAN expected.
2. **Suspect-qubit rule (tags b and s, the same job):** the mean over theta of each lattice's mean squared error of
   <Z_q> against its own answers (every qubit, t = 1..5): ratio s / b <= 0.8: HELPS; >= 1.25: HURTS; else NO EFFECT.
   Reported: the price in qubits (151 -> 125 in the dry run) and the worst qubits of each lattice.
3. **Stage C (tag c, theta 0.4, 0.8, 1.0):** over the answered qubits and t = 6, 7, 8: READS if the mean squared error
   is at most half the answer's mean square; the magnetisation of the answered qubits AGREES if within 0.05 of exact at
   each t.
   - READS and AGREES at all three theta: *psf-os reads the utility-form circuit without error mitigation to depth 8,
     where the answer needs a GPU server.*
4. **Stage D controls (t = 20):** theta 0 (exact 1) and pi/2 (stabilizer): the magnetisation within 0.05: AGREES.

## Reported, not judged

Stage D at theta 0.4, 0.8, 1.0, t = 20: the measured magnetisation and its shot-noise SE, recorded as the device's
value of a quantity with no exact answer (3,260 CZ in the dry run's lattice). Stage C per t and per qubit; the controls
at t = 6-8; billed time; the pod's checks and cost.

**Stop.** One pod run (or its STOP) and one device run.
