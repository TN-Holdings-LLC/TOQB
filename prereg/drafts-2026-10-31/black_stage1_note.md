# Black stage 1: where does the signal of kingston's dead run go? (home, 2026-10-31; declared on the owner's go of 2026-10-31 13:22 CET; the design of `coherent_stage1_DRAFT.md` with its open items settled)

**Why.** On 30 October the rule's n = 40 echo ring on ibm_kingston had an 18-site dead run (qubits 3-7, 17, 27-29, 38,
49-55, 59), three times with the byte-identical circuit. Its second block (38, 49-55, 59) was *inverted* (raw signal
-0.214 at D = 24, options test, off): the echo returned the wrong bit more often than the right one. Gate twirling
turned that block into a random one (+0.015) and dynamical decoupling did almost nothing (-0.192). The error there is
coherent, and it is not idle crosstalk. Twirling does not bring the information back; it only makes it random. Before
trying to undo the error (stage 2: a counter-rotation), we must know where the signal went. Read in Z only, a turned
signal and a lost signal look the same.

**31 October.** The same 18 qubits were dead again on the n = 40 standard ring (coverage day 1, job A, 11:40 CET;
the fourth run of the byte-identical circuit), so this defect stays put (black). A weak stretch elsewhere came and
went within 90 minutes (gray stage 1). The owner: test the operation on black, where an effect will be clear; this
job is the diagnosis that gives the operation (stage 2) its axis and angle.

**What is already known (30 October, post hoc, not judged here).** Block 38-59, Z, rerun (hz 0, 0.1, 0.3 averaged):
-0.094 at D = 24, -0.047 at D = 50, 0.000 at D = 100; the rest of the ring +0.429, +0.005, +0.001. Connected ZZ
correlation of neighbour pairs at D = 24 (hz 0): inside the dead run 0.154, healthy pairs of the same ring 0.315 (sd
0.027), the n = 20 ring 0.289. Healthy pairs are strongly correlated because the echo spreads its own errors (Lemma 2),
so the dead run is *less* correlated in ZZ than healthy pairs, not more. Only Z was read.

**Simulator check of the reading (n = 8, error after every CZ on qubits 3 and 4; `results/echo-tomo-validation-2026-10-31`).**
- A coherent one-qubit turn (RX) keeps the vector length; the Z signal falls slowly; ZZ correlation as elsewhere.
- A coherent two-qubit error (RZZ) shrinks the one-qubit vector like loss does (the signal goes into the pair), makes
  the Z signal over depth non-monotone (at 0.3 it changes sign), and raises the pair's connected ZZ correlation far
  above the other pairs (0.736 against 0.212 at 0.15; 0.616 against 0.107 at 0.3).
- Depolarising loss shrinks the vector, falls monotonically with depth, and leaves the pair's correlation as elsewhere
  (0.199 against 0.210).
- So the vector length alone cannot separate a two-qubit coherent error from loss. The depth curve and the pair
  correlation can. The design below judges all three.

**Design (one job, ibm_kingston, after this note is fixed and after a new fetch).**
- Rule only (`fold:rule`), map-free. The rule's mirror echo, hz = 0, h = 0.6, 4 inputs and 4 references, 1000 shots.
- n = 40 (the ring that holds the dead run): Z at one-way L = 1, 2, 3, 4, 6, 8, 10, 12 (D = 2 ... 24); X and Y at
  L = 6 and 12 (D = 12, 24). The X/Y records are the same circuits with a basis change before each echo measurement
  (X: RZ(pi/2) SX RZ(pi/2); Y: SX RZ(pi/2)); two-qubit gates unchanged; references stay in Z.
- n = 20 (control, no dead run on 30 October): Z at L = 6 and 12; X and Y at L = 12.
- 16 records, 128 circuits; predicted 42.2 s (time model). Built by `gpu/coherent_stage1.sh` (dry run on the 30 October
  14:02 fetch: all 16 records accepted, one ring per size, the n = 40 D = 24 Z circuit byte-identical to 30 October,
  QPY SHA-256 42376e3f...; manifest written).
- Options off (no DD, no twirling). The day's fetch unmasked: the rule's standard ring (the one holding the dead
  run). Nothing in the circuits is chosen from data; only which qubits are scored as the block comes from it.
- If the day's n = 40 D = 24 Z circuit is not byte-identical to 30 October's, that is reported and the job is still
  run.

**Scored units (fixed with this note).** Block B (judged) = qubits 38, 49, 50, 51, 52, 53, 54, 55, 59. Block A
(reported) = 3, 4, 5, 6, 7, 17, 27, 28, 29. Rest = the n = 40 ring minus both blocks (22 sites). Per site the
sign-aligned component a_j = mean over the 4 inputs of (-z_in,j) <P_j>, P = X, Y or Z. The inputs are balanced per
site, so any fixed readout bias (T1, leakage) cancels; with contracting noise alone a_j stays >= 0.

**Precondition P0.** A dead run (>= 3 consecutive ring sites below 0.12, Z, D = 24) holds at least 2 of the listed path
[28, 29, 38, 49]. If not: the defect is ABSENT that day; nothing below is judged; all values are reported.

**Judged (`python -m toqb.echo_tomo score`).**
- **J1, depth (primary):** block B's mean Z signal at D = 2 ... 24; signs of values beyond 2 SE in depth order.
  OSCILLATES (+ - +: a turn that comes back; a periodic coherent error, its period gives the angle per layer);
  CROSSES ONCE (+ -); STARTS INVERTED (already negative at the first depth beyond 2 SE); NO CROSSING.
- **J2, vector length at D = 12:** block B's mean |v| (from X, Y, Z) against the rest's. KEPT (>= 0.8 x rest: the
  signal was turned on each site); SHRUNK (< 0.5 x rest); MIXED otherwise.
- **J3, pair correlation at D = 12:** mean connected correlation |<P_a P_b> - <P_a><P_b>| of the 8 neighbour pairs
  inside block B, in X, Y and Z, against the rest's pairs (both ends outside the dead run). ENTANGLED if, in any of
  the three bases, block B exceeds the rest's mean by more than 3 x (sd / sqrt(#pairs)) and by at least 0.05; NOT SEEN
  otherwise.
- **Control:** the n = 20 ring's |v| and Z signal at D = 12 and 24, reported against 30 October (+0.364 at D = 24).

**One sentence per outcome (fixed in advance; nothing else is concluded from this job).**
- J2 KEPT: the signal was turned, not lost, on each site; stage 2 is a per-site counter-rotation with the axis and
  angle read from the D = 12 vector.
- J2 SHRUNK and J3 ENTANGLED: the signal went into the block's neighbour pairs; stage 2 needs a two-qubit counter-gate
  on the block's couplers, with the angle from J1 if it OSCILLATES.
- J2 SHRUNK and J3 NOT SEEN: the signal left what we can read (lost, or spread beyond neighbour pairs); a
  counter-rotation is not expected to help; stage 2 is not run and the path stays on the defect list.
- J2 MIXED: reported; stage 2 only by the owner's decision.
- J1 is reported with each sentence: OSCILLATES gives the counter-rotation's angle per layer; the others say the angle
  is not readable from depth alone.

**Reported, not judged.** Block A with the same numbers; D = 24 for J2 and J3; the full per-site table of all 16
records; the job's billed time. |v| from three noisy components is biased up by shot noise (about 0.02 at 1000 shots);
the same bias applies to block and rest.

**Stop.** One job. The cause of the coherent error is not pursued; stage 2 is a separate note.

**Settled (owner, 31 October: "あとは任せる").** Block B judged, block A reported; L = 1-12; n = 20 control (its ring
shares 3-7, 17, 27 with block A, reported); thresholds as above; a job of its own (not with coverage days).
