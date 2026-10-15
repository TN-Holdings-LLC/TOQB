# TOQB loop standard run 2, n = 6, L = 8: the score

Pre-registration: `prereg/2026-10-15-loop-n6-standard-2.md`. Seeds 1001-1200 (200).

## Verdicts

| ID | prediction | verdict | numbers |
|---|---|---|---|
| M1 | every arm run valid and complete | CONFIRMED | not valid or incomplete: 0 |
| M2 | noiseless final accuracy, PSF-Zero > Qiskit | REFUTED | mean difference -0.000, p = 0.528612; PSF-Zero better / equal / Qiskit better: 85 / 19 / 96 of 200; worst seed -0.292 |
| M3 | noisy final accuracy, PSF-Zero > Qiskit | NOT DECIDED | mean difference 0.001, p = 0.453933; PSF-Zero better / equal / Qiskit better: 91 / 7 / 102 of 200; worst seed -0.323 |
| M4 | noisy final margin, PSF-Zero > Qiskit | CONFIRMED | mean difference 0.050, p = 0.000005; PSF-Zero better / equal / Qiskit better: 150 / 0 / 50 of 200; worst seed -0.278 |
| M5 | the noiseless difference grows from iteration 60 to the end | REFUTED | 0.010 at 60, -0.000 at the end; mean growth -0.010, p = 0.882326 |
| M6 | PSF-Zero spends no more than Qiskit, every seed | CONFIRMED | over or missing: 0 |

## The two numbers

- **Display:** mean final accuracy, noisy, for the same money: PSF-Zero 0.702, Qiskit level 2 0.701.
- **Essential:** PSF-Zero gave the better model in 91 of 200 seeds, a worse one in 102; worst seed -0.323. Seeds reaching 0.7 (noisy, final): PSF-Zero 114, Qiskit 114.

## Reported without prediction

| quantity | PSF-Zero | Qiskit level 2 |
|---|---|---|
| final accuracy, noisy | mean 0.702 (sd 0.090; 0.406-0.875) | mean 0.701 (sd 0.078; 0.427-0.896) |
| final accuracy, noiseless | mean 0.708 (sd 0.087; 0.417-0.875) | mean 0.709 (sd 0.078; 0.438-0.875) |
| final margin, noisy | mean 0.206 (sd 0.117; -0.020-0.388) | mean 0.156 (sd 0.087; 0.002-0.282) |
| accuracy at 60, noisy | mean 0.625 (sd 0.105; 0.344-0.875) | mean 0.613 (sd 0.101; 0.375-0.833) |
| accuracy at 60, noiseless | mean 0.637 (sd 0.097; 0.417-0.854) | mean 0.627 (sd 0.096; 0.396-0.833) |
| whole training, batch $ | mean 1510.244 (sd 0.000; 1510.244-1510.244) | mean 1548.730 (sd 0.000; 1548.730-1548.730) |
| two-qubit gates | mean 120.000 (sd 0.000; 120.000-120.000) | mean 158.000 (sd 0.000; 158.000-158.000) |
| duration, us | mean 8.712 (sd 0.000; 8.712-8.712) | mean 18.108 (sd 0.000; 18.108-18.108) |
| wall time per arm, s | mean 142.816 (sd 2.914; 134.783-152.645) | mean 152.401 (sd 3.498; 144.488-163.168) |

Classical reference (the same task for every seed): logistic 0.771, logistic_quad 0.750, mlp32 0.771, knn5 0.729.

Versions and engine: 2.5.2; fast; psf_compile 2026-10-15.c61, psf_ai_compile 2026-10-15.a22.
