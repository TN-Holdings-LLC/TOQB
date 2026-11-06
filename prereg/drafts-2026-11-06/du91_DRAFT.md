# DRAFT (not declared; workplace, 2026-11-06; task X): IBM's dual-unitary chain experiment at its widths (51, 71, 91), raw, through the user entrance

Status: draft for home and the owner. Nothing is fixed. Code: `daily/du91.py` (chains, circuits, answers),
`notes/du91_2026-11-06/placement.py` (X1), `notes/du91_2026-11-06/checks.py` (X2).

## 0. What and why

- IBM (arXiv 2411.00765; home's summary, to be checked against the paper at home): ibm_strasbourg, chains of 51, 71,
  91 qubits, up to 4,095 two-qubit gates; tensor-network error mitigation, layer twirling with noise learning,
  informationally complete measurement; 262,144 shots per point; about 3 h 24 min for the 91-qubit measurement;
  checked at the dual-unitary point |J| = |b| = pi/4 against C_n(t) = cos(2h)^t (n = t, else 0), h = 0, 0.05, 0.1, 0.15.
- Here: the same circuit (SI Eq. S5, J = b = pi/4) at the same widths, written by a user in plain Qiskit, placed by
  psf-os by translation, no mitigation, no map, 4000 shots per point. Reported: how deep the raw values reach and what
  it cost, beside IBM's numbers.
- Precedent: N = 21, t <= 10, 2026-11-03 (`results/du-repro-2026-11-03`, declaration
  `prereg/drafts-2026-11-03/du_repro_note.md`): the judgements below are that note's.

## 1. Chains and placement (X1)

- A chain is the first N sites of a snake on Heron r2 labels; the shapes are tried in this fixed order, each with
  lattice2d's copies in its fixed order; the first qualifying copy of the first qualifying shape is used:

  | shape | rows / columns | copies (51 / 71 / 91) |
  |---|---|---|
  | S1 | from row 0, full width, turns at column 15 (even gaps) and 1 (odd gaps) | 3 / 2 / 2 |
  | S2 | the same from row 1 | 2 / 1 / 1 |
  | S3 | columns 1-11 (turns 11 and 1); copies also at columns 5-15 | 4 / 4 / 2 |
  | S4 | columns 3-13, the first row from column 15 | 2 / 2 / 1 |

  No other pair of turn columns holds 91 sites in eight rows (a row must give at least 11 sites plus its bridge); the
  shapes differ only in where the first row starts.
- On the device records we have (geometry and failed elements only; `notes/du91_2026-11-06/placement.json`):

  | record | 51 | 71 | 91 |
  |---|---|---|---|
  | ibm_fez 11-04 (p6, practice), 11-05 (daily, twirl) | S1 (4,0) | S3 (0,0) | S3 (0,0) |
  | ibm_marrakesh 11-04 (p6, practice) | S1 (0,0) | none | none |
  | ibm_marrakesh 11-05 (daily, twirl) | none | none | none |
  | ibm_kingston 11-03 (kim-e K manifest, with that day's registry mask) | none | none | none |

  So as of these records the experiment runs on ibm_fez only; marrakesh refuses (and has since 11-05 even for 51).
- **Finding to weigh:** fez's ring sentinel has been DEAD on the same stretch (41-43, 56, 63-67, often 36, 47, 57)
  in every fez job since 11-03 (`notes/os2d_w_2026-11-06`). The 71- and 91-site chains on S3 (0,0) run through it
  (row 2 and row 3); the on-cone value at t depends on chain sites 0..2t, so the stretch enters from t of about 12.
  A reversed chain (the same snake read from its other end) would keep the first 2t + 1 sites away from it; adding
  reversed shapes is an option, but it would be chosen knowing our own sentinel's finding (not a map, but a choice
  made after seeing a device's record): **the owner decides** whether the order is S1-S4 as above or with reversed
  shapes first.

## 2. Circuits, answers, cost (X2)

- Circuits: `gpu/practice_circuits.p4(t, pi/4, chain, h)`; h in {0, 0.05, 0.1, 0.15}; t in {4, 8, 12, 16, 20, 24}
  (24 points per width). h = 0 is the noise ruler (exact value 1 on the light cone).
- Answers: closed form (`psf_os.dual.exact`): cos(2h)^t on site t, 0 elsewhere (t <= (N - 1) / 2). Sealed as on 11-05
  (hash first), although the closed form is public.
- Checked noiseless (`notes/du91_2026-11-06/checks.json`): statevector N = 11 (t <= 5) and N = 21 (t 4, 8, 10) at all
  four h: max deviation 2.5e-13; Aer MPS N = 51, 71, 91 at t 4 and 8 (h 0 and 0.15): max 2.6e-12.
- CZ: (N - 1) / 2 for the Bell pairs + 2 (N - 1) / 2 per brickwork layer (RZZ(pi/2) as one CZ, psf-os ac84182):
  N = 91, t = 24: 45 + 90 x 24 = 2,205; CZ layers 2t + 1 = 49. Through run2d on the 11-05 fez record (user2d unchanged): t = 24 compiled CZ 1,225 / 1,715 / 2,205 and 49 CZ layers
  for N = 51 / 71 / 91, as the formula says; copies S1 (4,0), S3 (0,0), S3 (0,0).
- Jobs: one width, four h, six t = 24 user circuits = 72 circuits + 4 (ring) at 4000 shots: 87.8 s by the time model,
  over the 60 s default. Proposal: two jobs per width (h 0 and 0.05; h 0.1 and 0.15): 40 circuits, 46.6 s each;
  six jobs for the three widths, about 280 s by the model.

## 3. Judged (as 11-03), per width

1. **READS:** over the on-cone points (six t, four h), the mean squared error of <X_t> against the exact value, against
   the mean square of the exact values: READS if at most half.
2. **Decay rate:** per h > 0, R(t) = <X_t>(h) / <X_t>(h = 0) fitted as k^t (weighted least squares on ln R, over the t
   where both values exceed 3 SE); AGREES if |k - cos 2h| <= max(2 SE, 0.005), else DIFFERS.
3. **Readable depth:** per h, the largest t whose on-cone value exceeds 3 SE (reported, a number not a verdict).

## 4. Stages

51 -> 71 -> 91. A width runs only if the previous one READ (judgement 1) on the same device in the previous run; a
width that does not read stops the ladder (recorded, not retried that day). The first run may be 51 alone.

## 5. Reported (not judged)

- Off-cone values (exact 0) per t: mean and largest |value|.
- Retention per point (`notes/reporting/verdict_and_retention.md`: verdict first, retention beside, small answers
  marked).
- Beside IBM's numbers:

  | | IBM (arXiv 2411.00765, home's summary) | here |
  |---|---|---|
  | device | ibm_strasbourg | by queue (fez on the records so far) |
  | qubits | 51, 71, 91 | 51, 71, 91 |
  | two-qubit gates | up to 4,095 | up to 2,205 (t 24) |
  | shots per point | 262,144 | 4,000 |
  | wall time, 91 qubits | about 3 h 24 min | time model: 2 x 46.6 s per width (QPU model; queue not counted) |
  | mitigation | TEM, layer twirling with noise learning, IC measurement | none |
  | deepest t matched | about 45 | to be measured (expected about 20, below) |

## 6. Honest expectation

- IBM's depth is out of reach. With the chain's loss per CZ layer on 11-04 / 11-05 (FX-A: 0.007-0.013), the light-cone
  value at t falls as about exp(-0.01 x (2t + 1)) times cos(2h)^t: at t = 20, about 0.66 of the exact value at h = 0
  and less at h = 0.15; the readable depth (3 SE at 4000 shots, SE about 0.016) is expected near t of 20-24 at h = 0
  and lower at h = 0.15. These are estimates from two days of a different problem.
- For t <= 24 the on-cone value depends only on chain sites 0..2t (at most 49): the widths beyond that add gates, cost
  and off-cone checks, not physics on the cone. The claim is therefore "the same width, raw, to this depth, at this
  cost", not "the same experiment as IBM's".
- The conditions differ: device, mitigation, shots, gate set (CZ on Heron r2 against ECR on Eagle). No ranking is
  claimed.
