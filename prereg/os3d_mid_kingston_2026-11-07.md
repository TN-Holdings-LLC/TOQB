# Declared: the 4 x 4 x 3 run again, on ibm_kingston
(owner 2026-11-07 12:24 JST, after the fez run refused all five places: "kingston"; for the run of 2026-11-07, daytime)

Declared before the device record of this run is fetched. Everything as in `prereg/os3d_mid_2026-11-07.md` (lattice,
every qualifying place as a candidate, build with `--k 16 --max-seconds 400`, the declared gate, verdicts), except:

- Device: ibm_kingston (at the 04:17 CET reading 5 places qualified there). A fresh fetch (`gpu/daily_fetch.py`); if no
  place qualifies on kingston's fresh record, "not run".
- Answers: already released with the fez run (`results/os3d-mid-2026-11-07/answers/`, light-cone file 84d4e2ef...).
  The sealed hashes by k in `prereg/os3d_mid_2026-11-07.md` stand and the builder's output must match the one for its k.
  The build, the gate and the verdicts read no answer; the code is the declaring commit's.
