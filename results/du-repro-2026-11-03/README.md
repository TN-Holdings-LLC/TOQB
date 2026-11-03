# P4, 2026-11-03: the dual-unitary kicked Ising experiment reproduced on ibm_kingston without error mitigation: READS, and the decay rate AGREES with cos 2h at all three h

- **Declaration:** `prereg/drafts-2026-11-03/du_repro_note.md` (SHA-256 f01e308d...ef22a2), fixed 02:16 CET, TOQB
  c4c2ed4; psf-os 0fc96e5 (`psf_os/dual.py`). Built by `gpu/du_repro.py` from the fetch of 02:17:44 CET
  (calibration 01:16:20 CET, target fa420780...) and the day-3 registry.
- **Jobs:** S dbkjdi8nceqs73am18f0, V dbkjdm1ffo6c73bbl8d0, sent with `psf-os submit` at 02:20 CET, options off,
  "stay"; both DONE, collected with `psf-os collect`; 53 s billed each. 48 circuits x 4000 shots each.
  Scored by `scores.json` (`gpu/du_score.py`).

## The fetch changed the comparison before anything was sent

IBM's record of 02:17 CET marks couplers (29, 38) and (9, 10) as failed; the record of 2 November did not. They are
the middle couplers of two paths psf-os's registry had LISTED since 2 November ([28, 29, 38, 49] and [11, 10, 9]).
So the rule's standard ring no longer passes (29, 38): S and V got the same chain (qubits 3-7, 17, 27-33, 39, 53-55,
59, 75-73) and byte-identical circuits (efff3b34...). The owner chose to send both as declared (a replicate);
judgement 4 is not comparable.

## Judged

| | S | V |
|---|---|---|
| 1. sentinel | CLEAN (DEAD was expected on yesterday's ring; not on this chain) | **CLEAN** |
| 2. MSE of <X_t> vs exact, 40 points (half the mean square: 0.42) | 0.0139: READS | **0.0123: READS** |
| measured / exact, mean | 0.886 +- 0.002 | 0.892 +- 0.002 |
| 3. rate k, h = 0.05 (cos 2h 0.9950) | 0.9937 +- 0.0007 AGREES | **0.9971 +- 0.0007 AGREES** |
| 3. rate k, h = 0.10 (cos 2h 0.9801) | 0.9798 +- 0.0008 AGREES | **0.9810 +- 0.0008 AGREES** |
| 3. rate k, h = 0.15 (cos 2h 0.9553) | 0.9539 +- 0.0011 AGREES | **0.9573 +- 0.0011 AGREES** |

**Sentence fixed in advance (READS and AGREES at all three h):** *psf-os reproduces the exact answer of the
dual-unitary experiment without error mitigation on a 21-site chain.*

4. **V - S:** +0.0058 +- 0.0024 on the same circuits: not an OS effect but the difference between two runs a minute
   apart, 2.4 times the shot-noise SE (the shot-noise SE understates run-to-run variation).

## Reported

- Raw signal at t = 10 (210 CZ): h = 0: 0.781 (exact 1); h = 0.15: 0.496 (exact 0.633), i.e. about 0.78 of the answer
  with no mitigation. The rate uses the ratio to the h = 0 trace of the same job (Clifford, the same gates): declared
  in judgement 3, a division, not a noise model.
- Off-cone |<X_n>| (n != t): mean 0.021 (S), 0.022 (V); largest 0.096. Shot noise alone gives about 0.013 mean.
- t = 0 (readout of |+>): 0.9975-1.000.
- Scale against IBM's run (arXiv 2411.00765): 21 qubits and 210 CZ here, against 91 qubits and about 4,095 two-qubit
  gates there with noise learning, twirling and tensor-network mitigation.
