# TOQB loop reach run, n = 6, L = 8, 1,000 iterations: the score

Pre-registration: `prereg/2026-10-16-loop-n6-reach.md`. Seeds 8001-8200 (200).

## Verdicts

| ID | prediction | verdict | numbers |
|---|---|---|---|
| R1 | every arm run valid, 1,000 iterations, evaluated every 50 | CONFIRMED | not valid: 0 |
| R2 | iterations to a noisy test accuracy of 0.65, fewer with PSF-Zero | CONFIRMED | mean Qiskit - PSF-Zero 73.25 (95% 26.66 to 119.84), p = 0.001130; PSF-Zero sooner / equal / later: 103 / 33 / 64 of 200 |
| R3 | iterations to 0.70, fewer with PSF-Zero | CONFIRMED | mean Qiskit - PSF-Zero 82.25 (95% 24.85 to 139.65), p = 0.002760; PSF-Zero sooner / equal / later: 104 / 27 / 69 of 200 |
| R4 | dollars to 0.65, fewer with PSF-Zero | CONFIRMED | mean Qiskit - PSF-Zero 311.18 (95% 132.58 to 489.77), p = 0.000320; PSF-Zero sooner / equal / later: 136 / 0 / 64 of 200 |

## Reported without prediction

| quantity | PSF-Zero | Qiskit level 2 |
|---|---|---|
| 0.65: reached within 1,000 iterations | 192 of 200 | 186 of 200 |
| 0.65: iterations to reach (median, censored at 1,050) | 200.0 | 250.0 |
| 0.65: dollars to reach (median) | 755.1 | 968.0 |
| 0.70: reached within 1,000 iterations | 171 of 200 | 161 of 200 |
| 0.70: iterations to reach (median, censored at 1,050) | 300.0 | 400.0 |
| 0.70: dollars to reach (median) | 1132.7 | 1548.7 |
| accuracy at 1,000 iterations, noisy (mean) | 0.724 | 0.704 |
| dollars per iteration | 3.7756 | 3.8718 |

Mean noisy test accuracy by iteration (PSF-Zero / Qiskit level 2):

- 0: 0.289 / 0.283
- 50: 0.534 / 0.492
- 100: 0.583 / 0.554
- 150: 0.614 / 0.581
- 200: 0.639 / 0.608
- 250: 0.654 / 0.618
- 300: 0.661 / 0.638
- 350: 0.674 / 0.653
- 400: 0.682 / 0.659
- 450: 0.692 / 0.668
- 500: 0.690 / 0.673
- 550: 0.700 / 0.678
- 600: 0.698 / 0.685
- 650: 0.701 / 0.685
- 700: 0.706 / 0.686
- 750: 0.712 / 0.690
- 800: 0.711 / 0.695
- 850: 0.719 / 0.698
- 900: 0.717 / 0.700
- 950: 0.717 / 0.698
- 1000: 0.724 / 0.704

Versions and engine: 2.5.2; fast; psf_compile 2026-10-15.c61, psf_ai_compile 2026-10-15.a22.
