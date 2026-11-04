# P6 on a device: the Qedma tutorial's 2D Ising problem without error mitigation (drafted at the workplace, fixed at home, 2026-11-04)

Status: drafted by the workplace (95b88d6, `p6_device_note_DRAFT.md`), fixed at home after the owner's go of
2026-11-04 with the three choices below decided as proposed. The builder is `gpu/p6_device.py` (dry-run on fake
devices only, below).

**Why.** P6 is the problem of IBM's public tutorial "Ising model with Qedma QESEM": 35 qubits of a Heron r2 lattice,
per step RX(0.53) and RZ(0.1) on every qubit, then RZZ(1.0) on 38 edges in three layers; average magnetisation. The
tutorial reports, on ibm_marrakesh, unmitigated values 0.704, 0.648, 0.617 at 5, 7, 9 steps against belief-propagation
PEPS values 0.79537, 0.78653, 0.79699 (gaps 0.091, 0.139, 0.180). Our exact answers (light cones, sealed) agree with
the PEPS values to the fourth decimal at t = 5 and 7. The question: with psf-os's placement and no mitigation, how close
does the device come to the exact answer on the same problem?

**Same circuit, stated carefully.** psf-os builds the tutorial's logical circuit gate for gate (`psf_os.ising2d`,
psf-os 61e9edd). RZZ(1.0) is written as CX RZ CX with CX = H CZ H: 2 CZ per edge, 2 x 38 x t CZ per circuit
(acceptance checks the count), and each RZZ layer is a matching, so a step is 6 CZ layers. **What the tutorial's page
does not say:** whether its noisy values used native fractional RZZ gates or a CZ/CX decomposition, which error
suppression (dynamical decoupling, twirling) or readout handling they had, and their shot count (only a 300 s budget
per job). So the logical circuit is the same; the device-level circuit may differ, and the comparison is reported, not
judged.

## Device and placement

- **Device by queue (owner, 11/03):** right before the fetch, the pending jobs of ibm_fez, ibm_marrakesh and
  ibm_kingston are read (no quality number); the device with the fewest is used. Ties: the fixed order
  marrakesh, fez, kingston (marrakesh first because it is the tutorial's device; owner, 2026-11-04). The numbers are recorded.
- **Registry:** if the device has a registry (kingston), its LISTED paths are masked before placement, as in P5.
- **Placement:** `ising2d.place`: the first of six copies (row offset 0, 2, 4 x column offset 0, 4), in that order,
  with every qubit working, every edge a working coupler, and no qubit at an end of a failed or masked coupler. No
  search; the copy and the reasons each earlier copy was passed over are recorded.
- **If no copy qualifies on the chosen device (owner, 2026-11-04):** take the next device in queue order
  (fewest pending jobs among the rest), and so on; if none qualifies, no job is sent and that is reported. The
  alternative, relaxing the suspect rule on the first device, is not proposed: it changes the lattice rule after
  seeing the device. **This case is not hypothetical** (dry runs below): with IBM's failed marks of 3 November and the
  registry's mask (85, 86), no copy qualifies on kingston; without the mask, copy (2, 0) does.

## The job (one job, 4000 shots, no mitigation, options off, "stay", `psf-os submit`)

| cells | t | circuits | purpose |
|---|---|---|---|
| theta_x 0.53 | 1..9 | 9 | the tutorial's problem |
| theta_x 0 (control) | 1, 5, 9 | 3 | readout floor: every gate is diagonal, ideal <Z_q> = 1 at every depth, same CZ count as the problem at that t; also the input of the sub-analysis (rule R) |
| theta_x 0.3, 0.8 | 1..9 | 18 | only if their t = 6..9 answers (problem bank) are sealed before the fetch; otherwise left out |
| sentinel | echo D = 24, n = 40 ring | 4 | CLEAN expected |

16 circuits and 20.9 s by the time model (34 circuits and 40.9 s with the bank cells), from the dry run on
FakeKingston. The theta_x = 0 control is included (owner, 2026-11-04) because (1) it measures the readout floor inside the same job, as
P5's theta = 0 did, and (2) the sub-analysis needs it.

## Answers (sealed before the fetch)

theta_x 0.53: CPU t <= 5 (`results/p6-answers-2026-11-04/answers_cpu.json`, f183ca5) and pod t = 6..9
(`gpu/answers_gpu.json`, SHA-256 0482c81a..., c9097e5; checks K1 1.0e-5, K2 1.9e-5, K3 2.8e-8). Answered qubits: 35 at
t <= 7, 32 at t = 8, 28 at t = 9. Exact magnetisation on them: 0.86281, 0.84205, 0.87352, 0.83588, 0.79542, 0.79204,
0.78661, 0.77479, 0.76846 (t = 1..9). The copies are identical, so one set of answers serves whichever copy is placed.
theta_x 0: 1 exactly.

## Judged (theta_x 0.53; each bank theta separately if present)

1. **Sentinel:** CLEAN expected; DEAD or WEAK is reported with its sites and does not stop the scoring.
2. **READS:** the mean squared error of <Z_q> over answered qubits and t = 1..9 is at most half the answer's mean
   square (P3-P5's rule). Note: with answers near 0.8 this line is loose (about 0.3); it says the device carries the
   signal, not that it is accurate.
3. **AGREES:** the magnetisation over answered qubits is within 0.05 of exact at every t = 1..9.
   - READS and AGREES: *psf-os reads the tutorial's 2D Ising problem without error mitigation to step 9 within 0.05.*
   - Otherwise the first t that misses and by how much.

## Reported, not judged

- **Against the tutorial's unmitigated values** at t = 5, 7, 9: our |M_measured - M_exact| next to their
  |noisy - PEPS| (0.091, 0.139, 0.180), with the caveats above (device and date, gate implementation unknown on their
  side, reference PEPS-BP on 35 qubits against our exact answer on the answered qubits; at t = 9 also our M over all 35
  measured qubits against 0.79699). Why the two sets matter at t = 9: the 28 answered qubits average 0.76846 exactly,
  while the workplace's SPD over all 35 qubits gives 0.7909 at delta 3e-5 (an estimate from below; on the answered
  qubits it is 0.006 under the exact value), close to the PEPS value; the 7 unanswered qubits read higher. So at t = 9
  the tutorial's number and ours describe different qubit sets. Their mitigated values (0.783, 0.788, 0.692) are listed but not compared with our
  unmitigated ones.
- The theta_x = 0 floor per t; per-t magnetisations; the worst qubits; the copy and the reasons; the queue; billed time.

## Sub-analysis fixed in advance (prereg/drafts-2026-11-04/readout_rule_DRAFT.md, rule R)

From the theta_x = 0 cells (t = 1, 5, 9): leave out a qubit whose mean <Z> is below
median - max(5 x 1.4826 MAD, 0.05); rescore READS and AGREES on the kept qubits (measurement and answer alike).
Verdict of R: HELPS if the MSE (theta_x 0.53, answered and kept qubits) is at most 0.8 of the full set's, NO EFFECT
between 0.8 and 1.25, HURTS at 1.25 or more. Reported with the dropped qubits, their values and the line. The main
verdicts (1-3) are those of the full set.

## Dry runs (fake devices; not the device's state on the day)

| device record | copy chosen | job |
|---|---|---|
| FakeKingston (qiskit-ibm-runtime snapshot) | (0, 0) | 16 circuits, 20.9 s; with bank 34, 40.9 s; CZ per circuit 76 x t (0.53 and 0) |
| FakeFez snapshot | none: every copy has a failed coupler | — |
| FakeMarrakesh snapshot | none: every copy has a suspect qubit (copy (0, 4) only qubit 25) | — |
| fez with the failed marks of 3 Nov (32, 33), qubit 72 (stage E fetch) | (0, 0) | — |
| kingston with the failed marks of 3 Nov | (2, 0) | — |
| kingston with the failed marks of 3 Nov and the registry mask (85, 86) | none | — |

The fake snapshots are old and are not the devices' current marks; they show only that "no copy" happens, which is why
the fallback rule above has to be fixed before the fetch.
