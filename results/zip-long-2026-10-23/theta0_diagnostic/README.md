# Diagnostic (post hoc, 2026-10-23): the untrained model (theta = 0) through both circuits

Same logical model in both arms, so any difference is the circuit's readout. `toqb.fruit_common.predict_verify` at
theta = 0 on each run's task and stand-in (fresh H100 pod); theta0.json SHA-256
ae266ed5e3804de17033bcb576f05ed79a019cd96761e25c966c4fea70fe89db. Shot-free stand-in output; AUC (offset- and
scale-free), paired DeLong test, not declared.

| teacher | noiseless theta = 0: acc / AUC | stand-in AUC at theta = 0: zipper / item 31 (p) | at 500 loops (p) | change of the zipper's lead |
|---|---|---|---|---|
| 11 | 0.656 / 0.731 | 0.717 / 0.783 (5e-6) | 0.957 / 0.864 (9e-11) | -0.066 -> +0.093 |
| 12 | 0.904 / 0.964 | 0.951 / 0.908 (2e-5) | 0.978 / 0.879 (2e-14) | +0.043 -> +0.099 |
| 13 | 0.962 / 0.997 | 0.996 / 0.947 (8e-9) | 0.984 / 0.899 (5e-11) | +0.049 -> +0.085 |

Reading: both effects are there.
- Readout: on the two teachers near the start (12, 13) the zipper's circuit already reads the same untrained model
  out better (AUC +0.04 to +0.05). On teacher 11 item 31's reads it out better (-0.066).
- Learning: from theta = 0 to 500 loops the zipper's lead grows in 3 of 3, most on teacher 11, the one task that needs
  learning (theta = 0 scores 0.66 noiseless): the zipper's AUC rises 0.717 to 0.957, item 31's 0.783 to 0.864.
- So the workplace's withdrawal of "learns better early" (its Addendum 2) is too strong: the readout part is real on
  the near-start teachers, and the learning part shows where learning is needed. One teacher of that kind is not a
  claim; the declared test with a teacher far from the start is the clean one.
- Accuracy with the 500-loop delta shift is in the commit message's run (approximate: delta was not measured at
  theta = 0); AUC is the cleaner measure here.

## With theta = 0's own lam and delta (theta0_lam.json, run on the pod after all; post hoc)

lam / delta at theta = 0: item 31 0.148 / +0.048, 0.200 / +0.073, 0.114 / +0.074; zipper 0.138 / +0.017, 0.149 /
+0.017, 0.137 / +0.019 (teachers 11-13). Shot-free stand-in accuracy with each run's delta removed, McNemar, Holm:

| teacher | theta = 0: zipper / item 31 (Holm p) | 500 loops (delta of that point) | gain 0 -> 500: zipper / item 31 |
|---|---|---|---|
| 11 | 0.636 / 0.718 (1e-3, item 31 ahead) | 0.878 / 0.736 | +0.242 / +0.018 |
| 12 | 0.882 / 0.814 (1e-3) | 0.932 / 0.802 | +0.050 / -0.012 |
| 13 | 0.974 / 0.788 (1e-21) | 0.912 / 0.768 | -0.062 / -0.020 |

The same picture as the AUC: on teacher 11, the task that needs learning, item 31 reads the untrained model out
better, and in 500 loops the zipper gains +0.24 against item 31's +0.02 and overtakes it; on teachers 12 and 13 the
zipper's lead is mostly there before training (readout), and training adds little or takes some away.
