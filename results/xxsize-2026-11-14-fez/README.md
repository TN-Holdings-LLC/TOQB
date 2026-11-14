# xxsize-2026-11-14-fez (ibm_fez) (prereg/xxsize_2026-11-14.md)

- Declaration pushed 2026-11-14T12:25:45+01:00 (reflog "update by push"); queue read 2026-11-14T11:26:04.811419+00:00 (pending {'ibm_marrakesh': 1, 'ibm_fez': 1, 'ibm_kingston': 243}).
- Job n33: 34 circuits, 40.9 s by the model, circuits_sha256 ddeb5d86e9d1..., PASS carried over from notes/xxsize_2026-11-14/trybuild/ibm_fez_N33; job id dbs4chfv5hds73dihoq0; job files returned byte-identical.
  - n33_ans.json sha256 812719dde1fa... (released in answers/)
- Job n81: 34 circuits, 40.9 s by the model, circuits_sha256 16125d643330..., PASS carried over from notes/xxsize_2026-11-14/trybuild/ibm_fez_N81; job id dbs4ck1abdes73fqo1fg; job files returned byte-identical.
  - n81_ans.json sha256 0451ef729915... (released in answers/)
- Files over 50 MB are gzipped (`gunzip` restores them).

## Scorer output

### n33

```
N33_th0785_s02: CZ 128  READS (MSE 0.0155 / mean square 0.2746)  AGREES 8/33  r 0.819  charge 0.000  floor +0.968 mirror +0.711
N33_th0785_s04: CZ 256  READS (MSE 0.0217 / mean square 0.2239)  AGREES 3/33  r 0.739  charge 0.000  floor +0.966 mirror +0.499
N33_th0785_s08: CZ 512  READS (MSE 0.0532 / mean square 0.2125)  AGREES 1/33  r 0.547  charge 0.000  floor +0.967 mirror +0.234
N33_th0785_s12: CZ 768  READS (MSE 0.0802 / mean square 0.2236)  AGREES 3/33  r 0.428  charge 0.000  floor +0.967 mirror +0.116
N33_th0785_s16: CZ 1024  READS (MSE 0.0943 / mean square 0.2007)  AGREES 3/33  r 0.334  charge 0.000  floor +0.967 mirror +0.047
N33_th1571_s02: CZ 128  READS (MSE 0.0402 / mean square 1.0000)  AGREES 0/33  r 0.831  charge 0.000  floor +0.967 mirror +0.768
N33_th1571_s04: CZ 256  READS (MSE 0.0909 / mean square 1.0000)  AGREES 0/33  r 0.732  charge 0.000  floor +0.967 mirror +0.619
N33_th1571_s08: CZ 512  READS (MSE 0.2242 / mean square 1.0000)  AGREES 0/33  r 0.562  charge 0.000  floor +0.967 mirror +0.381
N33_th1571_s12: CZ 768  READS (MSE 0.3687 / mean square 1.0000)  AGREES 0/33  r 0.418  charge 0.000  floor +0.969 mirror +0.203
N33_th1571_s16: CZ 1024  DOES NOT READ (MSE 0.5307 / mean square 1.0000)  AGREES 0/33  r 0.285  charge 0.000  floor +0.968 mirror +0.106
```

### n81

```
N81_th0785_s02: CZ 320  READS (MSE 0.0181 / mean square 0.2600)  AGREES 17/81  r 0.793  charge 0.000  floor +0.973 mirror +0.663
N81_th0785_s04: CZ 640  READS (MSE 0.0316 / mean square 0.2046)  AGREES 4/81  r 0.674  charge 0.000  floor +0.972 mirror +0.410
N81_th0785_s08: CZ 1280  READS (MSE 0.0612 / mean square 0.1786)  AGREES 3/81  r 0.464  charge 0.000  floor +0.972 mirror +0.142
N81_th0785_s12: CZ 1920  DOES NOT READ (MSE 0.0937 / mean square 0.1740)  AGREES 1/81  r 0.292  charge 0.000  floor +0.970 mirror +0.044
N81_th0785_s16: CZ 2560  DOES NOT READ (MSE 0.1167 / mean square 0.1774)  AGREES 0/81  r 0.201  charge 0.000  floor +0.970 mirror +0.006
N81_th1571_s02: CZ 320  READS (MSE 0.0559 / mean square 1.0000)  AGREES 0/81  r 0.804  charge 0.000  floor +0.970 mirror +0.718
N81_th1571_s04: CZ 640  READS (MSE 0.1491 / mean square 1.0000)  AGREES 0/81  r 0.657  charge 0.000  floor +0.971 mirror +0.514
N81_th1571_s08: CZ 1280  READS (MSE 0.3713 / mean square 1.0000)  AGREES 0/81  r 0.416  charge 0.000  floor +0.971 mirror +0.215
N81_th1571_s12: CZ 1920  DOES NOT READ (MSE 0.5930 / mean square 1.0000)  AGREES 0/81  r 0.236  charge 0.000  floor +0.969 mirror +0.059
N81_th1571_s16: CZ 2560  DOES NOT READ (MSE 0.7621 / mean square 1.0000)  AGREES 0/81  r 0.130  charge 0.000  floor +0.969 mirror +0.006
```

## Prediction (written before the data)

The three predictions are judged over both devices together: `notes/xxsize_2026-11-14/README.md`
(1 angle: failed, 12 of 20 within 0.05; 2 size: failed, 7 of 20 within 0.05; 3 the 0.293 line: held, 20 of 20).
This folder is recorded under the name xxsize-2026-11-14-fez so that the two devices' records do not overwrite
each other (the night spec `prereg/xxsize_2026-11-14_night.json` with only its name changed).

## Reproduce

`python reproduce.py xxsize-2026-11-14-fez-n33`, `python reproduce.py xxsize-2026-11-14-fez-n81`.
