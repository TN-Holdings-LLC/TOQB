# P5 stage E, 2026-11-03/04: on ibm_kingston the suspect-qubit lattice brings theta 0.4 within the line (READS and AGREES at all three theta to depth 8); on ibm_fez (chosen by queue, no registry) theta 0.8 and 1.0 AGREE to depth 8 but theta 0.4 DIFFERS and the sentinel reads DEAD: two qubits with broken readout that IBM does not mark

- **Declaration:** `prereg/drafts-2026-11-03/kim_e_note.md` (SHA-256 c3dca91e...538e4528), fixed 15:03 CET, TOQB a7ad206.
- **Queue** read at 15:04:01 CET: ibm_fez 1, ibm_marrakesh 3, ibm_kingston 0 -> X = ibm_fez (`queue.json`). An
  ibm_marrakesh fetch taken by mistake is not used (`fetch_marrakesh_not_chosen.json`). By the time the jobs were sent
  (17:04 CET, after the pod) fez had 74 pending jobs.
- **Builds** 39eba6f (K: kingston 15:04:19 CET, suspect lattice 125 qubits; X: fez 15:05:54 CET, 153 qubits; failed on
  fez: (32, 33), qubit 72). Answers sealed in 39eba6f (CPU) and 3087056 (pod, H100, checks K1-K3 pass).
- **Jobs:** K dbl0c5hkdqps7393b9m0 (DONE 20:20 CET, 19 s billed), X dbl0c9t6p51s73cnh6e0 (DONE 17:14 CET, 40 s billed),
  sent with `psf-os submit` at 17:04 CET. Scored by `gpu/kim_e_score.py` (`K/scores.json`, `X/scores.json`).

## Judged

1. **Sentinels:** K **CLEAN**; X **DEAD** (n = 40 ring on fez, through qubits 23 and 51 below).
2. **K, stage C on the suspect lattice (kingston):**

| theta | MSE (half) | M measured / exact, t = 6, 7, 8 | max \|dM\| | verdict | stage C on the full lattice (ba41205) |
|---|---|---|---|---|---|
| 0.4 | 0.0021 (0.403) READS | 0.870/0.902, 0.858/0.887, 0.877/0.904 | 0.031 | **AGREES** | 0.053, DIFFERS |
| 0.8 | 0.0016 (0.110) READS | 0.432/0.440, 0.446/0.458, 0.474/0.484 | 0.012 | **AGREES** | 0.028 |
| 1.0 | 0.0010 (0.022) READS | 0.173/0.169, 0.184/0.180, 0.193/0.186 | 0.007 | **AGREES** | 0.010 |

   **Sentence fixed in advance holds:** *on the suspect-qubit lattice, psf-os reads the utility-form circuit without
   error mitigation to depth 8.*
3. **X, stages B and C on ibm_fez:**

| theta | B (t 1-5): MSE, max \|dM\| | C (t 6-8): MSE, max \|dM\| |
|---|---|---|
| 0.4 | 0.026 READS, 0.064 **DIFFERS** | 0.029 READS, 0.079 **DIFFERS** |
| 0.8 | 0.016 READS, 0.033 **AGREES** | 0.015 READS, 0.044 **AGREES** |
| 1.0 | 0.011 READS, 0.012 **AGREES** | 0.009 READS, 0.006 **AGREES** |

   The sentence for "all READS and AGREES" does not hold on the second device.

## Reported

- **Why fez misses:** qubit 23 reads <Z> = -0.79 at theta 0 (its readout is inverted: the state is |0> by
  construction), qubit 51 reads 0.23, qubit 83 0.68; IBM marks none of them failed. They are the three worst qubits at
  theta 0.4, t = 5, and 23 and 51 lie on the sentinel's ring. The theta-0 readout floor is 0.958 on fez against 0.977
  on kingston; without the 12 worst qubits fez's theta-0.4 magnetisation at t = 5 is 0.865 against 0.902 (the floor's
  size). fez had no registry: psf-os had nothing but IBM's failed marks there.
- The theta-0 circuit is itself a readout scan of every lattice qubit, taken in the same job, from the device's own
  counts (no calibration number): a qubit far below the floor at theta 0 can be dropped before scoring the others.
  This is a candidate rule; it is not applied here.
- Queue: K waited 3 h 15 min on kingston, X 9 min on fez.
