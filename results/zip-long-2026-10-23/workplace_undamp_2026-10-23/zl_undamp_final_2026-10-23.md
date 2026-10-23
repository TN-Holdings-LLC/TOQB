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

---

## Addendum 2 (2026-10-23 07:32 CEST): the untrained model is already near the teacher; this weakens "learns better early"

**Data.** The twin's learning curve stored in each zl run: `curve`, 100 points and 64 trajectories, so it is noisy.
The twin's accuracy at loop 0 (θ = 0, untrained) and later:

| run | 0 | 200 | 1,000 | 4,000 | 16,000 |
|---|---|---|---|---|---|
| item 31 t11 | 0.91 | 0.93 | 0.88 | 0.86 | 0.82 |
| zipper t11 | 0.83 | 0.95 | 0.86 | 0.80 | 0.65 |
| item 31 t12 | 0.89 | 0.90 | 0.90 | 0.87 | 0.86 |
| zipper t12 | 0.90 | 0.92 | 0.88 | 0.83 | 0.70 |
| item 31 t13 | 0.89 | 0.88 | 0.85 | 0.90 | 0.90 |
| zipper t13 | 0.95 | 0.95 | 0.90 | 0.87 | 0.80 |

- **The twin's CE is at or near its best at loop 0-200 in 6/6 runs**, and it worsens from there.
- **Why the untrained model scores so well:** the task draws the teacher's angles from ±0.3 around 0 and starts the
  student at θ = 0, so the untrained student is already close to the teacher. Training mostly drifts away from a
  near-optimal start.
- **Consequence for the addendum above.** At loop 0 the two arms are the same logical model with the same θ.
  - The zipper's δ-free lead at 500 loops (+0.142, t11) may therefore be the same near-initial model read out better
    (fewer CZ), not better learning.
  - **Unconfirmed:** which of the two it is. Reading 2 of Addendum 1 ("better early learning") is withdrawn until
    the θ = 0 check below has run.
- **Answer to "does training become unnecessary?"**
  - In this task, nearly: θ = 0 already scores 0.83-0.95 on the twin.
  - But this is a property of the task (teacher near the start), not of the compiler or the method.
  - It says nothing about tasks whose teacher is far from the start. In the workplace toy with teacher angle 1.0,
    θ = 0 gave 0.74 noiseless.
  - Choosing a loop budget from these curves would be a search. Any budget must be declared before the run, on fresh
    teachers.

**Cheapest check (declared first; owner decides).** Evaluate both arms at θ = 0 on the stand-in, shot-free (about 1
minute per arm, no training).

- If the zipper's δ-free lead at θ = 0 is already about +0.14, the lead is the schedule's readout, not learning.
- Then a task whose teacher is far from the start (a larger teacher angle, declared in advance) is needed before
  any claim about learning or training time.

---

## Addendum 3 (2026-10-23 07:36 CEST): the 500-loop checkpoint on all three teachers (home's u500 run)

**Data.** Home ran the undamp step at the 500-loop checkpoint for all six runs (u500.zip).

- λ and δ come from that log (3 decimals).
- The stand-in's exact per-point P(1) comes from the zl run files.
- Shot-free. Exact McNemar, Holm over the three teachers. Script: `ck500.py`.

| teacher | raw: zipper / item 31 (gap), Holm p | δ-free: zipper / item 31 (gap), Holm p | +1 calls raw → δ-free: item 31 / zipper |
|---|---|---|---|
| t11 | 0.866 / 0.682 (+0.184), 2e-15 | 0.878 / 0.736 (+0.142), 1.4e-11 | 0.80 → 0.35 / 0.59 → 0.49 |
| t12 | 0.908 / 0.626 (+0.282), 9e-36 | 0.932 / 0.802 (+0.130), 9e-14 | 0.84 → 0.39 / 0.56 → 0.46 |
| t13 | 0.942 / 0.654 (+0.288), 3e-35 | 0.912 / 0.768 (+0.144), 2e-13 | 0.83 → 0.33 / 0.54 → 0.47 |

The twin's interval held in 5 of 6 cases. Zipper t13 fell outside, better than predicted (0.4385 against
[0.4493, 0.6251]).

**Reading:**

1. **At 500 loops the zipper leads beyond the offset in 3/3:** +0.13 to +0.14, Holm p ≤ 1.4e-11. At 16,000 loops the
   δ-free lead is about 0 in 3/3 (Addendum 1). The early δ-free lead is now on three teachers, not one.
2. **Its cause is still open.** It is either better learning or the same near-initial model read out better (fewer
   CZ); see Addendum 2. The θ = 0 check decides between the two.
3. **The twin's δ over-corrects item 31.** After the shift item 31 calls +1 on only 33-39 % of the points, against
   50 % positive labels.
   - Its δ-free accuracy is therefore probably somewhat understated, and the +0.13 to +0.14 should be read as an
     upper side.
   - No other threshold is tried here: choosing one would be a search.
4. **Shot noise:**
   - With 250 shots, the zipper's undamped accuracy is 0.732 / 0.792 / 0.768 against item 31's 0.742 / 0.728 /
     0.734.
   - The zipper's small λ (0.147-0.160) makes its decisions shot-fragile, and the lead nearly vanishes at this shot
     count.
   - Any device test must state its shot count and expect this.
5. **Vanity and essential numbers:**
   - **Vanity:** "zipper +0.18 to +0.29 at 500 loops, p ≤ 1e-15".
   - **Essential:** +0.13 to +0.14 once item 31's offset is removed (an upper side, given δ's over-correction). With
     250 shots it is close to 0. Whether the lead is learning or readout is unresolved.

#### Update (2026-10-23 07:39 CEST): Addendum 3 rechecked with home's u500 files (full-precision λ, δ)

**Check.** u500.zip carries the six undamp records and the run files, cut at the 500-loop checkpoint. Script:
`ck500x.py`.

- The stand-in's exact CE was reproduced to 1e-6 in 6/6, both raw and undamped.
- The test labels are identical across the two arms.

**Changes from the 3-decimal δ:**

- **t11, δ-free:** zipper 0.876 against 0.878 before; gap +0.140, Holm p 3.6e-11.
- **t12, δ-free:** item 31 0.800 against 0.802 before; gap +0.132, Holm p 4.9e-14.
- **Everything else is unchanged,** including t13 (+0.144, 1.7e-13), all raw numbers and the +1 call rates.

The reading of Addendum 3 stands.

---

## Addendum 4 (2026-10-23 08:13 CEST): θ = 0 (untrained) on the stand-in, shot-free, raw readout

**Data.** Home ran `predict_verify` at θ = 0 for both arms and the three teachers (theta0.json).

- **Values used:** the stand-in's exact per-point P(1), against the zl run files' test labels.
- **Labels:** identical across arms. The run files' labels are assumed equal to `teacher_data2`'s, from the same
  task.
- **Test:** exact McNemar, Holm over the three teachers. Script: `theta0_check.py`.
- **Not yet δ-free:** θ = 0's λ and δ (theta0_lam.json) have not arrived.

**Zipper against item 31, by training point:**

| loops | t11: zip / q31 (gap), Holm p | t12 | t13 |
|---|---|---|---|
| 0 | 0.602 / 0.574 (+0.028), 0.17 | 0.856 / 0.656 (+0.200), 9e-21 | 0.968 / 0.754 (+0.214), 1e-30 |
| 500 | 0.866 / 0.682 (+0.184), 2e-15 | 0.908 / 0.626 (+0.282), 9e-36 | 0.942 / 0.654 (+0.288), 3e-35 |
| 16,000 | 0.710 / 0.532 (+0.178), 5e-9 | 0.714 / 0.586 (+0.128), 9e-7 | 0.738 / 0.588 (+0.150), 9e-9 |

**Learning from 0 to 500 loops, within each arm** (paired over points, Holm over teachers):

| arm | t11 | t12 | t13 |
|---|---|---|---|
| item 31 | +0.108 (4e-6) | −0.030 (0.036) | −0.100 (2e-9) |
| zipper | +0.264 (9e-25) | +0.052 (0.008) | −0.026 (0.019) |

- **Item 31 calls +1 on 74-87 % of the points at θ = 0**, so its offset is already there before any training.
- **The twin's accuracy at θ = 0** (from theta0.json's twin P(1)) is 0.57-0.64 for t11 and 0.68-0.95 for t12 and t13.
  t11 is the teacher farthest from the start.

**Reading (raw readout, offset included):**

1. **The lead has two sources, and which one dominates depends on the teacher.**
   - **t12 and t13** (start already near the teacher): the zipper leads by +0.20 to +0.21 before any training. That
     is the circuit, not learning.
   - **t11** (start farther away): no lead at θ = 0 (+0.028, not significant). The lead appears through training:
     the zipper gains +0.264 against item 31's +0.108.
2. **The gap widens from 0 to 500 loops for all three teachers:** +0.156 (t11), +0.082 (t12), +0.074 (t13).
   - This is descriptive; no interaction test was declared.
   - In t13 the gap widens because item 31 degrades more (−0.100 against −0.026), not because the zipper learns more.
3. **Where training has room (t11), the zipper learns more; where the start is near the teacher (t13), it degrades
   less.** Both are consistent with a cleaner training signal (the gradient-direction hypothesis), but the cause has
   not been tested.
4. **Vanity and essential numbers:**
   - **Vanity:** "the zipper leads by +0.18 to +0.29 at 500 loops".
   - **Essential:**
     - In 2 of 3 teachers about +0.2 of it is there before training (the circuit's readout, item 31's offset
       included).
     - Training adds +0.07 to +0.16 to the gap in 3/3.
     - In the one teacher that needs learning, the zipper's own gain is +0.264 against +0.108.
5. **Pending:**
   - the δ-free version, once theta0_lam.json arrives;
   - the stand-in only, three teachers.

**Correction to Addendum 2.** The worry that the 500-loop lead might be "the same near-initial model read out better"
is half right.

- **True for t12 and t13**, raw.
- **Not true for t11**, where the lead is built by training.

---

## Addendum 5 (2026-10-23 08:25 CEST): θ = 0 δ-free; item 31 does not learn in the first 500 loops, the zipper does

**Data.** θ = 0's λ and δ come from home's theta0_lam.json (toqb.undamp.estimate, the 64 training inputs, 1,024
trajectories, seed predict.seed + 5, as undamp_run).

| arm | δ at θ = 0, t11 / t12 / t13 | λ at θ = 0 |
|---|---|---|
| item 31 | +0.048 / +0.073 / +0.074 | 0.11-0.20 |
| zipper | +0.017 / +0.017 / +0.019 | 0.14-0.15 |

The δ at 500 and 16,000 loops come from u500 and undamp_final. Each point is δ-free: the sign of z − δ, shot-free,
on the stand-in. Script: `theta0_dfree.py`.

**Zipper against item 31, δ-free:**

| loops | t11: zip / q31 (gap), Holm p | t12 | t13 |
|---|---|---|---|
| 0 | 0.636 / 0.718 (−0.082), 0.001 | 0.882 / 0.814 (+0.068), 0.001 | 0.974 / 0.788 (+0.186), 1e-21 |
| 500 | 0.876 / 0.736 (+0.140), 4e-11 | 0.932 / 0.800 (+0.132), 5e-14 | 0.912 / 0.768 (+0.144), 2e-13 |
| 16,000 | 0.704 / 0.712 (−0.008), 0.8 | 0.698 / 0.734 (−0.036), 0.42 | 0.748 / 0.724 (+0.024), 0.56 |

**Learning from 0 to 500 loops within each arm, δ-free** (paired over points, Holm over teachers):

| arm | t11 | t12 | t13 |
|---|---|---|---|
| item 31 | +0.018 (0.42) | −0.014 (0.42) | −0.020 (0.064) |
| zipper | +0.240 (7e-20) | +0.050 (8e-4) | −0.062 (3e-7) |

**Reading:**

1. **At θ = 0 the circuits differ less than the raw numbers said.** Raw, the zipper led by +0.03 to +0.21; most of
   that was item 31's offset.
   - δ-free the picture is mixed: item 31 is better for t11 (−0.082), the zipper for t12 and t13 (+0.068, +0.186).
   - Addendum 4's reading 1 ("about +0.2 before training is the circuit") is corrected: it was largely item 31's
     offset.
2. **In the first 500 loops item 31 does not learn, once its offset is removed:** +0.018, −0.014 and −0.020, none
   significant.
   - Its raw gain in t11 (+0.108, Addendum 4) was its offset changing, not the model improving.
3. **The zipper does learn where there is room:**
   - t11: +0.240, from 0.636 to 0.876;
   - t12: +0.050.
   - It loses from a near-perfect start in t13: 0.974 to 0.912.
4. **So the 500-loop δ-free lead (+0.13 to +0.14 in 3/3) is built by the zipper's training in t11 and t12, and in t13
   is what remains of a head start.**
5. **Long training erases it:** the δ-free gap at 16,000 loops is about 0 in 3/3, with both arms near 0.70-0.75.
6. **For the study-method hypothesis** (a cleaner training signal from the zipper):
   - **Supported early:** item 31's training signal moves the model nowhere δ-free; the zipper's improves it.
   - **Not supported over long training:** there the zipper drifts back down.
   - **Unconfirmed:** the mechanism. It is consistent with the higher gradient cosine seen in the data/gradient test,
     but that has not been tested as a cause.
7. **Vanity and essential numbers:**
   - **Vanity:** "the zipper leads by +0.18 to +0.29 at 500 loops".
   - **Essential:** δ-free and shot-free, the zipper's own early learning is +0.24 and +0.05 against item 31's about
     0 (2 of 3 teachers). The lead is +0.13 to +0.14 at 500 loops and about 0 at 16,000 loops. With 250 shots it
     largely disappears (λ ≈ 0.15).
8. **Limits:**
   - the stand-in only;
   - λ and δ are the twin's estimates, and δ over-corrects item 31 (+1 calls 32-42 %);
   - three teachers;
   - this whole chain is post hoc, not declared.
   - A declared test on fresh teachers, with a teacher farther from the start, is needed before any claim.
