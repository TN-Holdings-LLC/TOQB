# P5 stage E: the suspect-qubit lattice at depth 6-8 on ibm_kingston, and stages B and C reproduced on a second device chosen by its queue (home, 2026-11-03)

**Why.** Stage C on kingston (`results/kim-cd-2026-11-03`) agreed at theta 0.8 and 1.0 and missed at theta 0.4 by
0.003 beyond the 0.05 line at t = 8; the same job showed that leaving out the ends of failed couplers halves the error
(ratio 0.556, t <= 5). Two questions: (K) does the suspect-qubit lattice bring theta 0.4 at t = 6-8 within the line on
kingston; (X) does the whole ladder (t = 1..8) hold on a second device.

**Device choice (owner, 2026-11-03: decide by the queue).** Right before the fetches, the pending jobs of ibm_fez and
ibm_marrakesh are read (pending jobs only: no quality number); X is the one with fewer (fez on a tie). The numbers are
recorded. Job K stays on ibm_kingston (the comparison with stage C).

**The jobs** (`gpu/kim_e.py`, psf-os 9f773ff unchanged; lattice: `kim.region(suspect=True)`; 4000 shots, options off,
"stay", `psf-os submit`):

| job | device | lattice | theta | t | dry run |
|---|---|---|---|---|---|
| K | ibm_kingston, registry day 3 | suspect | 0, 0.4, 0.8, 1.0 | 6, 7, 8 | 16 circuits, 21 s; 125 qubits; answered at t = 6, 7, 8: 125, 108, 75 |
| X | fez or marrakesh, no registry (none exists for them) | suspect | 0, 0.4, 0.8, 1.0 | 1..8 | fez (1 Nov fetch): 36 circuits, 43 s, 153 qubits; marrakesh (1 Nov): 150 qubits |

Each job ends with the sentinel (echo D = 24 on the n = 40 ring).

**Answers.** theta 0: 1. t <= 5: CPU cones (sealed with the build). t = 6-8: the pod (`gpu/kim_e_pod.sh`, once per
lattice, checks K1-K3 as in stage C), qubits with cones of at most 33 qubits. All answers are sealed (SHA-256
committed) before either job is sent. A refusal at submission (failed marks changed) means a new fetch and build for
that job.

## Judged (theta 0.4, 0.8, 1.0)

1. **Sentinels:** CLEAN expected on both.
2. **K, stage C on the suspect lattice:** READS (mean squared error over answered qubits and t = 6-8 at most half the
   answer's mean square) and AGREES (magnetisation of the answered qubits within 0.05 of exact at each t).
   - READS and AGREES at all three theta: *on the suspect-qubit lattice, psf-os reads the utility-form circuit without
     error mitigation to depth 8.* Reported with it: the theta-0.4 misses against stage C's (0.037, 0.039, 0.053).
3. **X, stages B and C:** the same two verdicts per theta over t = 1..5 (every qubit) and over t = 6..8 (answered
   qubits).
   - All READS and AGREES: *the result holds on a second device.*

## Reported, not judged

Queue numbers at the choice; per-t magnetisations; worst qubits; the theta-0 readout floor; billed time and the queue
wait.

**Stop.** One pod run (two lattices) and one run of each job.
