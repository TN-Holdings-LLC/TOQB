# W14 (draft, home, 2026-10-21): the undamped-readout match

**Status.** Draft for the owner. Nothing has been run. The owner fixes the headline and the points of section 4, then
the rule text and `toqb/match_score_undamp.py` are fixed by SHA-256 before the first record is read.

## Why

The owner's question of 2026-10-21: fix E, fix C, or carry E's strength into C. The answers so far:

- E under noise loses to C (the fruit match, 0 of 3 groups).
- C's optimiser has no room: C0 fits the 64 training points and its test CE stops after half its budget (W12).
- The readout has room. The twin knows how its noise shrinks and shifts the answer (z_noisy ~ lam z_ideal + delta).
  Undoing that by formula, with no labels and no device data, recovered 0.05 to 0.08 CE for trained models on the
  fruit match's records. On the rehearsal's records it turned Qiskit's raw CE lead (0.035) into a PSF lead (0.010).
  Both were post hoc: `results/readout-2026-10-21/`.

The pipeline under test is **design C's training with the undamped readout** (`toqb.undamp`, `toqb.undamp_run`).

## The match (`gpu/undamp_match.sh`)

| item | value |
|---|---|
| tasks | fresh teachers 13, 14, 15 x angles 0.3, 1.0, 2.0 (W9's ladder) x L 8: 9 tasks |
| training | C0 (`toqb.s2rc_ckpt`, seed 201, init 0, 2,000 loops, as the fruit match) on each compiler arm: PSF (`psfai:template`) and Qiskit (`qiskit:2:target:template`); 18 runs |
| readout | raw p = (1 + z) / 2; undamped z_u = clip((z - delta) / lam, -1, 1), (lam, delta) from the arm's own twin on the 64 training inputs (1,024 trajectories, seed predict.seed + 5) against the exact noiseless model; no labels, no stand-in |
| scoring | per point on the stand-in's exact P(1), W8's statistics; groups (angle, L) with Stouffer and Holm over groups (W11's rule); `toqb.match_score_undamp` |
| also reported | accuracy (McNemar), the undamped prediction layer (stand-in undamped CE inside the undamped interval), (lam, delta) per run |

## Comparisons

| id | X against Y | role (proposed) |
|---|---|---|
| A | PSF undamped against PSF raw | does the readout help PSF |
| B | PSF undamped against Qiskit raw | the new pipeline against the opponent as it stands |
| C | PSF undamped against Qiskit undamped | the same readout on both: what remains is the compiled model |
| D | Qiskit undamped against Qiskit raw | reported |

## Points for the owner

1. **The headline:** A, B or C, or a pair (proposed: B and C together, per group, "won in k of 3 groups").
   - B alone would let the readout win against an opponent without it. C keeps the race fair.
   - B and C together say "the pipeline beats Qiskit as it stands, and the gain is not only the readout".
2. **Undamping can hurt a poor model** (theta = 0, C0 at angle 2.0 in the post hoc test). Proposed: no rule to switch
   it off. A switch would be a choice made after seeing outputs, a lane. The loss is reported per group.
3. **Qiskit's lane** (calibration-aware placement) is kept as Qiskit's own choice, as W8.
4. **Cost:** the Qiskit runs take about twice as long. About 4 to 5 h on an H100 (estimate), about $18.

## Known prior art

Rescaling an expectation value by a known noise factor is an error-mitigation idea. It was not checked by search
today, and no novelty is claimed.
