# N = 91 (2026-11-09): after the verdicts (post hoc, not declared)

VS Claude's check from the raw job (`vs/`), reproduced at home from scores.json:

- Fit dispersion: the residuals of the declared rate fit are 4-8 times the shot noise (chi2 / 5 = 38.1, 26.2, 18.6
  for h = 0.05, 0.10, 0.15). With that dispersion in the SE (SE x sqrt(chi2 / 5) = 0.0017, 0.0018, 0.0021) the
  deviations k - cos 2h (+0.0006, +0.0020, +0.0037) are 0.4, 1.1 and 1.7 sigma. The declared verdicts (AGREES within
  max(2 SE, 0.005)) stand; the dispersion-inflated SE is printed beside them from now on.
- Across widths the deviation at h = 0.15 has the same sign every time: +0.0045 (N = 51), +0.0017 (N = 71), +0.0037
  (N = 91): slower decay than cos 2h. In all three runs h = 0 (the ruler) and 0.05 were in job A and 0.10, 0.15 in job
  B, so a difference between jobs enters the ratio; at N = 91 job A's sentinel was DEAD and job B's CLEAN.
  For a later declaration: put the h = 0 ruler in every job.
- Off the cone (ideal 0): mean |<X>| 0.043 (median 0.022) against about 0.013 from shot noise alone; 16.9 % of values
  beyond 3 SE (about 0.3 % from shot noise). Steady offsets, independent of t and h: q85 0.59, q83 0.45, q29 0.22
  (chain index 23, next to the t = 24 cone site), q34 0.18, q23 0.17, q143 0.16. Recorded as the raw noise floor of
  this run.
