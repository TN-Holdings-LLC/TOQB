# Flow L (2026-10-28): the kept signal of the bare 20-ring at depth, by Clifford eigenstate circuits, with a real-angle bridge

Model results on the twin of ibm_kingston's 2026-10-24 calibration (Target SHA-256 3b939138…), not a device.
`fold:rule`, n = 20 on the 20-cycle of flows J and K, P = 24 circuits, T = 256 trajectories, one H100. Times CET.

- **Declarations:**
  - `prereg/drafts-2026-10-28/clifford_lam_note.md`, SHA-256 1afcd16b…e330 (8904b2e, 00:51);
  - `clifford_lam_amend1.md`, SHA-256 dadc1d87…5a73 (df31d31, 02:32): the bridge at L = 24.
- **Runs:**
  - `main/` (`gpu/clifford_l.sh`, TOQB 8904b2e, psf-zero 4346919f): 01:12:11 to 03:25:46. The check passed: n = 20,
    L = 16, model 0 gave lam 0.84549, equal to flow J.
  - `amend1_L24/` (`gpu/clifford_l24.sh`, same code): 03:26:26 to 04:40:50.
- **Zips as received:** `clifford_l.zip` SHA-256 9a46d60a…; `clifford_l24.zip` a76278e9….
- **Derived:** `analyze.py` writes `depth_data.csv` and `summary.txt` from the raw rows. `depth_figure.py` draws
  `depth_figure.png/.pdf`; it is the workplace's figure, revised at home.

## Results (means of four; SE = sd of four / 2, as declared)

| L | 2Q gates | duration | real-angle lam | Clifford lam_C | ratio | bridge |
|---|---|---|---|---|---|---|
| 8 | 160 | 3.9 µs | 0.934 ± 0.008 | 0.860 ± 0.008 | 0.92 | DIFFER (0.074 > 0.023) |
| 16 | 320 | 5.6 µs | 0.818 ± 0.020 (flow J) | 0.617 ± 0.008 | 0.75 | DIFFER (0.201 > 0.044) |
| 24 | 480 | 7.3 µs | 0.696 ± 0.012 | 0.392 ± 0.007 | 0.56 | DIFFER (0.304 > 0.027) |
| 50 | 1000 | 12.9 µs | not fitted | 0.061 ± 0.010 | – | – |
| 100 | 2000 | 23.5 µs | not fitted | −0.001 ± 0.004 | – | – |

Durations are those of the real-angle circuits; the Clifford circuits are 0.06 µs longer because of the prep layer.

- **Per-layer factor:**
  - lam_C: 0.960 (L = 8 to 16), 0.945 (16 to 24), 0.931 (24 to 50);
  - real angles: 0.984 (8 to 16), 0.980 (16 to 24).
- **Shots relative to lam = 1 (1/lam²):**
  - real angles: 1.15, 1.49, 2.06 at L = 8, 16, 24;
  - Clifford: 1.4, 2.6, 6.5, 266 at L = 8, 16, 24, 50.
- **Vanity:** lam about 0.70 at 480 two-qubit gates (L = 24).
- **Essential:**
  - On this twin, the real-angle lam of random classifiers falls about 2% per layer to L = 24.
  - The Clifford test reaches deeper. It gives 0.06 at L = 50 and nothing resolved at L = 100 (|mean| < 0.01).
  - It sits below the real-angle lam by a ratio that falls with depth, so it says little about the real-angle lam at
    L ≥ 50.

## Predictions against results

| declared | result | held? |
|---|---|---|
| AGREE at L = 8 | DIFFER, ratio 0.92 | **no** |
| lam_C decreases with L | 0.860, 0.617, 0.392, 0.061, −0.001 | yes |
| lam_C(100) more than 2 SE above 0 | −0.001 ± 0.004 | **no** |
| amend. 1: DIFFER at L = 24 | DIFFER | yes |
| amend. 1: real lam 0.66-0.80 | 0.696 | yes |
| amend. 1: lam_C 0.30-0.48 | 0.392 | yes |
| amend. 1: ratio 0.40-0.70 | 0.563 | yes |

**Declared reading of the L = 24 ratio:** below 0.70, so at depth lam_C is only a lower side, not a near guide to lam.

## Not established

- **Lower bound.** lam_C < lam was seen at three depths (L = 8, 16, 24), not shown in general.
- **The real-angle lam at L ≥ 50.** A factor of 0.98 per layer would give about 0.4 at L = 50, but that is an
  extrapolation.
- **Why lam_C decays faster and not at a fixed rate.** Two candidates, neither tested:
  - Pauli weight: U†Z0U is spread over many qubits, so the noise acts on more of them.
  - The real-angle slope may be carried by low-weight parts of the output.
- **Anything about n.** Only n = 20 was run.
- **Anything on a device.**
- **Classical hardness.** Clifford circuits are classically easy, and every set here took 1-15 min on one GPU.
