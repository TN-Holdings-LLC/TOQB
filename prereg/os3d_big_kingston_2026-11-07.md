# Declared: the 4 x 6 x 3 run again, on ibm_kingston
(owner 2026-11-07 11:58 JST, after the fez run refused both candidates: "別でやる"; for the run of 2026-11-07, daytime)

Declared before the device record of this run is fetched. Everything as in `prereg/os3d_big_2026-11-07.md` (lattice,
build, gate, verdicts), except:

- Device: ibm_kingston, the other device where a 4 x 6 x 3 fold translation qualified at the 03:44 CET reading (one
  translation, so k = 1 and the gate decides on that one candidate). A fresh fetch (`gpu/daily_fetch.py`); if no
  translation qualifies on kingston's fresh record, "not run".
- Answers: already released with the fez run (`results/os3d-big-2026-11-07/answers/`, light-cone file f261370d...).
  The sealed hash for k = 1 stands (7d874e25aa250f807be9aa5211ba4737864add86f9c2908c5259fa17e8ed8ee2) and the builder's
  output must match it. The build, the gate and the verdicts read no answer; the code is the declaring commit's, so
  nothing in this run is set after seeing the answers.
