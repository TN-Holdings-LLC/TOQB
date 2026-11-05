# Software behind the device results of 2026-11-04 and later

Built (placement, compilation, job folders) and scored at home with:

| | version |
|---|---|
| Python | 3.13.17 |
| qiskit | 2.5.2 |
| qiskit-aer | 0.18.0 (checks and simulations only) |
| numpy | 2.5.3 |
| qiskit-ibm-runtime | 0.49.0 (installed beside; not used for building or scoring) |

Submitted and collected from the owner's WSL with `python -m psf_os submit / collect` (SamplerV2, dynamical decoupling
and twirling off); the versions on that side are not recorded yet.

| result | psf-os used to build |
|---|---|
| p6-device-2026-11-04, p6-marrakesh-2026-11-04 | 61e9edd |
| os2d-2026-11-04 | 58b1423 |
| corr-2026-11-04, corr-marrakesh-2026-11-04 | 1250c90 |
| practice-2026-11-04, practice-fez-2026-11-04, daily/2026-11-05, twirl-explore-2026-11-05 | ac84182 |

Scoring does not depend on these differences: `python reproduce.py` re-scores every result above from its committed
raw counts with psf-os ac84182 (code-equal to 7739365) and finds every number the same (2026-11-05).
