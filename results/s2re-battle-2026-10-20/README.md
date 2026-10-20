# Design C against design E, 2026-10-20 (exploratory; not pre-registered, not a claim)

Owner, 2026-10-20: the device stamp is postponed (later C + E in one job); "eliminating search is the main
proposition"; "let C and E fight first"; "the opponent is no longer Qiskit, it is ourselves". E's form was left open.

Task in every round: S2 teacher-student, n = 10, enc pi/2, teacher_seed 4, gap 0.2, 64 training points (balanced),
500 test points, model <Z0> of the PSF circuit (`toqb.task_loop`), loss and score as in design C.
Accuracy is on the 500 test points (one standard error about 0.02); CE uses p = (1 + z) / 2 (`s2r2._ce`).

## The designs

- **C** (`toqb.s2rc`): SPSA-like antithetic gradient, 8 directions, batch 4, h 0.1, lr 0.4, 2,000 loops, from
  uniform(-1, 1) (the rehearsal) or from theta = 0 ("C0").
- **E, one formula** (`toqb/s2re.py`): tangent at theta0 = 0 by parameter shift, theta* = pinv(G)(y tau - f0),
  tau = rms(f0). No search, no random draws, no learning rate.
- **E2** (`cloud/round3.py`): E's formula iterated (Gauss-Newton, min-norm step).
- **E3** (`cloud/round4.py`): exact per-parameter solve. Each parameter is one rotation, so every output is exactly
  a + b cos u + c sin u along it (checked to 6 digits at a fourth angle); C's loss mean((1 - y f)/2) is linear in f,
  so the minimum along u is atan2(c, b). Fixed sweep order from theta = 0.
- **E4** (`cloud/round5.py`): E3's exact per-parameter sinusoids with a proper scoring rule as the loss, Brier
  mean(((f - y)/2)^2) or CE -mean(log((1 + y f)/2)); the global minimum over one period is found on the explicit
  formula (4,096 angles and a parabola polish; no circuit calls in that step). Known idea: the same principle as
  Rotosolve / NFT (not checked by search on this day); what is new here is the fight against C on C's task.

## Noiseless rounds (cloud, exact <Z0>, L 8, seed 201)

| teacher angle | theta = 0 (no learning) | C | E one formula | E2 (iterations 1/2/3) | E3 (sweeps 1/2/3) | E4 Brier (sweeps 1/2) | E4 CE (sweeps 1/2/3) |
|---|---|---|---|---|---|---|---|
| 0.3 | 0.948 / CE 0.297 | 0.754 / 0.501 (from 0) | **0.966** / 0.318 | 0.966 / 0.460 / 0.466 | 0.916 / 0.934 / 0.940 | - | - |
| 1.0 | 0.596 / CE 0.764 | 0.714 / 0.559 (from uniform) | 0.542 / 0.731 | 0.542 / 0.484 / 0.514 | 0.612 / 0.614 / 0.628 | 0.632 / **0.722** (CE 0.577) | 0.576 / 0.686 / 0.718 (CE 0.579) |

Round 1 (teacher 0.3): the six rehearsal models of C evaluated noiselessly: 0.730 to 0.810.

Reading:
- Teacher 0.3 sits next to theta = 0 (0.948 without learning): it measures the starting point, not the method.
  C started at 0 ends below not learning (0.754 < 0.948): the search damages a good start there.
- E's one formula fails at teacher 1.0 (first order is wrong for steps of radians). E2 diverges (|theta|max 79 to 175
  rad). E3 is stable and monotone on the training loss but stalls at 0.628 on test.
- E4 Brier at sweep 2 reaches 0.722 against C's 0.714, at about a third of C's wall time (505 s against 1,380 s).
  The difference is inside one standard error: a tie, one seed, one teacher, noiseless. C's CE is still better
  (0.559 against 0.577).
- Lost: E4 Brier sweeps 3 to 4 and E3 teacher 1.0 sweep 4 (the cloud workspace stops detached processes some
  minutes after a reply; the outputs end where they end).

## Noisy round on the pod (`pod_battle_1/`, A100, teacher 0.3, PSF arm, stand-in snapshot:marrakesh)

Sizes of the rehearsal (T_pred 1,024, R 20,000). E's runs were stopped (FEAT 1,024 x (2d + 1) circuits per point was
far too large: E_L8 about 5x and E_L16 about 20x C0 L8's training; my sizing error). No noisy E result.

| | C from uniform (rehearsal, mean of 3) | C0 from 0 (mean of 3) | C0 inside the 99 % interval |
|---|---|---|---|
| L 8 stand-in accuracy / CE | 0.745 / 0.569 | **0.815** / **0.556** | 3 / 3 |
| L 16 stand-in accuracy / CE | 0.601 / 0.634 | **0.632** / **0.627** | 3 / 3 |

Per run (C0): L8 s201 0.825 / 0.5563, s202 0.825 / 0.5504, s203 0.795 / 0.5613; L16 s201 0.618 / 0.6273,
s202 0.618 / 0.6285, s203 0.660 / 0.6264.

Reading: the start at 0 helps C under noise; that is the start, not the search. Missing: theta = 0 scored on the
stand-in without learning (the noisy counterpart of 0.948), the first number to take next.

## Next (owner, 2026-10-20: dig deeper first, spend the 2 device minutes only when everything is ready)

1. Noisy theta = 0, no learning, on the stand-in (prediction only).
2. E4 Brier over more seeds and teachers (teacher 1.0 and between), against C at equal circuit evaluations.
3. E4 on the GPU twin (batched sinusoid evaluation), then the noisy fight against C on the pod.
4. Only then the C + E pre-registration and the device stamp.
