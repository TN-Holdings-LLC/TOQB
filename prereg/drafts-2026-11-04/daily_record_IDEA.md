# Idea (owner, 2026-11-04 14:33-14:36 CET; not a draft, not declared): a daily record of solved problems

Separate from the improvement work: every day, about two problems of today's difficulty, on two or three devices,
to build a reliability record that cannot be argued with afterwards. To be decided in the strategy talk (11/05 on).

## Shape (home's proposal, to be confirmed)

- Day (workplace): pick the day's problems by a fixed rule from a sealed pool; compute the exact answers on a pod;
  seal (hash committed); put them in the takehome ZIP.
- Night (home): fetch -> run2d batch -> submit -> collect -> score, on 2-3 devices; every day's result recorded,
  failures included. Job IDs let anyone check with IBM; answers can be recomputed by anyone.
- One fixed problem every day (the time series: day-to-day and device-to-device spread) and one new problem from the
  pool (no choice after the fact).
- Problems on a fixed patch placed by translation (P6 form): the answer is the same on any copy and any Heron r2
  device, so one pod computation serves every day and device. Whole-lattice problems (P5 form) only with the rule
  "run only if the failed elements are the same as in the morning".
- Depth: exact answers only while the causal cones fit a pod statevector (P6 form: about t 9-10); deeper would be an
  estimate (SPD / MPS), not a sealed answer.
- One standing declaration (rules, judgements READS / AGREES / BEATS, devices, what counts as a day) fixed once.
- Cost: about 10-15 s per device per day by the model (two problems with floor and mirror); to be checked on day 1.
