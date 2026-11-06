# DRAFT (not declared; workplace, 2026-11-06 CET; task X as narrowed by the owner at 01:37 CET): IBM's dual-unitary chain experiment at N = 51, raw, through the user entrance

Supersedes `du91_DRAFT.md` for what is to be run: the owner chose N = 51 and set 71 and 91 aside (for t <= 24 the
light-cone value depends only on chain sites 0..2t, at most 49; a wider chain would add numbers, not content).
Code: `daily/du91.py` (chains, circuits, answers; N = 51 is one of its widths), `notes/du91_2026-11-06/`.

## 0. Claims (and only these)

1. IBM's problem (arXiv 2411.00765), the same circuit at the dual-unitary point, run with no error mitigation and no
   map, from psf-os's user entrance (`psf-os run2d`), placed by translation.
2. Whether the raw decay rate matches cos 2h, and the readable depth for each h.
Not claimed: IBM's depth, IBM's widths, any ranking against IBM.

## 1. The problem

- Open chain of N = 51 sites; |+> on site 0, Bell pairs on (1, 2), ..., (49, 50); t brickwork layers (even pairs first)
  of U (SI Eq. S5) with J = b = pi/4; X readout of every site. User circuit: `gpu/practice_circuits.p4(t, pi/4, chain,
  h)`, written in plain Qiskit on Heron r2 labels.
- h in {0, 0.05, 0.1, 0.15}; t in {4, 8, 12, 16, 20, 24} (24 points). h = 0 is the noise ruler (exact 1 on the cone).
- Exact answer (closed form, `psf_os.dual.exact`): <X_t> = cos(2h)^t on site t, 0 elsewhere (t <= 25). Sealed as on
  2026-11-05 (hash committed first). Checked noiseless: statevector N = 11, 21 (2.5e-13) and Aer MPS N = 51 at t 4, 8
  (2.6e-12) (`notes/du91_2026-11-06/checks.json`).
- CZ: 25 + 50 t (t = 24: 1,225; 49 CZ layers), as compiled by run2d on the 11-05 fez record.

## 2. Placement and device

- Chain shapes in the fixed order of `daily/du91.SHAPES` (S1-S4), each with lattice2d's copies in their fixed order;
  the first qualifying copy of the first qualifying shape. No other placement step.
- Device: by the queue, as the daily record (pending jobs only; ties marrakesh, fez, kingston). **A device on which no
  shape qualifies is not used** (the next one by the queue; if none, no run that day).
- On the records so far only ibm_fez qualifies (S1 at (4,0): rows 4-7, labels 80-155); marrakesh (11-05) and kingston
  (11-03) do not. The chain does not touch fez's persistently DEAD sentinel stretch (rows 2-3); note that it is also
  outside the ring sentinel's path (rows 0-3), so the sentinel says nothing about the chain's rows.

## 3. Jobs

- 24 user circuits, each with its floor and mirror, + the ring: 76 circuits, 87.8 s by the time model (over 60 s).
  Two jobs back to back, h {0, 0.05} and h {0.1, 0.15}: 40 circuits, 46.6 s each; 4000 shots; options off; `--out`
  relative.

## 4. Judged (the 2026-11-03 declaration's judgements)

1. **READS:** over the 24 on-cone points, the mean squared error of <X_t> against the exact value, against the mean
   square of the exact values: READS if at most half.
2. **Decay rate**, per h > 0: R(t) = <X_t>(h) / <X_t>(h = 0), fitted as k^t (weighted least squares on ln R, over the t
   where both values exceed 3 SE); AGREES if |k - cos 2h| <= max(2 SE, 0.005), else DIFFERS (k, SE, cos 2h reported).
   If fewer than two t qualify for an h: NOT TESTED for that h.
3. **Readable depth**, per h: the largest t whose on-cone value exceeds 3 SE (a number, not a verdict).

## 5. Reported (not judged)

- Off-cone values (exact 0): mean and largest |value| per t.
- Retention per point, with the declared verdicts first (`notes/reporting/verdict_and_retention.md`).
- The sentinel as declared and beside the ring ledger (report only; `sentinel_ledger_DRAFT.md`).
- Beside IBM:

  | | IBM (arXiv 2411.00765) | here |
  |---|---|---|
  | device | ibm_strasbourg (ECR gates) | by queue; ibm_fez on the records so far (Heron r2, CZ) |
  | qubits | 51, 71, 91 | 51 |
  | two-qubit gates | up to 4,095 (N = 91) | up to 1,225 (t 24) |
  | shots per point | 262,144 | 4,000 |
  | wall time | about 3 h 24 min for N = 91, with noise learning and mitigation | two jobs of 46.6 s by the time model (queue not counted) |
  | mitigation | tensor-network error mitigation, Pauli twirling with noise learning, Clifford-point calibration, informationally complete measurement, readout mitigation | none |
  | unmitigated values | shown in Fig. 2 (circles, with the fitted unmitigated decay rates, dotted) and Fig. 1(e) (N = 91, h = 0.1); no numbers in the text ("decays quicker with t than the exact evolution") | the whole record |

  IBM's unmitigated points are given only as plotted symbols: they are not copied as numbers here. If the owner wants
  them in the table, they would have to be read off the figure (an approximate digitisation, marked so).

## 6. Honest expectation

- With the chain's loss per CZ layer seen on 11-04 / 11-05 (FX-A 0.007-0.013), the h = 0 cone value at t = 24 is about
  exp(-0.01 x 49) = 0.61 of exact; the readable depth (3 SE, SE about 0.016) is expected at or near t = 24 for h = 0
  and lower for h = 0.15 (exact 0.955^24 = 0.33 before loss). Estimates from two days of a related problem.
- The decay-rate test divides by the h = 0 ruler: a common loss cancels; a loss that depends on h does not.
- A device other than fez may not be usable on a given day; then the day has no run.
