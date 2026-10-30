# Rule-only echo on ibm_fez (home, FIXED 2026-10-30 14:30 CET on the owner's go, before any fetch): is there an n-wall in the rule's readable depth

**Why.** On 2026-10-30 the rule's echo L* on ibm_kingston was about 23 at n = 20, 36 and 13-16 at n = 40, 72 (twice,
`results/device-2026-10-30/test2`, `test3E`, `rerun-rule-only`); on ibm_marrakesh it was 14-16 at every n. ibm_fez,
the third device of the Open Plan (the same family, Heron r2), is asked the same question. No value for fez is
predicted.

**Design (owner's go 2026-10-30 22:29 JST).**
- ibm_fez, a new fetch after this note. `fold:rule` only. The mirror echo exactly as in
  `rerun_rule_only_note.md` (1f883a77...): n = 20, 36, 40, 72; hz = 0, 0.1, 0.3; one-way L = 12, 25, 50
  (D = 24, 50, 100); h = 0.6; 4 inputs and 4 references; 500 shots; 288 circuits, one job, time model 52.2 s.
- Map-free placement as always (coupling graph and failed elements only). A placement refused or an acceptance
  failed is recorded, never replaced. Code `gpu/rerun_rule_only.sh` with `DEVICE=ibm_fez` and this note as `NOTE`.

**Judged: W (n-wall), per hz.** L*(n) is the rule's L* fitted over D = 24, 50, 100 (`kising_charge.decay_length`,
as in test 2). Let M = (L*(20) + L*(36)) / 2. **NO n-WALL** if both L*(40) and L*(72) lie in [0.8 M, 1.2 M];
**n-WALL** if either lies below 0.8 M; **ABOVE** if either lies above 1.2 M and none below; NOT JUDGED at an hz where
any of the four fits has no value. Overall: the verdict shared by all three hz, else MIXED.

**Reported, not judged.** L* and rho_E per cell; the same W computed for kingston (this morning and the rerun) and
marrakesh (this morning) beside fez's; the per-site minority rates at D = 24; the fetch's time and calibration time.
Nothing read from these numbers changes this note.
