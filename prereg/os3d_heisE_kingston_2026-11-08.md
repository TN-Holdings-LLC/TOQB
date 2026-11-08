# Declared: the three-layout comparison of heisE again, on ibm_kingston
(owner 2026-11-08 20:17 JST "キングストンで3方式"; a second device for `prereg/os3d_heisE_2026-11-08.md`, which ran on
ibm_marrakesh at 12:26 CET, results in `results/os3d-heisE-2026-11-08`.)

Declared before the device record of this run is fetched. A change after this commit is a new declared file.

Everything is as in heisE (and heisD, which it refers to): the problem, the three layouts (old, carry, line with rule
A), the builder command, the choice of the place (rule "top" over the mean of the three t = 1 mirrors), the verdicts,
the comparison and its shot bound, the predictions (carry - old >= 0 and line - old >= 0 at every t on the judged
place) and the limits. One change: the device is ibm_kingston, fixed by the owner, not chosen by the queue. The record
is fetched by `python -m psf_os fetch --backend ibm_kingston` after this commit is pushed. If no translation fits:
"not run".

Answers: the three tables of exact answers (old e00309e6..., carry 6fa523f1..., line b34d56e1...) were released with
the marrakesh run (`results/os3d-heisE-2026-11-08/answers`), so they are public before this run. They are computed by
committed code from the bond log of each place; the builder's answers must again equal the tables' entries.

Code at the declaring commit.
