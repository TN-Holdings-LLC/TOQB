# Classifier series, job 3 of 6: ibm_fez, 2026-11-11 (prereg/qclf_2026-11-10.md)

- Record 11:13:35 CET (`../fetch_in`; queue marrakesh 1, fez 6, kingston 101; chosen marrakesh, fez).
- ibm_marrakesh first by the order: the build stopped, "the sentinel did not land on the user's ring" (14 failed
  qubits, as on 11-10) -> not buildable, next device. Not counted.
- ibm_fez: 994 circuits, 105.9 s by the model, rule G PASS. Gate hash 7d98a8c2... and the job file's sha256
  (e265620f..., before gzip) equal the 11-10 fez job (`results/night-2026-11-10/qclf/ibm_fez`, noiseless check of all
  984 circuits PASS, worst 1.1e-13) -> that PASS carries over (rule fixed before the record,
  `notes/tonight_2026-11-11/PLAN.md`). The same circuits ran on fez on 11-10 (job 2); today is a new device-day.
- Job dbq49goou4as73cuibvg, submitted 11:34 CET, DONE; job files returned byte-identical. Sentinel DEAD.
- Scored with the sealed answers (74d7332a..., not released until the last job of the series).
- Files over 50 MB committed as .gz (`LARGE_FILES.md`).

## Declared verdicts

- A: 133 of 200 correct at S 250 against p0 0.525: one-sided binomial p 4.2e-5: **READS**.
- M: signed margin +0.500 (SE 0.070).

## Beside

- Accuracy S 16 / 32 / 64 / 125 / 250: 0.635, 0.565, 0.685, 0.700, 0.665; ceiling 0.875; reach 0.440.
- Median lambda X / Y / Z 0.704 / 0.678 / 0.861; share answered +1 0.520; floor 0.985; mirror 0.653.
- The same circuits on fez on 11-10: A 134 of 200, M +0.458 (SE 0.068); lambda 0.697 / 0.651 / 0.854; floor 0.984;
  mirror 0.646.
