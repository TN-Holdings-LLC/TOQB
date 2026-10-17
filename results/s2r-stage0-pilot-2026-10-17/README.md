# S2R stage 0: the exploratory pilot (2026-10-17, authors' cloud; not scored)

The runs that chose sigma_0 and its decay for the pre-registration `prereg/2026-10-17-s2r-stage0.md` (section 7):
seed 901, N = 1,000 candidates per loop, both compilers. `plan_A.json` (sigma_0 0.3, decay 0.8), `plan_B.json`
(0.6, 0.7), `plan_D.json` (1.0, 0.7, chosen); `r_<setting>_<compiler>.json` are the S2R records, `spsa_D_*.json`
the device-only SPSA records. A first start of setting A died for lack of memory (8,000 circuits simulated at once);
the simulator was then made to take 400 at a time, and every record here comes from runs after that change. Setting
C (0.15, 0.9) was not run, and a variant with simulator-only generations inside each loop was written but not run or
kept.
