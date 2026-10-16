# TOQB loop budget run, n = 6, L = 8, 2 minutes of QPU: the score

Pre-registration: `prereg/2026-10-16-loop-n6-budget.md`. Seeds 6001-7000 (1000).

## Verdicts

| ID | prediction | verdict | numbers |
|---|---|---|---|
| B1 | every arm run valid, stopped within the budget, evaluated at the stop | CONFIRMED | not valid: 0 |
| B2 | noiseless accuracy at the budget, PSF-Zero > Qiskit | CONFIRMED | mean difference 0.0264 (95% 0.0204 to 0.0324), p = 0.000005; better / equal / worse: 550 / 84 / 366 of 1000; worst seed -0.292 |
| B3 | noisy accuracy at the budget, PSF-Zero > Qiskit | CONFIRMED | mean difference 0.0392 (95% 0.0330 to 0.0453), p = 0.000005; better / equal / worse: 624 / 51 / 325 of 1000; worst seed -0.281 |
| B4 | noisy margin at the budget, PSF-Zero > Qiskit | CONFIRMED | mean difference 0.0225 (95% 0.0200 to 0.0250), p = 0.000005; better / equal / worse: 735 / 2 / 263 of 1000; worst seed -0.123 |
| B5 | PSF-Zero gets at least as many iterations as Qiskit within the budget, every seed | CONFIRMED | fewer or missing: 0 |

## The two numbers

- **Display:** mean accuracy at 2 minutes of QPU, noisy: PSF-Zero 0.533, Qiskit level 2 0.494.
- **Essential:** PSF-Zero gave the better model in 624 of 1000 seeds, the same in 51, a worse one in 325; worst seed -0.281.

## Reported without prediction

| quantity | PSF-Zero | Qiskit level 2 |
|---|---|---|
| accuracy at the budget, noisy | mean 0.533 (sd 0.103; 0.188-0.896) | mean 0.494 (sd 0.101; 0.208-0.802) |
| accuracy at the budget, noiseless | mean 0.552 (sd 0.097; 0.208-0.854) | mean 0.526 (sd 0.095; 0.229-0.833) |
| margin, noisy | mean 0.022 (sd 0.058; -0.102-0.284) | mean -0.000 (sd 0.043; -0.114-0.205) |
| iterations within the budget | mean 50.000 (sd 0.000; 50.000-50.000) | mean 49.000 (sd 0.000; 49.000-49.000) |
| spent, batch $ | mean 188.781 (sd 0.000; 188.781-188.781) | mean 189.719 (sd 0.000; 189.719-189.719) |
| two-qubit gates | mean 120.000 (sd 0.000; 120.000-120.000) | mean 158.000 (sd 0.000; 158.000-158.000) |
| duration, us | mean 8.712 (sd 0.000; 8.712-8.712) | mean 18.108 (sd 0.000; 18.108-18.108) |
| wall time per arm, s | mean 15.241 (sd 0.593; 13.988-17.580) | mean 15.046 (sd 0.593; 14.134-17.326) |

Classical reference (the same task for every seed): logistic 0.771, logistic_quad 0.750, mlp32 0.771, knn5 0.729.

Versions and engine: 2.5.2; fast; psf_compile 2026-10-15.c61, psf_ai_compile 2026-10-15.a22.
