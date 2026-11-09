# Schwinger model candidates (VS Claude, 2026-11-09 05:52-07:23 CET; workplace review; not declared, no device)

Instruction: `指示書_シュウィンガー_2026-11-09.md` (and `VSクロードへ_参考_シュウィンガー比較_2026-11-09.md`); VS's
results in `vs/` (zip sha256 47cafaae..., checked). No site-by-site exact value or nu value is written anywhere here
(only root-mean-square sizes to 2 decimals, nu bands of width 0.05, agreement deviations and model MSEs), so a later
declaration can still seal its answers.

## What was built

Kogut-Susskind staggered fermions, open boundary, gauge field eliminated, Jordan-Wigner (Martinez et al., Nature 534,
516 (2016), eq. 1); parameter sets M1 (J = w, m = 0.5 w), M2 (J = w, m = 0), M3 (J = 2 w, m = 0), eps0 = 0, from the
paper's figures 2(a) and 3. Bare vacuum, first-order Trotter, dt = 0.25 / w fixed before any answer, steps 1-8. All
pairwise ZZ by a swap network (N layers per step, reversed on even steps); each gate SWAP . exp(-i dt (A ZZ + hopping))
in 3 CX. Chains by du91's shape rule first, rule C only if none: N <= 12 always took shape S1 at (0, 0) on fez,
kingston and marrakesh (rule C not needed). Through `psf-os run2d` offline: 160 circuits (fez M1-M3, kingston and
marrakesh M1; N 6 / 8 / 10 / 12; steps 1-8), all accepted, CZ = 3 N (N - 1) / 2 per step exactly, compiled = exact
to 4.2e-13.

## Review (workplace)

- **Readout order.** run2d reads the touched qubits in label order (clbit k = k-th label), not the user's classical
  bits; after an odd number of swap-network steps the sites are reversed. VS found it and fixed the site map; a
  declaration must give the answers per label (clbit) or seal the site map with them. Any user circuit that permutes
  its qubits meets this.
- **Cost.** CZ per qubit grows like N: 33 at N = 12 for one step, as much as a whole du-stage2 circuit (528 CZ, 32 per
  qubit, read on kingston 11-03). The comparable sizes are N = 6 at 2 steps (90 CZ, 30 per qubit) and one step of N 8-12.
- **Uniform fixed model** (not fitted): beats both trivial guesses (vacuum, all 0) at steps 1-5 for every N, loses at
  6-8. Steps 3-4 sit near 0 (an all-0 guess is close), step 1 near the vacuum: weak tests. Steps 2 and 5 are the
  informative ones. The uniform model was optimistic before for Heisenberg (15-28 %), so steps 5 at N >= 8 (105-165 CZ
  per qubit) are unlikely to read on a device.
- **Trivial guesses.** The vacuum (staggered +-1) is the natural trivial guess here, not judge's all-0 / all-1; a
  declaration should put the vacuum guess beside READS / BEATS.
- Label note: the table's "二乗平均 <Z>" is the root mean square (its square is the all-0 guess's MSE).

## A candidate set for a declaration (proposal only; the owner decides)

N = 6 and 8, steps 1, 2 and 5, M1-M3 (18 circuits; CZ 45-420), shape S1 on any of the three devices; answers per
label, sealed; READS / BEATS (judge) plus the vacuum guess beside; nMSE as the main measure.
