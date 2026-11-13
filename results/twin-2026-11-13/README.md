# twin-2026-11-13 (ibm_marrakesh) (prereg/twin_2026-11-13.md)

- Declaration pushed 2026-11-13T11:33:36+01:00 (reflog "update by push"); queue read 2026-11-13T10:36:02.678514+00:00 (pending {'ibm_marrakesh': 0, 'ibm_fez': 0, 'ibm_kingston': 101}).
- Job xx: 16 circuits, 20.9 s by the model, circuits_sha256 0fb8e24d689d..., PASS carried over from night1113 prepare.log: twin_check ALL PASS, hub_check --mps-steps 4 ALL PASS; job id dbreon8k09pc73autk1g; job files returned byte-identical.
  - xx_ans.json sha256 be2deb83be2a... (released in answers/)
  - xx_ans_twin.json sha256 8644926c95cc... (released in answers/)
- Job hub: 16 circuits, 20.9 s by the model, circuits_sha256 74e8b3353f99..., PASS carried over from night1113 prepare.log: twin_check ALL PASS, hub_check s2/s4 ALL PASS; hub_s6_check.txt: s6 quimb PASS; job id dbreonujjaos73aiuob0; job files returned byte-identical.
  - hub_ans.json sha256 db805cec3b95... (released in answers/)
  - hub_ans_twin.json sha256 af8f7cf5b3ac... (released in answers/)
- Files over 50 MB are gzipped (`gunzip` restores them).

## Scorer output

### xx

```
N91_th0785_s04: user READS (MSE/msq 0.092, r 0.737) | twin READS (MSE/msq 0.073, r 0.754) | r_twin - r +0.017 | r_twin >= 0.293 True matches user verdict True | mirror +0.489
N91_th0785_s08: user READS (MSE/msq 0.186, r 0.599) | twin READS (MSE/msq 0.157, r 0.617) | r_twin - r +0.018 | r_twin >= 0.293 True matches user verdict True | mirror +0.227
N91_th0785_s12: user READS (MSE/msq 0.282, r 0.491) | twin READS (MSE/msq 0.261, r 0.499) | r_twin - r +0.007 | r_twin >= 0.293 True matches user verdict True | mirror +0.126
```

### hub

```
L20_s2_U4: user READS (MSE/msq 0.041, r 0.854) | twin READS (MSE/msq 0.050, r 0.803) | r_twin - r -0.051 | r_twin >= 0.293 True matches user verdict True | mirror +0.608
L20_s4_U4: user READS (MSE/msq 0.184, r 0.721) | twin READS (MSE/msq 0.135, r 0.674) | r_twin - r -0.047 | r_twin >= 0.293 True matches user verdict True | mirror +0.266
L20_s6_U4: user DOES NOT READ (MSE/msq 0.506, r 0.514) | twin READS (MSE/msq 0.245, r 0.553) | r_twin - r +0.039 | r_twin >= 0.293 True matches user verdict False | mirror +0.099
```

## Prediction (written before the data)

- "|r_twin - r| <= 0.05 for the three XX pairs and for Hubbard at 2 and 4 steps": **failed narrowly** (XX +0.017 /
  +0.018 / +0.007; Hubbard 2 steps -0.051, 4 steps -0.047).
- Hubbard at 6 steps (open): r_twin - r = +0.039; the twin READS, the user circuit does not (MSE / mean square 0.506).
- "r_twin >= 0.293 matches the user circuit's READS in at least 5 of the 6 pairs": held (5 of 6; the miss is Hubbard
  6 steps).

## Beside (not judged, never used to correct)

- The twin followed the kept share r within 0.051 in all six pairs (largest gap Hubbard 2 steps). For XX it ran
  slightly above r (+0.007 to +0.018), for Hubbard below at 2 and 4 steps and above at 6.
- Hubbard's user error split as z = r e + rest: (1 - r)^2 = 0.021 / 0.078 / 0.236 and rest 0.019 / 0.106 / 0.269 at
  2 / 4 / 6 steps. At 6 steps the rest (shape errors) is larger than the shrink, which the twin cannot see: its line
  (r_twin >= 0.293) says "reads", the user circuit does not. This is the limit stated in psf_os/twin.py.
- XX on marrakesh read to 12 steps (r 0.49; fez on 11-12: r 0.33, did not read at 12). Another device-day, not the
  same chain.
- First night with gpu/night.py: prepare built both jobs on marrakesh (91-qubit chain placeable on today's record),
  the new circuits were checked before submission (twin_check and hub_check ALL PASS; the 6-step check finished after
  a restart), record verified the job files and reproduced both scores.

## Reproduce

`python reproduce.py twin-2026-11-13-xx`, `python reproduce.py twin-2026-11-13-hub`.
