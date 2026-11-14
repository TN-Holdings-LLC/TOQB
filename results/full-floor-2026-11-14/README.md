# full-floor-2026-11-14 (ibm_marrakesh) (prereg/full_floor_2026-11-13.md)

- Declaration pushed 2026-11-14T11:17:27+01:00 (reflog "update by push"); queue read 2026-11-14T10:17:50.511433+00:00 (pending {'ibm_marrakesh': 2, 'ibm_fez': 0, 'ibm_kingston': 236}).
- Job floor: 2 circuits, 5.2 s by the model, circuits_sha256 e5d1adac0895..., no pre-run check declared (measurement record); job id dbs3cavv5hds73dignug; job files returned byte-identical.
- Files over 50 MB are gzipped (`gunzip` restores them).

## Scorer output

### floor

```
151 qubits: 1 - z(|0>) median 0.0150, worst 0.560; 1 + z(|1>) median 0.0455, worst 0.406
```

## Prediction (written before the data)

None: a measurement record (`prereg/full_floor_2026-11-13.md`), night 2. Beside it, with night 1 on the same 151
qubits (the failed qubits were the same both nights: 82, 94, 113, 119, 130):

| | night 1 (11-13) | night 2 (11-14) | correlation per qubit, night 1 vs night 2 |
|---|---|---|---|
| 1 - z(\|0>), median | 0.0180 | 0.0150 | 0.27 |
| 1 + z(\|1>), median | 0.0390 | 0.0455 | 0.33 |

The per-qubit ranking changed much between the two nights. The quirk-ledger check is declared only after a third
night, as the declaration says; nothing here is used for placement.

## Reproduce

`python reproduce.py full-floor-2026-11-14-floor`.
