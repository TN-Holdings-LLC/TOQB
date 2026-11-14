# xxcone-2026-11-14 (ibm_marrakesh) (prereg/xxcone_2026-11-14.md)

- Declaration pushed 2026-11-14T13:01:24+01:00 (reflog "update by push"); queue read 2026-11-14T12:01:41.994174+00:00 (pending {'ibm_marrakesh': 0, 'ibm_fez': 0, 'ibm_kingston': 242}).
- Job n33: 34 circuits, 40.9 s by the model, circuits_sha256 e039d7463d9b..., PASS carried over from notes/xxsize_2026-11-14/trybuild/ibm_marrakesh_N33; job id dbs4sh9abdes73fqoh80; job files returned byte-identical.
  - n33_ans.json sha256 812719dde1fa... (released in answers/)
- Job n81: 34 circuits, 40.9 s by the model, circuits_sha256 e4d434d6df05..., PASS carried over from notes/xxsize_2026-11-14/trybuild/ibm_marrakesh_N81; job id dbs4sjok09pc73avon0g; job files returned byte-identical.
  - n81_ans.json sha256 aa9571b968a2... (released in answers/)
- Files over 50 MB are gzipped (`gunzip` restores them).

## Scorer output

### n33

```
N33_th0785_s02: CZ 128  READS (MSE 0.0265 / mean square 0.2746)  AGREES 11/33  r 0.801  charge 0.000  floor +0.968 mirror +0.735
N33_th0785_s04: CZ 256  READS (MSE 0.0333 / mean square 0.2239)  AGREES 7/33  r 0.717  charge 0.000  floor +0.971 mirror +0.497
N33_th0785_s08: CZ 512  READS (MSE 0.0514 / mean square 0.2125)  AGREES 1/33  r 0.582  charge 0.000  floor +0.971 mirror +0.244
N33_th0785_s12: CZ 768  READS (MSE 0.0686 / mean square 0.2236)  AGREES 3/33  r 0.494  charge 0.000  floor +0.970 mirror +0.137
N33_th0785_s16: CZ 1024  READS (MSE 0.0834 / mean square 0.2007)  AGREES 3/33  r 0.396  charge 0.000  floor +0.971 mirror +0.092
N33_th1571_s02: CZ 128  READS (MSE 0.0558 / mean square 1.0000)  AGREES 0/33  r 0.824  charge 0.000  floor +0.970 mirror +0.815
N33_th1571_s04: CZ 256  READS (MSE 0.0742 / mean square 1.0000)  AGREES 0/33  r 0.770  charge 0.000  floor +0.970 mirror +0.692
N33_th1571_s08: CZ 512  READS (MSE 0.1399 / mean square 1.0000)  AGREES 0/33  r 0.653  charge 0.000  floor +0.970 mirror +0.505
N33_th1571_s12: CZ 768  READS (MSE 0.2235 / mean square 1.0000)  AGREES 0/33  r 0.546  charge 0.000  floor +0.971 mirror +0.344
N33_th1571_s16: CZ 1024  READS (MSE 0.2957 / mean square 1.0000)  AGREES 0/33  r 0.462  charge 0.000  floor +0.971 mirror +0.235
```

### n81

```
N81_th0785_s02: CZ 320  READS (MSE 0.0208 / mean square 0.2600)  AGREES 23/81  r 0.803  charge 0.000  floor +0.971 mirror +0.699
N81_th0785_s04: CZ 640  READS (MSE 0.0305 / mean square 0.2046)  AGREES 6/81  r 0.695  charge 0.000  floor +0.972 mirror +0.454
N81_th0785_s08: CZ 1280  READS (MSE 0.0505 / mean square 0.1786)  AGREES 3/81  r 0.533  charge 0.000  floor +0.971 mirror +0.222
N81_th0785_s12: CZ 1920  READS (MSE 0.0707 / mean square 0.1740)  AGREES 2/81  r 0.416  charge 0.000  floor +0.971 mirror +0.130
N81_th0785_s16: CZ 2560  DOES NOT READ (MSE 0.0920 / mean square 0.1774)  AGREES 3/81  r 0.325  charge 0.000  floor +0.970 mirror +0.087
N81_th1571_s02: CZ 320  READS (MSE 0.0461 / mean square 1.0000)  AGREES 0/81  r 0.829  charge 0.000  floor +0.971 mirror +0.799
N81_th1571_s04: CZ 640  READS (MSE 0.0832 / mean square 1.0000)  AGREES 0/81  r 0.747  charge 0.000  floor +0.970 mirror +0.668
N81_th1571_s08: CZ 1280  READS (MSE 0.1666 / mean square 1.0000)  AGREES 0/81  r 0.619  charge 0.000  floor +0.971 mirror +0.473
N81_th1571_s12: CZ 1920  READS (MSE 0.2772 / mean square 1.0000)  AGREES 0/81  r 0.496  charge 0.000  floor +0.971 mirror +0.328
N81_th1571_s16: CZ 2560  READS (MSE 0.3767 / mean square 1.0000)  AGREES 0/81  r 0.404  charge 0.000  floor +0.971 mirror +0.211
```

## Prediction (written before the data)

`python notes/xxcone_2026-11-14/cone.py ibm_marrakesh_n33 ibm_marrakesh_n81` (run in this folder; `cone_result.json`).
Gap g = r(N = 33) - r(N = 81) on the same qubits, by block (far 0-10, mid 11-21, near 22-32):

| theta | layers | far | mid | near |
|---|---|---|---|---|
| pi/4 | 8 | +0.019 | -0.014 | +0.025 |
| pi/4 | 16 | +0.010 | +0.002 | +0.108 |
| pi/4 | 32 | +0.021 | +0.058 | +0.189 |
| pi/4 | 48 | +0.061 | +0.116 | +0.222 |
| pi/4 | 64 | +0.007 | +0.201 | +0.200 |
| pi/2 | 8 | -0.005 | -0.007 | +0.028 |
| pi/2 | 16 | +0.007 | +0.017 | +0.080 |
| pi/2 | 32 | +0.002 | +0.057 | +0.111 |
| pi/2 | 48 | +0.045 | +0.096 | +0.134 |
| pi/2 | 64 | +0.108 | +0.082 | +0.124 |

1. "pi/4, far block: |g| <= 0.03 at every depth": **failed**, by one cell: 48 layers, +0.061 (the other four
   +0.007 to +0.021; 64 layers +0.007).
2. "pi/4 at 16 and 32 layers: g(near) - g(far) >= 0.05": **held** (+0.098, +0.168).
3. "pi/2, far block: |g| <= 0.03 up to 32 layers and g >= 0.03 at 64": **held** (-0.005 / +0.007 / +0.002; +0.108).

Beside: the order in which the gap opens came back as in the first run: the near block first (16 layers), the middle
block from 32 layers, the far block last (pi/2 at 48-64 layers). Whole-chain r (pi/4), first run 12:30 / this run
13:04: N = 33 0.830 0.732 0.617 0.505 0.411 / 0.801 0.717 0.582 0.494 0.396; N = 81 0.799 0.693 0.540 0.427 0.345 /
0.803 0.695 0.533 0.416 0.325.

## Reproduce

`python reproduce.py xxcone-2026-11-14-n33`, `python reproduce.py xxcone-2026-11-14-n81`.
