# Paper 7 outline (workplace draft, 2026-11-04): from problems with answers to a problem without one

Status: an outline for home and the owner. No new claim; every number points to a declared record. Show-off numbers
and essential numbers are given side by side.

## Working title

*Reading a 151-qubit lattice without error mitigation: a ladder from problems with exact answers to one without*

## The ladder (owner, 11/03: no tests made to impress; hard problems with answers first, then the same difficulty
without an answer)

| rung | problem | answer from | record | headline | essential |
|---|---|---|---|---|---|
| 1 | P4 stage 1: dual-unitary kicked Ising chain (arXiv 2411.00765), N = 21, t <= 10, 210 CZ | closed form / numpy | results/du-repro-2026-11-03 | decay rate AGREES with cos 2h (0.9971, 0.9810, 0.9573 +- 0.001) | 0.89 of the exact answer recovered on average (a downward scale), READS MSE 0.012 against 0.42 |
| 2 | P4 stage 2b: away from the dual-unitary point, N = 33, t <= 16, 528 CZ | GPU statevector, sealed before the run | results/du-stage2-2026-11-03 | both off points READ and AGREE (RMS 0.023, 0.037; line 0.05) | on the light cone only; control rate 0.9559 +- 0.0008 against 0.9553 |
| 3 | P5 stage B: kicked Ising on kingston's whole lattice (151 qubits, 163 edges), t <= 5, 815 CZ | CPU causal cones (<= 19 qubits) | results/kim-lattice-2026-11-03 | magnetisation within 0.05 at every t (largest miss 0.042) | the worst qubits are the ends of IBM's failed coupler (130, 131) |
| 4 | P5 stage C: t = 6-8 | GPU cones (<= 33 qubits), sealed | results/kim-cd-2026-11-03 | READS at 0.4, 0.8, 1.0; AGREES at 0.8 and 1.0 | theta 0.4 DIFFERS at t = 8 (0.053); only qubits with small cones (towards the edges) are answered at t = 7, 8 (122, 82) |
| 5 | P5 stage E: suspect-qubit lattice (kingston) and a second device chosen by queue (fez) | as rung 4 | results/kim-e-2026-11-03 | kingston: all AGREE to depth 8 (theta 0.4: 0.031) | fez: theta 0.4 DIFFERS (0.079) through readout faults IBM does not mark (23: -0.79 at theta 0); price of the suspect rule 26 qubits |
| 6 | P5 stage D: t = 20, 3,260 CZ, no exact answer | none; SPD estimate (workplace, rust/spd) as an independent classical value with its convergence width | results/kim-cd-2026-11-03 + notes/spd_2026-11-04 | device M 0.819, 0.253, 0.050 (theta 0.4, 0.8, 1.0); controls AGREE (0.979, 0.001) | the classical value is an estimate with a truncation error that cannot be bounded rigorously; see the SPD table |

Sections:
1. Introduction: why answers first; the policy (no map read, no search, answers sealed before the run).
2. Methods: psf-os (scan, registry, avoid, sentinel), the circuits (RZZ(-pi/2) as one CZ; edge colouring), the answers
   (closed form, statevector, causal cones on GPU, sealing), scoring (READS, AGREES), the suspect-qubit rule.
3. Rungs 1-2 (1D). 4. Rungs 3-5 (2D, two devices). 5. Rung 6 (t = 20) with the classical estimate.
6. Limits and the comparison below. 7. What the next problem without an answer should be.

## A fair comparison with IBM's public example (Qedma QESEM tutorial)

The tutorial (IBM Quantum documentation, "qedma-2d-ising-with-qesem", read 2026-11-04) runs a 2D kicked Ising circuit
on 35 qubits of a Heron r2 device: RZZ(1.0), RX(0.53), RZ(0.1) per step; magnetisation at 5, 7, 9 steps; reference
values by belief-propagation PEPS (quimb). Unmitigated against the reference: 0.704 / 0.795 (5 steps, gap 0.091),
0.648 / 0.787 (7 steps, gap 0.139), 0.617 / 0.797 (9 steps, gap 0.180). QESEM-mitigated: 0.783 +- 0.013, 0.788 +- 0.027,
0.692 +- 0.074.

What differs, to be stated in the paper:
- **Weight of a step.** Their RZZ(1.0) is a generic angle: two CZ per edge. Our RZZ(-pi/2) is one CZ. Each step has
  three edge colours in both, so a step is about 6 CZ layers for them and 3 for us. By CZ depth, our t = 8 (24 CZ
  layers) sits below their 5 steps (about 30), and their 7 steps (about 42) correspond to our t of about 14. Compare at
  equal CZ depth, not equal step count.
- **Clifford structure.** Our RZZ(-pi/2) is Clifford; only RX(theta) is not. That makes our circuit easier for some
  classical methods (SPD works at t = 20); theirs has non-Clifford two-qubit gates.
- **The reference.** Ours are exact (statevector or causal cones) up to t = 8; theirs is a PEPS-BP estimate. At t = 20
  neither side has an exact value.
- **Size and selection.** 151 qubits (the whole lattice after the registry's mask) against 35 chosen qubits.
- **Mitigation.** We use none; their headline is the mitigated value. Fair to compare: our unmitigated miss against
  their unmitigated gap at similar CZ depth (ours at most 0.053 at 24 layers, full lattice; theirs 0.091 at about 30
  layers). Not fair: our unmitigated against their mitigated.
- **Readout.** Our theta-0 floor (0.977 on kingston) accounts for about 0.02 of the theta-0.4 miss; their noisy values
  carry their readout error too.

## Open items for home

- Whether rung 6 needs the pod run of SPD at delta 1e-5 (notes/spd_2026-11-04/spd_pod.sh) before writing.
- Whether the readout-check rule (prereg/drafts-2026-11-04/readout_rule_DRAFT.md) becomes a rung or an appendix.
- The fez result (rung 5) as the paper's main limit: a device without a registry and with unmarked readout faults.
