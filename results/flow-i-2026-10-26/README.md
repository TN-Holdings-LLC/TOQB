# Flow I, test match 4, 2026-10-26/27: Qiskit against the count rule and the zipper on the twin of ibm_kingston's 2026-10-24 calibration (rule declared)

Declared in prereg/drafts-2026-10-26/qiskit_match_k_note.md (SHA-256 a6c4193e…, `972c03e`, 14:18 CET). H100 pod, toqb
`e42eb8a` (972c03e plus the Target file in data/targets), psf-zero `61d0b545`; Target SHA-256 3b939138… (flows C, G).
Start 2026-10-26 15:15:52 CET; part 1 (Qiskit at n = 13, 14, 16, 18) 15:16:03-17:33:04 CET; part 2 (n = 15, 17) from
17:33:04; **stopped by the owner after n = 15** at 2026-10-27 07:40:41 CET (a watcher stopped the run once n = 15 had
all four models). Parts 3 and 4 and n = 17 were not run. Files: `check.jsonl`, `part1.jsonl`, `part2.jsonl` (the
`.log` files are identical copies of the rows), `times.txt`, `rust.txt`; qiskit_match_k_n15.zip SHA-256
c4ccd07f1d506972cd8c6acc38689cf2a0b5a08d12da3d30481c7e4bd11c2161.

**Check (declared): passed.** `fold:rule` and the zipper at n = 13, model 0, equal flow G's rows (lam 0.78576 and
0.6644, q2, us), so flow G's rule and zipper rows at n = 13-18 are used.

## Main match: `fold:rule` against Qiskit (level 2 on the Target, default seed), L = 16, four models

| n | Qiskit's active qubits | rule's lam | zipper's lam | Qiskit's lam | rule vs Qiskit | zipper vs Qiskit | two-qubit gates rule / zipper / Qiskit | us rule / zipper / Qiskit |
|---|---|---|---|---|---|---|---|---|
| 13 | 20 | 0.76-0.81 | 0.64-0.70 | 0.24-0.59 | **WIN** (4/4) | WIN (4/4) | 224 / 464 / 571 | 9.2 / 10.8 / 53.7 |
| 14 | 20 | 0.73-0.82 | 0.63-0.77 | 0.19-0.64 | **WIN** (4/4) | WIN (4/4) | 256 / 496 / 530 | 9.2 / 10.8 / 49.1 |
| 15 | 24 | 0.78-0.81 | 0.67-0.69 | 0.21-0.47 | **WIN** (4/4) | WIN (4/4) | 288 / 544 / 699 | 9.3 / 10.8 / 65.5 |
| 16 | 16 | 0.77-0.80 | 0.60-0.70 | 0.10-0.38 | **WIN** (4/4) | WIN (4/4) | 320 / 576 / 968 | 9.3 / 10.8 / 94.7 |
| 17 | 24 | | | | not run (stopped) | | 352 / 624 / 629 | 9.3 / 10.8 / 57.8 |
| 18 | 22 | 0.61-0.68 | 0.63-0.66 | -0.05-0.28 | **WIN** (4/4) | WIN (4/4) | 352 / 656 / 639 | 6.7 / 10.8 / 53.0 |

Qiskit's lam per model (± its standard error from the fit, lam sqrt(1/corr^2 - 1)/sqrt(P - 2)):
n = 13 0.25 ± 0.08, 0.29 ± 0.05, 0.59 ± 0.10, 0.24 ± 0.06; n = 14 0.30 ± 0.09, 0.64 ± 0.07, 0.22 ± 0.06, 0.19 ± 0.10;
n = 15 0.21 ± 0.06, 0.33 ± 0.10, 0.47 ± 0.11, 0.31 ± 0.07; n = 16 0.26 ± 0.05, 0.38 ± 0.16, 0.11 ± 0.06, 0.10 ± 0.08;
n = 18 -0.05 ± 0.26, 0.15 ± 0.13, 0.24 ± 0.15, 0.28 ± 0.14. The rule's standard errors are 0.01-0.03.

- **Prediction (rule WIN against Qiskit at every n where both ran): held** at all five n run (20 of 20 models).
- **Vanity:** Qiskit's circuits have 1.8-3.0 times the rule's two-qubit gates and 5.3-10 times its duration, on 16-24
  active qubits for a ring of 13-18.
- **What a device user needs (a twin of a real day's calibration):** the rule kept 0.61-0.82 of the signal on every
  model; Qiskit's circuits kept -0.05-0.64, below 0.3 on 14 of 20 models. Where Qiskit's lam is positive the rule keeps
  1.3-7.6 times as much (shots for the same precision 1.6-57 times fewer). At n = 18, model 0, Qiskit's circuit kept no
  measurable signal (-0.05 ± 0.26, correlation with the noiseless output -0.04). The zipper too kept more than Qiskit on
  every model. Qiskit's circuit is the same for the four models (its template does not depend on the parameters), yet
  its lam ranges 0.19-0.64 at n = 14 and its correlation with the noiseless output is 0.28-0.90 (the rule's 0.99): its
  long circuits leave the output noisy as well as damped.
- **Cost of simulating Qiskit's circuits** (one model, 24 inputs x 256 trajectories): 223-238 s at 20 active qubits,
  27 s at 16, 1,518 s at 22, 12,693 s at 24; the rule and the zipper at n = 13-18 took 3-141 s (flow G). The declaration's
  estimate for 24 active qubits was about 2.8 times too low. Above n = 18 Qiskit's circuits use 22-28 or more active
  qubits; not simulating them is a limit of this method, not a measurement of Qiskit.

**Not claimed.** No device; one day's calibration of one device; random models; Qiskit at optimization level 2 with its
default seed only; n = 17 and n >= 20 not run.

**Owner's decision (2026-10-27):** Qiskit is not included in further TOQB runs: on these matches it lost every
completed comparison and took most of the GPU time. This flow is its last match.
