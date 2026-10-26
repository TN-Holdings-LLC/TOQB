# Estimating lam without simulation: both estimators fail the declared test (2026-10-26)

Declared in prereg/drafts-2026-10-26/esp_check_note.md (SHA-256 df3e5b50…, `9e35695`, 03:26 CET) before any estimate
was computed. `toqb/esp_est.py` (E1: ESP of the whole circuit; E2: ESP of clbit 0's backward light cone; no fitted
parameter) on the 64 cells of flows D and E that have a twin lam (holes, pendants, zipper, Qiskit; n = 9-19, L = 8,
16); `toqb/esp_score.py` scores them; `esp_cells.jsonl`, `score.txt`. Cloud container, compile only.

| estimator | L | Spearman with lam (need >= 0.8) | pairs ordered alike (need >= 90 %) | verdict |
|---|---|---|---|---|
| E1 | 8 | 0.45 | 23 / 28 (82 %) | fail |
| E1 | 16 | 0.48 | 26 / 29 (90 %) | fail |
| E2 | 8 | 0.68 | 26 / 28 (93 %) | fail |
| E2 | 16 | 0.57 | 26 / 29 (90 %) | fail |

**By the declaration, no estimate is reported as a lam for n = 21-30; the counts alone stand
(results/rule-big-2026-10-26).**

- **Read (not a rule).** The error product misses most of what decides lam here. It is far below lam in size (L = 16:
  0.005-0.11 against lam 0.07-0.73), and it misorders the zipper against Qiskit and the holes, and the pendants against
  the zipper at n = 18 (score.txt lists every misordered pair). This fits earlier findings that the noise reaching the
  read-out depends on the circuit's shape (results/lam-ablate-2026-10-22), not only on how many errors it contains.
- The light cone (E2) ranks better than the whole circuit (E1) but not well enough.
