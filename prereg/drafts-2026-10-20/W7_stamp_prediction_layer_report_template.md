# Design C stamp, 2026-10-21: result, then the prediction layer (report template)

**Template written at the workplace, 2026-10-20.** Fill in after the job; every `[ ]` comes from an artifact. The
design C result is the official one. The prediction layer is a second view of the same job and changes nothing in
it.

**Job:**

- backend `[ ]`; job ID `[ ]`;
- calibration fetched `[ ]`, at submission `[ ]`, at result `[ ]`;
- QPU time billed `[ ]` s (modelled `[ ]` s);
- manifest SHA-256 `[ ]`; reference-twin outputs SHA-256 `[ ]`, fixed before submission at `[ ]` CEST.

## 1. Design C's result (pre-registered; `s2rc_device score`)

| cell | P | correct (strict) | H1 p (Holm, 4 cells) | H1 | CE (pred) | in 99 % (twin + shots / shots) | accuracy (pred) | mean deviation (shot floor) |
|---|---|---|---|---|---|---|---|---|
| PSF L 8 | 150 | `[ ]` | `[ ]` | `[ ]` | `[ ]` (`[ ]`) | `[ ]` / `[ ]` | `[ ]` (`[ ]`) | `[ ]` (`[ ]`) |
| Qiskit L 8 | 150 | `[ ]` | `[ ]` | `[ ]` | `[ ]` (`[ ]`) | `[ ]` / `[ ]` | `[ ]` (`[ ]`) | `[ ]` (`[ ]`) |
| PSF L 16 | 500 | `[ ]` | `[ ]` | `[ ]` | `[ ]` (`[ ]`) | `[ ]` / `[ ]` | `[ ]` (`[ ]`) | `[ ]` (`[ ]`) |
| Qiskit L 16 | 500 | `[ ]` | `[ ]` | `[ ]` | `[ ]` (`[ ]`) | `[ ]` / `[ ]` | `[ ]` (`[ ]`) | `[ ]` (`[ ]`) |

**H2** (PSF's deviation smaller than Qiskit's; Wilcoxon, Holm over 2 depths):

- L 8: mean d `[ ]`, p `[ ]`, `[ ]`;
- L 16: mean d `[ ]`, p `[ ]`, `[ ]`.

## 2. The prediction layer (TOQB v0.2 layer 4; a second view, not a test)

**Setup.**

- Twin: `traj2` (T = 1,024). Reference twin: Aer, `NoiseModel.from_backend` on the fetched Target (T = `[ ]`).
- Truth tier: **device**. Measurement kind: shots (N = 250).
- Claimable `[ ]`: this needs the prediction fixed by hash before submission and the order of the times confirmed.

| cell | I over Aer, per point (nats) | I over chance, per point | z | coverage 50 / 90 / 99 % | 99 % coverage, class +1 / −1 | CE in interval (R1) | CE gap (R2) | accuracy in interval (R1) | accuracy gap (R2) | prediction cost: GPU s / $ |
|---|---|---|---|---|---|---|---|---|---|---|
| PSF L 8 | `[ ]` | `[ ]` | `[ ]` | `[ ]` / `[ ]` / `[ ]` | `[ ]` / `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` / `[ ]` |
| Qiskit L 8 | `[ ]` | `[ ]` | `[ ]` | `[ ]` / `[ ]` / `[ ]` | `[ ]` / `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` / `[ ]` |
| PSF L 16 | `[ ]` | `[ ]` | `[ ]` | `[ ]` / `[ ]` / `[ ]` | `[ ]` / `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` / `[ ]` |
| Qiskit L 16 | `[ ]` | `[ ]` | `[ ]` | `[ ]` / `[ ]` / `[ ]` | `[ ]` / `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` / `[ ]` |

**How to read the table:**

- I > 0 means traj2 gave the observed counts more probability than the reference did.
- z near 0 means traj2 was as sure as it should have been; z ≪ 0 means it was overconfident or biased.
- Coverage near the nominal level (and equal for both classes) means its per-point intervals were right.
- Coverage errs on the wide side by construction: the twin's Monte Carlo error is an upper bound.
- **The prediction cost** is traj2's run time. In the `s2rc` record, the prediction alone is inside `times.eval`,
  together with the learning curve; `[ ]` shows which figure was used.

**The same view for the reference twin** (against chance), so that both twins are shown on one measurement:

| cell | Aer: I over chance, per point | Aer: z | Aer: 99 % coverage |
|---|---|---|---|
| PSF L 8 / Qiskit L 8 / PSF L 16 / Qiskit L 16 | `[ ]` / `[ ]` / `[ ]` / `[ ]` | `[ ]` / `[ ]` / `[ ]` / `[ ]` | `[ ]` / `[ ]` / `[ ]` / `[ ]` |

## 3. Vanity and essential figures

| | figure |
|---|---|
| Vanity | "On a real IBM device, accuracy `[ ]` %, and the GPU twin's prediction fell inside its interval in `[ ]` of 4 cells" |
| Essential | H1 `[ ]` of 4 cells and H2 `[ ]` of 2 depths (the pre-registered result); traj2's information over Aer `[ ]` nats per point and z `[ ]` (the prediction layer); device use: 1 job, `[ ]` s of QPU (open plan); the twin and the compilers are written by the same authors as TOQB, except the reference (Aer, Qiskit level 2) |

## 4. Limits

**One device, one day, one job.** Every figure above comes from a single job on `[ ]`, on 2026-10-21, with one
calibration. It says nothing about other devices, other days or repeated jobs. The prediction layer's numbers are a
second view of the same counts, not an independent test. With n = 10, L = 8 / 16 and the two compilers as set, they
do not extend to other widths, depths or circuit families.

---

## Points for the owner to decide (W6 and W7)

1. **README v0.2:**
   - adopted as the draft for the repository, and when (after the stamp is proposed, so §12 can hold its first
     device numbers);
   - whether the v0.1 status line and the scored-runs block move to §13, as drafted, or stay at the top with §13
     pointing to them. The text is word for word in either case.
2. **README §12's stand-in table:** the columns (Bernoulli score over chance, 99 % coverage per class, CE inside,
   deviation rms) and whether it shows each seed or the mean of the three.
3. **This report's order:** design C's result first and the prediction layer second, as drafted. Also whether the
   reference twin's own row is shown (proposed: yes, so that both twins are seen on the same counts).
4. **Which figure counts as the prediction cost:** `times.eval` (it includes the learning curve), or the whole run's
   GPU time. Separating the prediction's own time is one of the post-stamp changes to `s2rc`.
5. **Wording of the vanity figure** when some cells fall outside their interval or fail H1. Proposed: keep the
   template's form and fill in the counts as they come.
