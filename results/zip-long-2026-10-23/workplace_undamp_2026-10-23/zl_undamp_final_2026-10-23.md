# Long loops (zl), undamped readout at the final point only: a diagnosis, report only (workplace, 2026-10-23 06:59 CEST)

**Status.** This is a diagnosis, not a result to carry forward.

- **The owner's decision stands:** no correction; accuracy is primary.
- **λ and δ** come from the twin on the training inputs, without labels (toqb.undamp_run).
- **Scope reduced.** The declared undamp step covered every checkpoint. It was too slow and home stopped it, so the
  step was rerun on the final point only (`--final-only`). Checkpoint-wise λ exists only where the stopped run had
  already logged it.
- **Not on a device.** All numbers are on the stand-in: 500 test points, 250 shots.

## Why the declared step was slow (measured)

| case | time |
|---|---|
| final point alone | 61 s (51 s of it user CPU) |
| earlier zu4 point | 40-53 s |
| checkpoint points in the stopped run (3 in parallel) | 11-15 min each |

- The final-point path is normal; the per-checkpoint path is the slow one.
- **Unconfirmed:** why. The source was not read. A likely candidate is a replay of earlier checkpoints' random draws.
- **Settings ruled out:** the GPU and thread settings (TOQB_XP=cupy, threads 1) were in effect.

## Final point (16,000 loops)

| teacher | arm | λ | δ | stand-in CE raw → undamped | accuracy raw → undamped |
|---|---|---|---|---|---|
| t11 | item 31 | 0.317 | +0.036 | 0.6439 → 0.6106 | 0.587 → 0.648 |
| t11 | zipper | 0.227 | −0.007 | 0.6474 → 0.5909 | 0.672 → 0.674 |
| t12 | item 31 | 0.293 | +0.056 | 0.6310 → 0.5407 | 0.617 → 0.676 |
| t12 | zipper | 0.221 | −0.006 | 0.6492 → 0.5956 | 0.686 → 0.686 |
| t13 | item 31 | 0.233 | +0.048 | 0.6462 → 0.5992 | 0.630 → 0.676 |
| t13 | zipper | 0.195 | +0.008 | 0.6532 → 0.5606 | 0.687 → 0.684 |

**Zipper minus item 31:**

| teacher | accuracy, raw | accuracy, undamped | CE, raw | CE, undamped |
|---|---|---|---|---|
| t11 | +0.085 | +0.026 | +0.004 | −0.020 |
| t12 | +0.069 | +0.010 | +0.018 | +0.055 |
| t13 | +0.057 | +0.008 | +0.007 | −0.039 |

The twin's interval for the undamped CE contained the stand-in in 5 of 6 cases. Zipper t13 fell outside: 0.5606,
below [0.5698, 0.7158], so better than predicted.

## Checkpoints logged before the stop

| case | λ at each checkpoint |
|---|---|
| item 31 t11 | 0.217 → 0.238 → 0.276 → 0.317 (500, 1,000, 2,000, 16,000 loops) |
| zipper t11 | 0.160 → 0.166 → 0.173 → 0.198 → 0.227 (500, 1,000, 2,000, 4,000, 16,000) |
| item 31 t12 | 0.264 → 0.268 → 0.276 → 0.293 (500, 1,000, 2,000, 16,000) |

Stand-in accuracy at 500 loops, raw → undamped:

| case | raw | undamped |
|---|---|---|
| item 31 t11 | 0.628 | 0.742 |
| zipper t11 | 0.721 | 0.732 |
| item 31 t12 | 0.640 | 0.728 |

## Reading

1. **λ rises with training** in every series followed. The model's damping shrinks as it trains, so the loss of
   accuracy with training is not caused by growing damping.
2. **Only item 31 carries a readout offset:** δ +0.036 to +0.056 in 3/3, against −0.007 to +0.008 for the zipper.
   - Undamping moves the sign threshold. Item 31's accuracy rises by 0.046-0.061; the zipper's changes by
     −0.003 to +0.002.
   - **Unconfirmed:** the offset's cause. One candidate is relaxation toward |0⟩ on item 31's longer schedule.
3. **On the stand-in, most of the zipper's accuracy lead is item 31's offset.**
   - Raw: +0.057 to +0.085.
   - Undamped: +0.008 to +0.026.
   - At 500 loops (t11) the order reverses once undamped: 0.742 against 0.732.
4. **Vanity and essential numbers:**
   - **Vanity:** "the zipper beats item 31 in accuracy at every checkpoint".
   - **Essential:** on the stand-in, that lead is largely an offset in item 31's readout, not a better-trained
     model. This weakens the study-method hypothesis (the zipper learns better) and points to a narrower property:
     the zipper gives an offset-free readout. That is still a property of the zipper, but a different claim.
5. **Limits:**
   - three teachers, the final point and three logged checkpoints;
   - the stand-in, not a device;
   - λ and δ are twin estimates;
   - no per-point paired test yet (needs the per-point data in zl_undamp_final.zip).

## Next, if wanted (each declared before it runs; design changes go to the owner first)

- **Per-point paired tests** (W8 helpers, McNemar and Holm, α 0.01) on the undamped accuracy gap, from
  zl_undamp_final.zip.
- **The parameter-swap test.** Run zipper-trained θ on item 31's circuit and the reverse. Report raw accuracy, and
  report δ next to it, to separate "learned better" from "read out without offset".

---

## Addendum (2026-10-23 07:01 CEST): per-point paired tests, shot-free; correction of reading 3

**Data.** zl_undamp_final.zip carries summaries only, with no per-point values. The paired tests therefore use the
stand-in's exact per-point P(1) and the test labels, both stored in the zl run files (`rehearsal.standin_p1`,
`test_labels`).

**Convention.**

- z = 1 − 2·P(1), and the undamped readout is clip((z − δ)/λ).
- This reproduces the recorded `standin_ce_exact` and the undamped `ce_exact` to 4 decimals in 6/6 files.
- With λ > 0, undamped accuracy is the sign of z − δ.
- Both arms share the same 500 test points; the labels are identical, with 50 % positive.

**Test.** Exact McNemar, Holm over the three teachers, α 0.01. Scripts: `pair.py` (final point) and `ck.py`
(checkpoints).

**Final point (16,000 loops), shot-free stand-in accuracy:**

| teacher | raw: zipper / item 31 (gap) | McNemar zip-only / q31-only, Holm p | undamped: zipper / item 31 (gap) | McNemar, Holm p |
|---|---|---|---|---|
| t11 | 0.710 / 0.532 (+0.178) | 154 / 65, 4.9e-9 | 0.704 / 0.712 (−0.008) | 67 / 71, 0.8 |
| t12 | 0.714 / 0.586 (+0.128) | 116 / 52, 8.7e-7 | 0.698 / 0.734 (−0.036) | 57 / 75, 0.42 |
| t13 | 0.738 / 0.588 (+0.150) | 120 / 45, 9.1e-9 | 0.748 / 0.724 (+0.024) | 58 / 46, 0.56 |

**Item 31's raw readout calls +1 on 82-92 % of the points**, against 50 % positive labels; the zipper calls +1 on
51-55 %. After the δ shift item 31 calls +1 on 36-42 %, so the twin's δ slightly overshoots.

**t11 checkpoints**, using the δ logged by the stopped run (3 decimals), shot-free; plain p, one teacher:

| loops | raw: zipper / item 31 (gap), p | undamped: zipper / item 31 (gap), p |
|---|---|---|
| 500 | 0.866 / 0.682 (+0.184), 2e-15 | 0.878 / 0.736 (+0.142), 1.4e-11 |
| 1,000 | 0.760 / 0.634 (+0.126), 1.5e-8 | 0.796 / 0.736 (+0.060), 0.013 |
| 2,000 | 0.758 / 0.582 (+0.176), 3.9e-14 | 0.798 / 0.740 (+0.058), 0.018 |

> **Correction, 2026-10-23: reading 3 overstated a reversal at 500 loops.** The shot-based numbers (item 31 0.742
> against the zipper's 0.732 undamped) were shot noise.
>
> - The zipper's λ is small (about 0.16), so its |z| is small and 250 shots flip many signs. Its shot-based undamped
>   accuracy is 0.732, against 0.878 shot-free.
> - Shot-free, the zipper keeps a clear lead at 500 loops after the δ shift: +0.142, p 1.4e-11.

**Revised reading:**

1. **On the stand-in, item 31's raw accuracy deficit is mostly a readout offset.** It calls +1 on about 85 % of the
   points.
   - At 16,000 loops, removing δ removes the zipper's lead entirely: −0.036 to +0.024, Holm p ≥ 0.42, in 3/3.
2. **Early in training the zipper is better beyond the offset.** At 500 loops (t11): +0.142, p 1e-11. The lead
   shrinks with training: +0.06 at 1,000-2,000 loops (p about 0.015, not significant at α 0.01) and nothing at
   16,000.
3. **What this means for the study-method hypothesis:**
   - It is supported early in training, on one teacher.
   - It is not supported at the end of long training.
   - Combined with the accuracy drop with training (both arms), the zipper's real advantage looks like better early
     learning that long training erodes, plus an offset-free readout throughout.
4. **Shot noise hurts the zipper more**, because its λ is smaller: shot-based accuracy falls well below shot-free.
   This matters for any device test with a fixed shot count.
5. **Vanity and essential numbers:**
   - **Vanity:** "the zipper +0.13 to +0.18 in accuracy, p ≤ 1e-6, 3/3".
   - **Essential:** after the offset it is +0.14 at 500 loops (one teacher) and about 0 at 16,000 loops (3/3, not
     significant).
6. **Limits:**
   - the stand-in only;
   - δ is the twin's estimate;
   - checkpoints for one teacher only;
   - the δ-shift accuracy is a diagnostic, not a method (owner: no correction).
   - **Unconfirmed:** the offset's cause. Relaxation toward |0⟩ fits the direction (item 31 leans to z > 0, that is
     |0⟩) but has not been tested.

**Next (each declared first; owner decides):**

- Undamp at the 500-loop checkpoint for t12 and t13, final-point style, one point per call, so that reading 2 rests
  on 3 teachers.
- The parameter-swap test as before.
