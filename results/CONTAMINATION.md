# Contamination notice: outputs that use failed elements (added 2026-10-10, after standard run 2)

**Status: a correction to the published results of standard runs 1 and 2.** Their scores are not changed: they
stay as the pre-registrations defined them. This notice says which of their numbers rest on outputs that cannot be
used, and how TOQB treats such outputs from now on. Times are in CEST.

## What was wrong

FakeTorino's Target reports some couplers with an error of 1, which means that the two-qubit gate on them fails.
qiskit-ibm-runtime builds the same kind of Target for the real devices. Such couplers are not marked as
non-operational, so they stay in the Target. A circuit with a gate on one of them gives noise on the device, and
nothing in the circuit or the result says so. **Its value to someone who runs it is zero.** If it is mixed into a
set of results, nobody can tell which results are noise.

TOQB's structural check accepted these outputs as valid, and the scoring counted them like any other output: in the
tiers, and in the two-qubit ratios against the reference. TOQB recorded the number of such gates (`on_failed`), but
only as a reported figure. One prediction (T4 in run 1, S4 in run 2) checked it, and only for PSF-Zero's
recommended call. The reference compiler itself (qiskit:2:target) produced such outputs, and they were scored.

## Which outputs

On the 18 FakeTorino tests of the standard sample, the same 26 outputs in run 1c and in run 2 have two-qubit gates
on failed couplers (an element is failed when its reported error is >= 0.5):

| test | outputs with gates on failed elements (number of such gates) |
|---|---|
| ham_dsjc1000.1,n-36,rinst-4 | qiskit:2:target (145), qiskit:1:target (190), qiskit:3:target (169), psf:default (309) |
| ham_graph-2D-grid-nonpbc-qubitnodes_Lx-5_Ly-15_h-3 | qiskit:2:target (45), qiskit:1:target (62), qiskit:3:target (68), psf:default (64) |
| ham_queen13_13,n-28,rinst-0 | qiskit:2:target (181), qiskit:1:target (140), qiskit:3:target (89), psf:default (132) |
| ham_reg-4_n-90_rinst-07 | qiskit:2:target (197), qiskit:1:target (234), qiskit:3:target (153), psf:default (333) |
| ham_mu_y_prime_enc_unary_dvalues_16-16-16-16-16-16 | qiskit:2:target (4), qiskit:1:target (8), psf:default (4) |
| ham_mu_y_prime_enc_unary_dvalues_8-8-8-8-8-8-8 | tket:2 (2) |
| ham_ham_JW-8 | psf:default (401) |
| adder_8 | psf:default (81) |
| gf2^5_mult | tket:2 (11) |
| gf2^9_mult | psf:default (23) |
| mod_adder_1024 | psf:default (564) |
| qcla_mod_7 | psf:default (98) |

| compiler | FakeTorino outputs usable on the device (run 1c and run 2) |
|---|---|
| qiskit:2:target (the reference) | 13 of 18 |
| qiskit:1:target | 13 of 18 |
| qiskit:3:target | 14 of 18 |
| tket:2 | 4 of 18 (14 failed for other reasons) |
| psf:default | **8 of 18** |
| psf:recommended | 17 of 18 (none used a failed element; hwb8 was stopped by time) |

The lists are in [`standard-run-1/contaminated-run-1c.json`](standard-run-1/contaminated-run-1c.json) and
[`standard-run-2/contaminated.json`](standard-run-2/contaminated.json).

**These counts are a lower bound.** The records count two-qubit gates only, and the outputs themselves were not
kept. FakeTorino reports one qubit whose measurement fails (error >= 0.5). A measurement on it would also make an
output unusable, and the records cannot show whether any output measured it.

**PSF-Zero's default call is the worst case here, and the reason is partly TOQB's.** Its adapter passed only the
coupling map and the basis, never the Target: the default call had no way to know which elements had failed. In the
same runs, the recommended call, which gets the Target, used no failed element. Still, the default call as the
PSF-Zero README gave it is what a user would run, and its outputs are listed as they are.

## What the published numbers mean now

- **Runs 1 and 2's scores stand as defined**, and they are not rescored officially. Any figure that counts the 26
  outputs above is **contaminated**: the tier shares on FakeTorino, the two-qubit ratios, and the comparisons
  against the reference on the five tests where the reference itself is unusable.
- **Re-scored views (exploratory, after the fact).** The same records are read with failed elements as failures,
  next to the published scores:
  [`standard-run-1/run-1c-rescored-v14/essential.md`](standard-run-1/run-1c-rescored-v14/essential.md) and
  [`standard-run-2/rescored-v14/essential.md`](standard-run-2/rescored-v14/essential.md). Each is labelled
  "display / essential". The records hold no first-compile time, so their essential time is the display time.

## From TOQB v14 on

- **An output with any operation on a failed element is unusable.** That covers a two-qubit gate on a failed
  coupler, and any gate or measurement on a failed qubit (including a qubit whose measurement fails). On a device
  with a Target, it is scored as a failure, like an invalid output. It is not given a penalty weight: one such
  output is enough for its result to be worth nothing (`toqb/metrics.py: failed_operations`).
- **Every adapter gets the device's error information.** TOQB will not disqualify a compiler for an element it was
  not allowed to see. That means the Target for Qiskit and PSF-Zero's calls, and the averaged errors in TKET's
  `BackendInfo`.
- **Two numbers, always.** A run's results are given as scored by its pre-registration ("display") and as a user who
  runs the outputs on the device sees them ("essential": unusable outputs are failures, and time is the first compile
  in the process, which a user always pays) (`toqb/essential.py`).
- **A scored run under these rules needs its own pre-registration (standard run 3).**
