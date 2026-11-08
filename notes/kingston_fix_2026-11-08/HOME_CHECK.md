# Home check of VS Claude's kingston note (2026-11-08)

From the two scores files (old against line, every place and t; post hoc, not a declared verdict):
- normalised per-site error MSE / mean square: line smaller in 13 of 16 (marrakesh) and 15 of 16 (kingston);
- mirror mean: line higher in 14 of 16 (marrakesh) and 16 of 16 (kingston). The note's "all 8 places, every t" is
  not exact: marrakesh candidate 3 (row 0, even, floor 0.87-0.89) has the line mirror lower at t = 3, 4
  (0.09 -> 0.07, 0.00 -> -0.02), and its normalised error higher at t = 3, 4 as well.
- kingston judged place t = 4: retention line - old -0.051 (VS's bootstrap: -2.3 sigma, one of 32 comparisons), while
  the normalised error is 0.466 (old) and 0.455 (line), and the mirror 0.09 and 0.17.
