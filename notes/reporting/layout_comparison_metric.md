# Main measure for comparing layouts (owner 2026-11-08 23:17 JST "よいです")

From the next declared comparison of layouts on: the main measure is the normalised per-site error,
nMSE = mean over sites of (<Z> - exact)^2 / mean over sites of exact^2, compared between layouts at the same place
and depth (smaller is closer to the exact answer). The retention of an order parameter (m_s / m_s exact) is printed
beside it on every row, as before.

Why: the order parameter decays in the exact evolution; noise that slows the exchange can keep it high, so its
retention can look better on a noisier circuit (2026-11-08: kingston judged place t = 4, retention line - old -0.051
while nMSE 0.466 -> 0.455 and mirror 0.09 -> 0.17; old's retention 0.495 -> 0.499 from t = 3 to 4 with mirror 0.11;
notes/kingston_fix_2026-11-08). A hypothesis, not yet tested directly. The two runs of 2026-11-08 keep their declared
verdicts on retention; their nMSE comparison is recorded as a post-hoc reference only.
