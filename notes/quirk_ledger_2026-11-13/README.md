# Quirk ledger: does our own record know each qubit's habits? (workplace VS Claude, 2026-11-13; desk only, not declared)

OS item 4 (owner 10:53 JST): learn the machine's habits from our own job records, without reading IBM's calibration
numbers. Nothing here corrects a result, judges a test, or changes a placement.

`ledger.py --psf-os PATH` reads every finished user2d job under results/. The per-label floor and mirror values are
read exactly as `psf_os.user2d.card` reads them (equal to card() to 0 on a checked circuit) and put on the physical
qubit through the record's mapping. It writes `ledger.json` (the ledger and every comparison) and `ledger.md` (the
tables).

## 1. The ledger

**What was read:** 36 jobs, 16 device-days, 11-04 to 11-12:

- ibm_fez: 7 days.
- ibm_marrakesh: 6 days.
- ibm_kingston: 3 days.

**Per physical qubit, device and day**, as means over the circuits that used it:

- **floor:** 1 - z of the floor circuit (readout loss).
- **mirror:** the mirror circuit's z, standardised within the circuit. The circuit's depth sets the mean, so only how
  the qubit ranks among the circuit's qubits is kept.
- **rest:** where scores.json has per-qubit z and exact values (hubbard, hubbard-big, hub-dt, xx91). It is the
  qubit's share of the circuit's wrong-shape error, rest^2 / mean(rest^2). rest comes from z = r e + rest, split as
  in `notes/noise_structure_2026-11-13`.

**Day label:** the record folder's date. This is the project's day, in Japan time. For example, the 11-07 daily ran
at 23:56 CET on 11-06.

**Records not read:** 46, each with its reason at the end of ledger.md.

- **Other record formats:** s2rc, ising2d, du_kising, kim_lattice, and the utility jobs' user/floor/mirror form. No
  reader was written for them in the 2 hours.
- **Five old device runs (10-26 to 10-30) fail to load in psf_os.job.read.** Three are missing a key ('points' or
  'setting'). Two report that a run file "differs from the manifest", probably the Windows line-ending change of a
  checkout (unverified).

## 2. Does it persist across days? (Spearman over the shared qubits; all day pairs)

| device | floor: median (range), pairs | mirror: median (range), pairs | rest |
|---|---|---|---|
| ibm_fez | +0.77 (+0.47 to +0.94), 21 | +0.34 (-0.10 to +0.59), 21 | +0.27 (11-11 to 11-12, 1 pair) |
| ibm_marrakesh | +0.55 (+0.34 to +0.65), 15 | +0.33 (+0.18 to +0.63), 15 | no record |
| ibm_kingston | +0.78 (+0.71 to +0.79), 3 | +0.08 (-0.31 to +0.27), 3 | no record |

- **floor:** the readout loss is a lasting habit of the qubit. On ibm_fez the rank correlation stays near 0.8 over a
  gap of 1 to 3 days, and is still 0.73 after 8 days (11-04 to 11-12, ledger.md).
- **mirror:** the circuit-through habit persists only weakly.
- **rest:** 0.27 here. This compares different circuits on the two days, by their share of the error. The workplace
  Claude's 0.63 was the same circuit on the same qubits (signed rest). So the place-bound part shows more clearly
  when the circuit is the same.

## 3. Can the earlier day predict the next recorded day? (earlier day only, never a later one)

| quantity | predictions | median Spearman | weakest fifth again weakest (chance 0.20) |
|---|---|---|---|
| floor | 13 | +0.77 | 0.60 on average (ibm_fez 0.67-0.90; marrakesh 0.33-0.54; kingston 0.25-0.67) |
| mirror | 13 | +0.38 | 0.33 |
| rest | 1 (fez 11-11 to 11-12) | +0.27 | 0.48 |

## 4. Against IBM's calibration numbers (reference only)

**Not possible from the records.**

- psf-os does not record IBM's error numbers. The committed `device.json` files carry only the failed and masked
  marks.
- So there is nothing to compare the ledger's floor with without fetching IBM's calibration, which would mean
  connecting to IBM.
- The check "do our own records tell the same as IBM's numbers" is left for a day when a record of the calibration
  exists. The ledger itself needs no IBM number.

## 5. In one sentence

**From our own records alone, the qubits with the worst readout can be named a day ahead.**

- On ibm_fez, 6 to 9 of every 10 qubits in the earlier day's weakest fifth are again in the weakest fifth (chance
  2).
- On marrakesh and kingston it is weaker (3 to 6 of 10).
- The circuit-through (mirror) and wrong-shape (rest) habits are only weakly predictable from these records.
- **Using this ledger to choose or avoid qubits would be a "special condition" under the project's placement policy**
  (placement reads no error numbers). The policy is about IBM's numbers, but a ledger of our own error measurements
  is still an error number. Whether to use it is the owner's decision. Nothing here uses it.

## Cautions

- **Not one repeated circuit.** Different days used different circuits and partly different qubits. Each comparison
  is over the qubits both days used: 22 to 113.
- **The floor is a single short circuit**, so it is the least confounded quantity. Mirror and rest depend on the
  circuits.
- **These records only.** One device on one day per ledger entry. Nothing here is a statement beyond these records.
