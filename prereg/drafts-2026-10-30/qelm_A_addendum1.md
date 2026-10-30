# QELM task A, addendum 1 (home, FIXED 2026-10-30 08:45 CET on the owner's go, before any fetch): ibm_kingston only

Applies to `qelm_A_note.md` (SHA-256 8c26afd773cbde8a4a749e6172b26bf10ab8e5579d4d3eafd290c4b3bd50f3b8, fixed by the
workplace 2026-10-30 03:30:50 CET) and its data `results/qelm-A-2026-10-30/noiseless.json` (32a6d656...b38d).

1. **Device: ibm_kingston only** (owner, 2026-10-30 16:35 JST). The declared bands are the kingston row of section 3
   (`results/qelm-A-2026-10-30/predict_kingston.json`). Rules G, Q1, Q2, Q3a, Q3b and R are unchanged.
2. **Why one device.** The question that matters most here is Q2 (whether the accuracy can be predicted before the run);
   one device answers it. The stand-in (pod, 2026-10-30) put Q3a on the "not WIN" side (rule 0.840 against zipcyc 0.785
   at S = 250, one-sided p 0.080), so a second device would mostly repeat a likely null at 5.2 min. Nothing in the
   rules, points or shots is changed after the stand-in.
3. **Device path.** `toqb.qelm_device` (build one job per arm from the declared task; score by the declared rules) and
   `gpu/qelm_device.sh`, added at home today; checked end to end on a fake device.
