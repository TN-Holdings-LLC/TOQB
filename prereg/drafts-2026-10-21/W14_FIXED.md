# W14 fixed (owner and home, 2026-10-21 14:26 CEST, before any record of the undamped-readout match exists)

The owner chose the headline: B (PSF undamped against Qiskit raw) and C (PSF undamped against Qiskit undamped) both
WIN in a group (angle, L); "won in k of 3 groups". Points 2 to 4 of the draft as proposed: no switch that turns the
undamping off for a poor model (reported per group instead); Qiskit's calibration-aware placement is its own choice;
about 4 to 5 h on an H100.

| file | SHA-256 |
|---|---|
| prereg/drafts-2026-10-21/W14_undamp_match_draft_2026-10-21.md | 39268a39ab686425a399e3e99e7b9fe0fd5009defb309152cdfcdfdc68e00df2 |
| toqb/match_score_undamp.py | 11bbc285b4a5e1f1522f27fe46b032adc0dccb4c67bae63cd5b9c40f61508d0d |
| tests/test_match_score_undamp.py | eef6d601524432008eabfa0fc6ed749b8b1dac5a77ae874d0de3ee88d4fa9c58 |
| toqb/undamp.py | d9d617887f743ef7e65eced4f3705c42e11a22ec04336df7aa1e477d89cbd8f7 |
| toqb/undamp_run.py | d85a6e91192b2a2109c205d432c83aecf59973a7ba8ad8f17d48ce8cbe803752 |
| toqb/match_score.py (W8, imported) | aa40de4363ab69840047060b8169e9010476b38a7690911feb0f27cfd896e122 |
| gpu/undamp_match.sh | 5eea9b515388a04dbd836f66356c4d497c1c18e485b2ef38bffac0ab01e2c9f1 |

Home check: tests 24 passed (undamp 5, its scorer 2, W8 and W11 scorers).
