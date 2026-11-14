# xxsize-2026-11-14-marrakesh (ibm_marrakesh) (prereg/xxsize_2026-11-14.md)

- Declaration pushed 2026-11-14T12:25:45+01:00 (reflog "update by push"); queue read 2026-11-14T11:26:04.811419+00:00 (pending {'ibm_marrakesh': 1, 'ibm_fez': 1, 'ibm_kingston': 243}).
- Job n33: 34 circuits, 40.9 s by the model, circuits_sha256 e039d7463d9b..., PASS carried over from notes/xxsize_2026-11-14/trybuild/ibm_marrakesh_N33; job id dbs4ccmjjaos73ajovrg; job files returned byte-identical.
  - n33_ans.json sha256 812719dde1fa... (released in answers/)
- Job n81: 34 circuits, 40.9 s by the model, circuits_sha256 e4d434d6df05..., PASS carried over from notes/xxsize_2026-11-14/trybuild/ibm_marrakesh_N81; job id dbs4cevv5hds73dihon0; job files returned byte-identical.
  - n81_ans.json sha256 aa9571b968a2... (released in answers/)
- Files over 50 MB are gzipped (`gunzip` restores them).

## Scorer output

### n33

```
N33_th0785_s02: CZ 128  READS (MSE 0.0127 / mean square 0.2746)  AGREES 9/33  r 0.830  charge 0.000  floor +0.965 mirror +0.729
N33_th0785_s04: CZ 256  READS (MSE 0.0223 / mean square 0.2239)  AGREES 6/33  r 0.732  charge 0.000  floor +0.966 mirror +0.506
N33_th0785_s08: CZ 512  READS (MSE 0.0366 / mean square 0.2125)  AGREES 1/33  r 0.617  charge 0.000  floor +0.967 mirror +0.239
N33_th0785_s12: CZ 768  READS (MSE 0.0581 / mean square 0.2236)  AGREES 3/33  r 0.505  charge 0.000  floor +0.967 mirror +0.141
N33_th0785_s16: CZ 1024  READS (MSE 0.0727 / mean square 0.2007)  AGREES 4/33  r 0.411  charge 0.000  floor +0.967 mirror +0.086
N33_th1571_s02: CZ 128  READS (MSE 0.0325 / mean square 1.0000)  AGREES 0/33  r 0.847  charge 0.000  floor +0.967 mirror +0.814
N33_th1571_s04: CZ 256  READS (MSE 0.0522 / mean square 1.0000)  AGREES 0/33  r 0.787  charge 0.000  floor +0.967 mirror +0.705
N33_th1571_s08: CZ 512  READS (MSE 0.1238 / mean square 1.0000)  AGREES 0/33  r 0.657  charge 0.000  floor +0.968 mirror +0.488
N33_th1571_s12: CZ 768  READS (MSE 0.1914 / mean square 1.0000)  AGREES 0/33  r 0.570  charge 0.000  floor +0.967 mirror +0.339
N33_th1571_s16: CZ 1024  READS (MSE 0.2841 / mean square 1.0000)  AGREES 0/33  r 0.471  charge 0.000  floor +0.966 mirror +0.234
```

### n81

```
N81_th0785_s02: CZ 320  READS (MSE 0.0229 / mean square 0.2600)  AGREES 25/81  r 0.799  charge 0.000  floor +0.969 mirror +0.701
N81_th0785_s04: CZ 640  READS (MSE 0.0326 / mean square 0.2046)  AGREES 6/81  r 0.693  charge 0.000  floor +0.968 mirror +0.462
N81_th0785_s08: CZ 1280  READS (MSE 0.0510 / mean square 0.1786)  AGREES 3/81  r 0.540  charge 0.000  floor +0.970 mirror +0.225
N81_th0785_s12: CZ 1920  READS (MSE 0.0703 / mean square 0.1740)  AGREES 3/81  r 0.427  charge 0.000  floor +0.970 mirror +0.130
N81_th0785_s16: CZ 2560  READS (MSE 0.0880 / mean square 0.1774)  AGREES 4/81  r 0.345  charge 0.000  floor +0.969 mirror +0.086
N81_th1571_s02: CZ 320  READS (MSE 0.0494 / mean square 1.0000)  AGREES 0/81  r 0.832  charge 0.000  floor +0.968 mirror +0.798
N81_th1571_s04: CZ 640  READS (MSE 0.0829 / mean square 1.0000)  AGREES 0/81  r 0.752  charge 0.000  floor +0.967 mirror +0.670
N81_th1571_s08: CZ 1280  READS (MSE 0.1721 / mean square 1.0000)  AGREES 0/81  r 0.614  charge 0.000  floor +0.969 mirror +0.470
N81_th1571_s12: CZ 1920  READS (MSE 0.2774 / mean square 1.0000)  AGREES 0/81  r 0.498  charge 0.000  floor +0.969 mirror +0.330
N81_th1571_s16: CZ 2560  READS (MSE 0.3932 / mean square 1.0000)  AGREES 0/81  r 0.392  charge 0.000  floor +0.969 mirror +0.217
```

## Prediction (written before the data)

The three predictions are judged over both devices together: `notes/xxsize_2026-11-14/README.md`
(1 angle: failed, 12 of 20 within 0.05; 2 size: failed, 7 of 20 within 0.05; 3 the 0.293 line: held, 20 of 20).
This folder is recorded under the name xxsize-2026-11-14-marrakesh so that the two devices' records do not overwrite
each other (the night spec `prereg/xxsize_2026-11-14_night.json` with only its name changed).

## Reproduce

`python reproduce.py xxsize-2026-11-14-marrakesh-n33`, `python reproduce.py xxsize-2026-11-14-marrakesh-n81`.
