# Ohm's law on the device, 6 cycles: design check, tools, try-build (workplace, 2026-11-12; not declared)

Home's instruction of 02:05 CET (owner 09:58 JST: 6 cycles; 8 cycles and POD put aside). Desk work and a declaration
draft only; no device, IBM, GitHub or POD from here.

## 1. Design check (`notes/ohm_2026-11-11/samples6w.py`; outputs `design6_N40_m0.5.txt`, `design6_N40_m0.3.txt`)

samples6w.py is samples6.py (home, first run here) plus: A0 against free fermions per string, the per-shot variance of
the right-half count measured by sampling the MPS (5 strings, 400 shots) beside the independent-site bound, the shot
error of the exponent and of A1 - A2, and a bootstrap over strings. Smoke run N 12, K 3: free fermions 3.4e-8 (cutoff
1e-10). N 40, K 30 (design strings, seed 11), exponent of the mean M from 3 to 6 cycles:

| m | A0 | A1 | A2 | A1 - A2 | shot error of A1 - A2 at 500 / 1000 / 2000 / 4000 shots | ratio at 1000 |
|---|---|---|---|---|---|---|
| 0.5 | 1.051 | 0.660 | 0.609 | 0.050 | 0.072 / 0.051 / 0.036 / 0.025 | 1.0 |
| 0.3 | 1.054 | 0.673 | 0.615 | 0.059 | 0.123 / 0.087 / 0.062 / 0.044 | 0.7 |

- The criterion (gap at least three times the shot error) is met by **no** setting reachable in one 160 s job: even
  4000 shots per circuit give 2.0 (m 0.5) and 1.3 (m 0.3), and a 160 s job holds only K 14 at 1000 shots.
- The gap itself is small at these K: 0.05-0.06 against 0.21 in linear response (home: 0.71 / 0.50). The resample
  spread over strings is 0.05 (m 0.5) to 0.08-0.12 (m 0.3) per arm, so at K 30 the gap of these strings is not the
  ensemble's; whether finite m itself closes the gap needs many more strings (the POD scan below).
- A0 against A1 (about 0.39) is resolved at every setting (ratio about 8 at m 0.5, 1000 shots).
- The shot errors use the independent-site bound of the per-shot variance; sampling gave about 0.15-0.2 of it
  (anticorrelation from the conserved count), so the true shot errors are about 0.4-0.45 of those listed. Even then
  A1 - A2 reaches only about 2.4 x at m 0.5, 1000 shots.
- Signal: M after 3 / 6 cycles, A0 0.80 / 1.66, A1 0.62 / 0.98, A2 0.44 / 0.68 quanta at m 0.5 (0.49 / 1.01, 0.39 /
  0.62, 0.28 / 0.43 at m 0.3). m 0.5 doubles the signal against the same shot noise; the exponents barely move.
- Cost: A1 / A2 at 6 cycles reach bond 1300-1360 (cap 4096) and 15-35 s per string here (with the MPS sampling).

**Proposal:** m 0.5, K 14 strings and their complements, 1000 shots (508 circuits, 158.5 s by the model), cycles 3 and
6; the prediction names A0 > A1 and A0 > A2 only, with A1 against A2 beside; unless the POD scan (VS) finds a setting
(arm, window, m) whose gap is at least three times the shot error.

## 2. Tools (`gpu/ohm_answers.py`, `ohm_build.py`, `ohm_check.py`, `ohm_score.py`; the form of the hub_* tools)

- `ohm_answers.py`: strings (K, m, seed; each with its complement), the logical circuit (fSim as a two-qubit unitary;
  RZ(0) left out), per-qubit <Z> by quimb (A1, A2) and free fermions (A0); values only to the file; printed checks:
  bond, error estimate, total Z against its initial value, A0 quimb against free fermions.
- `ohm_build.py`: the chain (hub_build.chain_of), every arm x cycles x string through user2d.build_batch with the
  compiled-circuit mirror (hub_build), answers by chain label; refuses if A1 and A2 differ in CZ count or CZ depth, or
  if the strings regenerated from the seed differ from the answers file's.
- `ohm_check.py`: compiled circuits reduced to the chain, Aer MPS (3 cycles) or quimb (6 cycles) against the answers
  (1e-6), mirrors all zeros, A1 / A2 equal.
- `ohm_score.py`: the measure M per circuit in quanta (why: the quantity of the question, exact per circuit, so the
  string spread is not in the comparison); READS (MSE <= half the mean square of the exact M), AGREES |dM| <= 0.2
  quanta (about three shot errors of one circuit at 1000 shots); beside: W = mean (M_s - M_c)/2 and its exponent, the
  drift D = mean (M_s + M_c)/2, the per-qubit verdicts, floor, mirror, sentinel.
- End-to-end test (`fake_counts.py`, a test helper: per-qubit bits sampled from the exact <Z>, floors and mirrors all
  zeros, a perfect sentinel): one string pair on the 11-11 fez record, every arm and cycle count READS, AGREES 2/2,
  W within shot noise of the exact. (The first fake put the bits in chain order; the user entrance measures clbit k on
  the k-th sorted label; fixed in the helper, the scorer was right.)

## 3. Try-build and pre-run check (11-11 ibm_fez record, `results/hubbard-big-2026-11-11/fetch_in/ibm_fez/dev`)

One string pair (seed 999): chain by shape S1; CZ (CZ layers) A0 234 (12) / 468 (24), A1 = A2 351 (18) / 702 (36);
12 user circuits, 40 circuits, 15.2 s at 1000 shots. Pre-run check: ALL PASS (Aer MPS 3 cycles: worst 3.7e-11; quimb
6 cycles: worst 9.0e-11 for A0, 1.4e-14 for A1 / A2; mirrors at most 4.9e-14). The full proposal: section 4.

## 4. The proposal built (no answers yet)

- Full try-build of the proposal (m 0.5, K 14 and complements, seed 20261112, 1000 shots) on the same record, with an
  all-zeros test file in place of the answers: chain S1; 168 user circuits, 508 circuits with floors, mirrors and the
  sentinel, 158.4 s by the model (under 160); A1 and A2 equal in CZ and CZ depth for all 28 strings and both cycle
  counts (351 / 702 CZ, 18 / 36 layers); A0 234 / 468 (12 / 24).
- Answers for it were started (cutoff 1e-12, cap 2048) and **stopped under the 1-minute rule**: A0 (free fermions,
  checked against quimb 1.0e-11) and A1 at 3 cycles took seconds, but A1 at 6 cycles reached bond 914 and 104 s for its
  slowest string (664 s for 28). N and cycles are as home's (40, 6); the difference from home's 4 s is the cutoff
  (1e-12 here, 1e-10 in samples6.py) and the design run sharing the two cores. Not continued: the answers depend on
  m, K and the seed, which wait for the design scan; they are cheap on a POD or at home (`gpu/ohm_answers.py`, about
  10-20 min on one core at cutoff 1e-12).

## 5. The POD design scan (VS, 11-12 03:38-04:36 CET; `pod_design/`) and why it disagreed with section 1

VS's scan (N 40, K 100 and complements, m 0.2 / 0.3 / 0.5, six arms, four windows) found A1 - A2 about 0.25 in the
exponent of W from 3 to 6 cycles (m 0.5: 0.696 against 0.446), where section 1 had 0.05. Checked here against the scan's
own rows (`P1_design.jsonl`, which keeps the plain mean M beside W and W per string):

- **The two scripts make the same circuits.** Both draw the strings from seed 11 in the same order and insert the field
  the same way (RZ(H p_k) after each cycle; samples6w applies RZ(0) on the zero sites, design_pod leaves them out).
  On the first 30 strings the scan's W exponent equals section 1's for A0 (1.051) and A1 (0.660) to three digits; for
  these arms W and M coincide (the scan's M and W exponents are equal for A0, A1, B1, B2).
- **The difference is the estimator.** Section 1 used the plain mean M of the strings; the scan, W = (M_s - M_c)/2
  with the complement. For A2 they differ: m 0.5, K 100, M 0.610 against W 0.446 (section 1: M 0.609 at K 30); also
  A2h2. Reason: the complement turns the period-3 field (1, -1, 0) into (-1, 1, 0), so a string and its complement do
  not see mirror-image dynamics and M carries a part even in m; W keeps the part odd in m, the transport, and comes
  near the linear-response 0.50 (home). Without the field (A0, A1) or at phi = pi (B1, B2) the complement is an exact
  mirror and M = W.
- So section 1's conclusion (A1 and A2 not separable) was about M and is withdrawn for W; the job's comparison is W.

With W and the proposal (m 0.5, K 14 and complements, 1000 shots), from the scan's rows: A1 - A2 gap 0.250, shot error
of the gap 0.050 by the independent-site bound (ratio 5.0, criterion 3; with the sampled variance about 0.45 of the
bound, about 11); among 2000 random 14-string subsets of the 100, the exact gap was positive in all (mean 0.250, sd
0.058). At m 0.3 the ratio is 3.0 (bound) and 0.997 of the subsets keep the sign; at m 0.2, 2.0 and 0.956. So m 0.5.
B1 (phi pi) sits 0.13 below A1: not separable at this size; not an arm.
