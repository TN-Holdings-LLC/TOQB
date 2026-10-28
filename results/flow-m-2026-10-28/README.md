# Flow M (2026-10-28): the kicked Ising ring at J = pi/4 (real angles, exact reference) at depth, on the schedule of flow L

Model results on the twin of ibm_kingston's 2026-10-24 calibration (Target SHA-256 3b939138…), not a device.
`fold:rule`, n = 20 on the 20-cycle of flows J-L, h = 0.6, P = 24 X-basis inputs, T = 256 trajectories, four seeds per
L; one H100 NVL. Times CET.

- **Declaration:** `prereg/drafts-2026-10-28/kising_m_note.md`, SHA-256 1f452930…b6bb (3ce7002, 05:13).
- **Run:** `run/` (`gpu/kising_m.sh`, TOQB 3ce7002, psf-zero 4346919f), 05:38:36 to 08:15:38. The check passed
  (tests/test_kising.py, 6 passed, on the pod).
- **Zip as received:** `kising_m.zip`, SHA-256 8e203d37….
- **Derived:** `analyze.py` writes `summary.txt` and `depth_figure_lm.png/.pdf` (flow L's means beside flow M's).

## Results (means of four; SE = sd of four / 2)

| L | 2Q gates | duration | lam_K | corr | lam_C (flow L) | real-angle lam (flow L) | side (declared rule) |
|---|---|---|---|---|---|---|---|
| 8 | 160 | 3.9 µs | 0.873 ± 0.001 | 1.00 | 0.860 | 0.934 | CLIFFORD-SIDE |
| 16 | 320 | 5.6 µs | 0.453 ± 0.012 | 0.93-0.98 | 0.617 | 0.818 | CLIFFORD-SIDE |
| 24 | 480 | 7.3 µs | 0.291 ± 0.007 | 0.93-0.97 | 0.392 | 0.696 | CLIFFORD-SIDE |
| 50 | 1000 | 12.8 µs | 0.084 ± 0.013 | 0.22-0.56 | 0.061 | – | – |
| 100 | 2000 | 23.4 µs | 0.046 ± 0.010 | 0.29-0.64 | −0.001 | – | – |

- **Within 2 SE:**
  - lam_K agrees with lam_C at L = 8 (0.013 against 0.017) and L = 50.
  - It is below lam_C at L = 16 and 24, and above it at L = 100 (0.047 against 0.021).
  - It differs from the real-angle lam at every L where that was measured.
- **Per-layer factor of lam_K:** 0.921 (L = 8 to 16), 0.947 (16 to 24), 0.953 (24 to 50), 0.988 (50 to 100).
  - The decay slows with depth. lam_C's per-layer factor did the opposite: 0.960, 0.945, 0.931.
- **Noiseless spread:** sd of z_exact is 0.09-0.46 at every L, so the slope is fitted at every depth. At L = 50 and
  100 the correlation is low (0.22-0.64): the kept signal is small against the trajectory noise.
- **Vanity:** a signal resolved at 2000 two-qubit gates (L = 100, 4.8 SE).
- **Essential:**
  - The real-angle kicked Ising ring keeps less than random Clifford circuits at L = 16-24, and less than half of the
    random classifier's lam.
  - Shots relative to lam = 1 are 5, 12, 141 and 474 at L = 16, 24, 50 and 100.

## Predictions against results

| declared | result | held? |
|---|---|---|
| CLIFFORD-SIDE at L = 16 | CLIFFORD-SIDE | yes |
| CLIFFORD-SIDE at L = 24 | CLIFFORD-SIDE | yes |
| L = 8 within 0.80-0.92 | 0.873 | yes |
| L = 16 within 0.50-0.72 | 0.453 | **no** (below) |
| L = 24 within 0.28-0.55 | 0.291 | yes |
| L = 50 below 0.15 | 0.084 | yes |
| L = 100: \|lam_K\| below 0.1 | 0.046 | yes |

## Not established

- **Why lam_K keeps 0.046 at L = 100 while lam_C is 0.** One candidate, untested: the Floquet step conserves fermion
  parity (the product of X), and a part of <X_0> tied to conserved quantities may decay slowly under this noise.
  This is an observation after the run; nothing about it was declared.
- **Pauli weight as the cause of the Clifford-side decay.** Plausible from the Jordan-Wigner strings, not computed here.
- **Other h, other n, a device.** Only one of each was run.
- **Advantage.** Free fermions are classically easy; this is a benchmark with a known answer.
