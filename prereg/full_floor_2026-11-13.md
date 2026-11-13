# Declared: a whole-device readout record each night, for the fair check of the quirk ledger (Heron, raw)

Home Claude, 2026-11-13 (owner 12:37 JST: "やり方は任せます", on adding a whole-device floor). Declared with this commit,
pushed before the device record of the night is fetched. Not a test with a verdict: a measurement record.

## Why

The quirk ledger (`notes/quirk_ledger_2026-11-13`, psf-os `quirk.rank`, workplace VS) could not show whether a chain
re-ranked by yesterday's ledger has a better floor today, because each day's floor exists only on the qubits that
day's jobs used (`notes/quirk_rank_2026-11-13/effect.md`: 4 better, 5 worse of 9 changed choices, on unequal qubit
sets). A floor on every working qubit, every night, gives the comparison on equal ground.

## Circuits

`gpu/full_floor.py build DEV OUT ANS`: two circuits on every working qubit (failed qubits left out), no two-qubit
gate: measured as prepared (|0...0>) and after one X on each (|1...1>); 4000 shots; about 5 s by the model (fez
11-12 record: 153 qubits, 5.2 s). A companion job on the device the night's main jobs use
(`gpu/night.py prepare prereg/full_floor_2026-11-13_night.json FETCH WORK --device <that device>`), from tonight on,
each night until the owner stops it.

## Recorded (`gpu/full_floor.py score`), beside everything, never used to correct

Per physical qubit: 1 - z(|0>) and 1 + z(|1>). After at least three nights: does yesterday's ledger, ranking the
candidate chains of a job (as `quirk.rank`), pick chains whose whole-device floor today is lower than the default
chain's? That check is written as its own declaration before it is scored; until then the ledger is not used for
placement.
