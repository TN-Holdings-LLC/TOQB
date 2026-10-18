# TOQB S2R stage 0: the score

Pre-registration: `prereg/2026-10-17-s2r-stage0.md`. Seeds 9001-9020 (20).

## Verdicts

| ID | prediction | verdict | numbers |
|---|---|---|---|
| S1 | every run valid | CONFIRMED | not valid: 0 |
| S2 | S2R: PSF-Zero's final stand-in test accuracy higher than Qiskit level 2's | NOT DECIDED | mean 0.015 (95% -0.020 to 0.050), p = 0.210602; better / equal / worse: 11 / 2 / 7 of 20 |
| S3 | S2R: the simulator's ranking agrees better with the stand-in's for PSF-Zero (mean Spearman) | NOT DECIDED | mean 0.036 (95% -0.003 to 0.074), p = 0.042670; better / equal / worse: 13 / 0 / 7 of 20 |
| S4 | S2R beats device-only SPSA at the same budget, for each compiler | CONFIRMED | PSF-Zero: mean 0.231 (95% 0.154 to 0.308), p = 0.000016; better / equal / worse: 18 / 0 / 2 of 20; Qiskit: mean 0.242 (95% 0.196 to 0.287), p = 0.000001; better / equal / worse: 20 / 0 / 0 of 20 |

## Reported without prediction

| quantity | PSF-Zero | Qiskit level 2 |
|---|---|---|
| S2R: final stand-in test accuracy (mean) | 0.727 | 0.712 |
| device-only SPSA: final stand-in test accuracy (mean) | 0.496 | 0.470 |
| S2R: final simulated test accuracy (mean) | 0.742 | 0.729 |
| S2R: final noiseless test accuracy (mean) | 0.738 | 0.725 |
| S2R: Spearman, simulator vs stand-in, top k (mean) | 0.371 | 0.336 |
| S2R: loops within the budget (mean) | 6.00 | 6.00 |
| S2R: dollars spent (mean) | 181.23 | 185.85 |
| SPSA: iterations within the budget (mean) | 50.0 | 49.0 |
| SPSA: dollars spent (mean) | 188.78 | 189.72 |

S2R, mean stand-in test accuracy after each loop (PSF-Zero / Qiskit level 2):

- loop 0: 0.245 / 0.240 (20 / 20 seeds)
- loop 1: 0.438 / 0.399 (20 / 20 seeds)
- loop 2: 0.639 / 0.617 (20 / 20 seeds)
- loop 3: 0.680 / 0.677 (20 / 20 seeds)
- loop 4: 0.705 / 0.704 (20 / 20 seeds)
- loop 5: 0.740 / 0.721 (20 / 20 seeds)
- loop 6: 0.727 / 0.712 (20 / 20 seeds)

Versions: 2.5.2; psf_compile 2026-10-15.c61, psf_ai_compile 2026-10-15.a22.
