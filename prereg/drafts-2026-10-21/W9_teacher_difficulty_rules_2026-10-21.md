# W9. How hard the teacher is: rules fixed before training (proposal, 2026-10-21)

**Status.** Written at the workplace on 2026-10-21. This is a proposal: the owner decides. It does not apply to
today's match, which is fixed at angle 1.0. Nothing was run.

**The problem.** At teacher angle 0.3, θ = 0 already scores 0.948 noiseless. That task measures the starting point,
not the method. The risk on the other side is that choosing the task by any rule becomes choosing a lane: a task that
happens to suit one method.

| | A. One fixed angle, θ = 0 always reported | B. Angle set by θ = 0's training accuracy | C. A fixed ladder of angles, all reported |
|---|---|---|---|
| rule | the angle is declared before any run (for example 1.0); every report shows Z (θ = 0) next to the methods, and a win needs E4 > Z (as today's W8) | the smallest angle on a fixed list (0.2, 0.4, …, 2.0) at which θ = 0's **noiseless training** accuracy is ≤ 0.65, computed before any method runs | three angles declared in advance (proposed: 0.3, 1.0, 2.0), every method run at all three, every result reported |
| what it measures | how a method does on one stated task, against doing nothing | how a method does on a task that is "not solved by the start", with the threshold stated | how a method's advantage changes with difficulty, from easy (θ = 0 good) to hard |
| lane risk | low: no selection. An angle that happens to be easy or hard is visible through Z | moderate: the task is selected, but only by θ = 0's behaviour (shared by all methods). It still conditions on the shared start, which can favour methods that leave θ = 0 quickly. It uses training points only (no test leakage) and the noiseless model (no calibration) | none: no selection at all; the ladder is fixed before any result |
| cost | none beyond Z (minutes) | noiseless θ = 0 on 64 training points per listed angle: seconds on a CPU, before the match | 3 × the match's GPU time (today's match is about 3-4 h for one angle) |
| weakness | one task can mislead on its own | a threshold and a list are still choices; a scan over a list is a small search | expensive; at 0.3 the result is known to be dominated by the start |

**Recommendation (one): C, the fixed ladder.**

- It is the only rule with no selection at all, so it cannot become a lane.
- It answers the question that matters, which is where, if anywhere, the formula beats the search.
- It reports the easy end too, where C has been seen to damage a good start (0.754 against θ = 0's 0.948, noiseless).

**If the cost is too high,** A is the honest fallback: one declared angle, with Z always reported and required to be
beaten. B is not recommended, because it selects.

**Points for the owner to decide:**

1. A, B or C, and the angle or angles.
2. For B, if chosen: the threshold (0.65 proposed) and the list.
3. Whether the ladder's angles are run at both depths (L 8 and 16), which doubles the cost again.
