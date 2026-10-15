# TOQB loop standard run, n = 6, L = 8: the score

Pre-registration: `prereg/2026-10-15-loop-n6-standard.md`. Seeds: 101-120 (20).

## Verdicts

| ID | prediction | verdict | numbers |
|---|---|---|---|
| L1 | every arm run valid and complete | CONFIRMED | not valid or incomplete: none |
| L2 | noiseless final accuracy, PSF-Zero > Qiskit | NOT DECIDED | mean difference 0.040, p = 0.058960, PSF-Zero better / equal / Qiskit better: 14 / 0 / 6 of 20; worst seed -0.188 |
| L3 | noisy final accuracy, PSF-Zero > Qiskit | CONFIRMED | mean difference 0.078, p = 0.001310, PSF-Zero better / equal / Qiskit better: 16 / 1 / 3 of 20; worst seed -0.135 |
| L4 | noisy final margin, PSF-Zero > Qiskit | CONFIRMED | mean difference 0.038, p = 0.000555, PSF-Zero better / equal / Qiskit better: 16 / 0 / 4 of 20; worst seed -0.044 |
| L5 | mean noiseless difference >= 0.1 | REFUTED | 0.040 |
| L6 | PSF-Zero spends no more than Qiskit on the whole training, every seed | CONFIRMED | seeds over or missing: none |

## The two numbers

- **Display (the benchmark's headline):** mean final accuracy on the test set, noisy, for the same money: PSF-Zero 0.549, Qiskit level 2 0.471.
- **Essential (for someone who trains once):** PSF-Zero gave the better model in 16 of 20 seeds, the same in 1, a worse one in 3; the worst seed's difference was -0.135. Noiseless, i.e. how far the training itself went: mean difference 0.040.

## Reported without prediction

| quantity | PSF-Zero | Qiskit level 2 |
|---|---|---|
| final accuracy, noisy | mean 0.549 (sd 0.077; median 0.536; 0.417-0.688) | mean 0.471 (sd 0.082; median 0.474; 0.302-0.656) |
| final accuracy, noiseless | mean 0.552 (sd 0.077; median 0.562; 0.375-0.708) | mean 0.512 (sd 0.084; median 0.521; 0.375-0.708) |
| final margin, noisy | mean 0.025 (sd 0.046; median 0.013; -0.059-0.152) | mean -0.014 (sd 0.033; median -0.015; -0.079-0.044) |
| whole training, batch $ | mean 226.537 (sd 0.000; median 226.537; 226.537-226.537) | mean 232.310 (sd 0.000; median 232.310; 232.310-232.310) |
| whole training, session $ | mean 232.404 (sd 0.117; median 232.403; 232.110-232.566) | mean 236.657 (sd 0.071; median 236.662; 236.519-236.763) |
| two-qubit gates | mean 120.000 (sd 0.000; median 120.000; 120.000-120.000) | mean 158.000 (sd 0.000; median 158.000; 158.000-158.000) |
| duration, us | mean 8.712 (sd 0.000; median 8.712; 8.712-8.712) | mean 18.108 (sd 0.000; median 18.108; 18.108-18.108) |
| wall time per arm, s | mean 456.570 (sd 3.033; median 456.880; 450.126-461.436) | mean 511.893 (sd 2.477; median 511.328; 508.463-517.639) |
| reached accuracy 0.7 (seeds; median $ to reach it, batch) | 0 of 20; - | 0 of 20; - |

Classical reference (the same task for every seed): logistic 0.771, logistic_quad 0.750, mlp32 0.771, knn5 0.729.

Versions: 2.5.2; psf_compile 2026-10-15.c61, psf_ai_compile 2026-10-15.a22.

## Per seed

| seed | PSF-Zero noisy / noiseless / margin | Qiskit noisy / noiseless / margin | $ batch PSF-Zero / Qiskit | equivalence PSF-Zero / Qiskit |
|---|---|---|---|---|
| 101 | 0.656 / 0.646 / 0.106 | 0.521 / 0.542 / -0.015 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 102 | 0.490 / 0.542 / 0.008 | 0.427 / 0.438 / -0.079 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 103 | 0.521 / 0.521 / 0.021 | 0.656 / 0.708 / 0.043 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 104 | 0.521 / 0.583 / 0.019 | 0.479 / 0.417 / -0.012 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 105 | 0.625 / 0.625 / 0.048 | 0.521 / 0.542 / 0.022 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 106 | 0.688 / 0.708 / 0.152 | 0.562 / 0.583 / 0.030 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 107 | 0.417 / 0.375 / -0.059 | 0.521 / 0.521 / -0.015 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 108 | 0.594 / 0.583 / 0.033 | 0.531 / 0.438 / -0.007 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 109 | 0.688 / 0.583 / 0.039 | 0.469 / 0.479 / -0.027 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 110 | 0.531 / 0.479 / -0.001 | 0.375 / 0.438 / -0.033 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 111 | 0.479 / 0.542 / -0.002 | 0.479 / 0.583 / -0.054 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 112 | 0.542 / 0.583 / 0.012 | 0.573 / 0.646 / 0.044 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 113 | 0.625 / 0.625 / 0.072 | 0.458 / 0.521 / -0.004 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 114 | 0.542 / 0.542 / 0.002 | 0.438 / 0.479 / -0.015 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 115 | 0.562 / 0.500 / 0.046 | 0.479 / 0.583 / 0.007 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 116 | 0.531 / 0.583 / 0.011 | 0.375 / 0.438 / -0.057 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 117 | 0.469 / 0.583 / -0.001 | 0.458 / 0.542 / -0.017 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 118 | 0.521 / 0.542 / -0.008 | 0.302 / 0.438 / -0.054 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 119 | 0.542 / 0.458 / 0.013 | 0.406 / 0.375 / -0.019 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
| 120 | 0.438 / 0.438 / -0.016 | 0.385 / 0.542 / -0.012 | 226.54 / 232.31 | 3 of 3 / 3 of 3 |
