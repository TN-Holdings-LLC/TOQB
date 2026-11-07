# Declared: the 4 x 4 x 3 run on ibm_kingston with the stop removed (always judge the top place; the gate as a flag)
(owner 2026-11-07 12:28 JST: "外して", after the proposal; supersedes `prereg/os3d_mid_kingston_2026-11-07.md`, whose
fetch at 04:28 CET came after it was pushed but before this change: that record is not used. For the run of 2026-11-07)

Declared before the device record of this run is fetched. Everything as in `prereg/os3d_mid_kingston_2026-11-07.md`
(ibm_kingston, 4 x 4 x 3, every qualifying place, the build, the answers and their sealed hashes, verdicts), except
the choice:

- Rule "top" (`gpu/os3d_v31_score.py OUT ANSWERS top`): the candidates are ranked by the mean of their own t = 1
  mirror, as in the gate; the first is **always** judged. The declared gate's checks (a) no site below the job's mirror
  line, (b) no |1> floor mark, (c) within 0.1 of the best are computed for every candidate and reported beside the
  verdicts as a flag: "healthy" when the judged place passes them all, "weak elements" otherwise. Nothing is refused.
- Why: on 2026-11-07 the gate refused every place at 48 and 72 sites (fez 5 + 2, kingston 1) while the arms read
  0.78-0.89 retention; the owner asked for a 3D record at these sizes. Applied after the fact to the day's runs (seen
  data, not evidence): marrakesh 4 x 2 x 2 candidate 1 (healthy, as judged); fez 4 x 4 x 3 candidate 1 (weak elements;
  error second smallest of five); kingston 4 x 6 x 3 candidate 0 (weak elements).
