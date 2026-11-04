# Declared: practice problems through the user entrance (owner's go of 2026-11-04 12:07 CET (B) and 12:23 CET (1))

The question: a user writes known problems as plain circuits and hands them to psf-os (`psf-os run2d`, batch); how
far can the answers on the card be read, without correction (the correction test is on hold, owner 12:04 CET)?

## Problems (answers sealed before tonight: du_bank b937d47e..., P5 bank b3a2a864... and 7a792490...)

- P4 kicked Ising chain (arXiv 2411.00765, SI Eq. S5): N = 33, h = 0.15, J = pi/4, b = pi/4 - 0.05 and pi/4 - 0.3,
  t = 2, 4, 8, 12, 16; X readout. Chain on labels 0..15, 19, 35..20. (10 circuits)
- P5 kicked Ising on the marrakesh lattice of the bank (151 qubits, 166 edges): RZZ(-pi/2) on every edge then
  RX(theta), theta = 0.4, 0.8, 1.0, t = 2, 4, 6, 8; Z readout. (12 circuits)
- Written as a user, in plain Qiskit (rz, rzz, rx, h, cx), by `gpu/practice_circuits.py` (no psf-os code), not by the
  OS's own problem modules.

## Checks done before this note (CPU, no device)

- The user circuits against the sealed answers: P4 t 2, 4, 8 (matrix-product state, whole chain) max 1.4e-5; P5 t 2,
  3 (causal cones, statevector) max 1e-15.
- Compiled by `psf-os run2d` (psf-os ac84182) on tonight's marrakesh record, noiseless: P4 t 4, 8 max 1.4e-5; P5 t 2
  (cones) 7e-16. CZ per circuit as the problems need (P4: 16 + 2 per gate; P5: 166 per step), after the fix of
  ac84182 (RZZ(+-pi/2) as one CZ; before it, two).

## Device and job

- ibm_marrakesh (the P5 lattice is marrakesh's). Fetched by `psf-os fetch` (coupling graph and failed elements only).
- One batch job by `psf-os run2d --circuit <22 files> --max-seconds 100`, psf-os ac84182: each circuit placed on its
  own by `lattice2d.place`, with its own floor and mirror; one ring sentinel; 4000 shots; no correction, no mitigation.
- If the entrance refuses any P5 circuit (a new failed element under the lattice), the 10 P4 circuits go alone and
  P5 is NOT TESTED. If it refuses a P4 circuit, no job.

## Judged (per circuit; scorer `gpu/practice_score.py`, fixed with this note, reading the entrance's own cards)

1. **READS:** MSE over the answered qubits <= half the mean square answer.
2. **AGREES:** |M - M_exact| <= 0.05 (M over the answered qubits).
3. **BEATS:** MSE below the better trivial guess (every <Z> = 0, or every <Z> = 1).
Plus once for the job: **RUNS** if the entrance builds and the job returns with no hand step.

## Reported

- Readable depth per problem family (largest t with READS, AGREES, BEATS).
- The card's floor and mirror flags against the worst qubits; the sentinel; P4's light-cone site value.

## Honest expectation

- Raw values sit about a floor (0.8-0.9) below the answers, so AGREES is unlikely beyond small t, and for answers near 1
  (P5 theta 0.4) BEATS is hard (the all-1 guess is close). READS is easy where answers are near 1 or 0: BEATS is
  the stricter test. P4 b = pi/4 - 0.05 is nearly dual-unitary: its signal sits on one site, small elsewhere.
