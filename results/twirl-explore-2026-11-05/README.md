# Exploratory (not declared, not the daily record): CZ-twirled correction on the device, 2026-11-05

Owner, 2026-11-05 evening: "no record needed; fix the correction as well as possible, check it, test D02 on the device
to see whether the direction is right". Code `gpu/twirl_explore.py` (e6d7234); synthetic check in
`notes/twirl_explore_2026-11-05/`. psf-os fetch 11:57 CET; jobs marrakesh dbm644hkbkrc73cou76g, fez dbm6471kbkrc73cou7e0
(64 circuits, 1000 shots each). Answers: the day-1 answers (`results/daily/2026-11-05/answers.json`).

| M - M_exact | raw | twirled | corrected, untwirled mirror | corrected, twirled mirror |
|---|---|---|---|---|
| D02 marrakesh | -0.092 | -0.159 | +0.030 (MSE 0.0043) | +0.026 (0.0044) |
| D02 fez | -0.143 | -0.239 | +0.005 (0.0117) | -0.029 (0.0316) |
| FX-A marrakesh | -0.037 | -0.052 | +0.120 (0.0168) | +0.059 (0.0065) |
| FX-A fez | -0.038 | -0.055 | +0.070 (0.0085) | +0.045 (0.0073) |

- The twirl halves the mirror's over-correction of FX-A (+0.120 -> +0.059, +0.070 -> +0.045), as the synthetic noise
  predicted in direction (not in size: +0.015 there).
- It costs forward signal: D02 raw -0.092 -> -0.159 and -0.143 -> -0.239 with only about 130 extra X gates and
  depth +4 %; most likely the twirl breaks a cancellation of coherent errors between the two CZs of each RZZ(1.0)
  (hypothesis, not tested). On fez the twirled D02 correction is worse per qubit (MSE 0.0316 against 0.0117).
- Net: half the direction. Next idea (not built): twirl each RZZ block as a unit (Paulis around the CX-RZ-CX pair),
  keeping the block's own echo; and an echo on idle qubits.

## Second job: block twirl beside the CZ twirl (12:34 CET; marrakesh dbm6jcl8mdtc73d7dio0, fez dbm6jfd8mdtc73d7dit0)

| M - M_exact | raw | CZ twirl | block twirl | corr. raw mirror | corr. CZ twirl | corr. block twirl |
|---|---|---|---|---|---|---|
| D02 marrakesh | -0.110 | -0.169 | -0.168 | +0.017 | +0.024 | +0.020 |
| D02 fez | -0.149 | -0.241 | -0.232 | +0.002 | -0.035 | -0.031 |
| FX-A marrakesh | -0.035 | -0.044 | -0.045 | +0.149 | +0.087 | +0.094 |
| FX-A fez | -0.048 | -0.065 | -0.056 | +0.142 | +0.114 | +0.115 |

- The block twirl loses as much forward signal as the CZ twirl: the "broken echo inside each RZZ" hypothesis is
  refuted. Any frame randomisation costs D02 about 0.06-0.09: the untwirled circuit's smaller miss came from coherent
  errors that happen to pull the answer up, not from a smaller loss.
- FX-A stays over-corrected with every mirror (+0.09 to +0.15 this run; +0.05 to +0.06 an hour earlier): the mirror's
  decay (0.36-0.50 per run) is far faster than the square of the forward decay for this chain problem, twirled or not.
- Conclusion of the exploration: a mirror-based gate correction is problem-dependent here (D02 fits, FX-A does not)
  and the twirl does not remove that. Only the floor step is safe for both (small).
