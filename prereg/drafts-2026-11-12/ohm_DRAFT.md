# DRAFT (not declared): where Ohm's law appears, raw, 6 cycles (Heron)

Workplace, 2026-11-12 (home's instruction of 02:05 CET; owner 09:58 JST: 6 cycles). To be fixed by home and the owner:
renamed `prereg/ohm_YYYY-MM-DD.md` (the run date), the open settings below filled from the design scan, committed and
pushed before any device record of the run is fetched. Paper 9 or its own note.

## Question

On a 40-qubit chain, after 3 and 6 cycles of an fSim(pi/4, phi) brickwork from a weakly polarised wall, does the device
read the transferred magnetization of each circuit, and does the growth from 3 to 6 cycles keep the exact ordering of
the three arms: free (ballistic), interacting integrable (superdiffusive), interacting with a period-3 field (diffusive,
the Ohmic t^(1/2) in linear response; home 11-12)?

## Circuits (`gpu/ohm_answers.py`, `gpu/ohm_build.py`)

- N 40 qubits on one chain, logical qubit k on chain label k. Start: a product state, qubit k |1> with probability
  (1 + m)/2 on the left half and (1 - m)/2 on the right half; K strings drawn with a declared seed, each with its
  complement (the mirrored wall: the left leans to |0>). The same 2K strings in every arm and cycle count.
- Cycle: fSim(pi/4, phi) on bonds (0,1), (2,3), ..., then on (1,2), (3,4), ...; arms
  - A0: phi 0 (free fermions);
  - A1: phi pi/2 (isotropic);
  - A2: phi pi/2, then RZ(H p_k) on qubit k after each cycle, p = (1, -1, 0) repeating, H 1.
- Cycles 3 and 6. Try-build on the 11-11 ibm_fez record (`results/hubbard-big-2026-11-11/fetch_in/ibm_fez/dev`), one
  string pair: chain by shape S1; CZ (CZ layers) A0 234 (12) / 468 (24), A1 and A2 351 (18) / 702 (36) at 3 / 6
  cycles; A1 and A2 equal in CZ count and depth (the builder refuses otherwise); 6 cycles stay under the 48 CZ layers
  that read on 11-11 (Hubbard 4 steps), below the 72 that did not.
- Each circuit with its floor and mirror (mirror: compiled circuit, barrier, its inverse, as gpu/hub_build), one ring
  sentinel; S shots.

**Open (from the design scan):** m, K, S. With the time model (0.036 s + 0.00027 s per shot per circuit, 3 s per job)
and 160 s, the job holds 3 arms x 2 cycle counts x 2K strings x 3 circuits + 4: K 14 at S 1000, K 24 at S 500.

## Device and placement (no quality number)

As prereg/hubbard_2026-11-11.md: right before the fetch, pending jobs of ibm_marrakesh, ibm_fez, ibm_kingston; in the
order of fewest pending (ties: that order), the first device on which the job builds. Chain: daily/du91 shapes first,
psf-os rule C if none qualifies.

## Answers (sealed)

`gpu/ohm_answers.py`: per-qubit <Z> of every circuit, A1 and A2 by quimb CircuitMPS (cutoff 1e-12, cap 2048), A0 by
free fermions (exact at any size). Held outside the repository until the verdicts; its sha256 is written here before
the push. Checks (printed, no values): largest bond below the cap, quimb's error estimate, total Z equal to its
initial value, A0 by quimb against free fermions on the first strings.

## Pre-run check (before submission): `gpu/ohm_check.py OUT ANS`

On the job's own compiled circuits, every circuit: 3 cycles by Aer's MPS without truncation, 6 cycles by quimb, per-qubit
<Z> within 1e-6 of the answers; every mirror all zeros; A1 and A2 equal in CZ count and depth. FAIL anywhere: not run.

## Verdicts (`gpu/ohm_score.py OUT ANS`)

The measure is the transferred magnetization of each circuit, M = (count of |1> on the right half at the end) - (at the
start), in quanta, from the per-qubit <Z>: the quantity the question is about, exact per circuit, so the device is
compared with the exact value of the same string and the spread between strings is not part of the comparison.
Per arm and cycle count, over its 2K circuits: READS if the mean squared difference of M is at most half the mean
square of the exact M; AGREES counted per circuit, |M_device - M_exact| <= 0.2 quanta (about three shot errors of one
circuit at 1000 shots).

Beside, never judged, never used to correct: W(t) = mean of (M_s - M_c)/2 (string minus complement) and its exponent
log2(W(6)/W(3)) per arm, device and exact; the drift D(t) = mean of (M_s + M_c)/2 (decay towards |0> lowers both); the
per-qubit <Z> verdict of every circuit; floor, mirror, sentinel, CZ.

## Prediction (before any data; not rewritten if wrong)

- Every arm READS at 3 cycles; at 6 cycles (36 CZ layers for A1 and A2) READS for A0 and A1, A2 open (to be written).
- The device's exponents keep the exact ordering A0 > A1 > A2. **Open:** the design check (workplace, N 40, K 30) found
  the exact A1 - A2 gap of the K-string mean far smaller than in linear response (m 0.5: 0.66 against 0.61) and below
  the shot error a 160 s job reaches (ratio 1.0 at 1000 shots), while A0 against A1 (about 0.4) is well resolved. Unless
  the design scan finds a setting with a gap at least three times the shot error, the prediction should name only
  A0 > A1 and A0 > A2, with A1 against A2 beside.

## Limits

One device-day; raw values only; 40 qubits, inside the exact computation; finite bias and K strings, so the exponents
are those of these strings, not the linear-response values; noise mixes spins and so looks like extra transport: the
comparison is with the exact M, and W cancels the decay drift only to first order.
