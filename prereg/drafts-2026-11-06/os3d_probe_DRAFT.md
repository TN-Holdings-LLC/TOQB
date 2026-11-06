# DRAFT (not declared): the 3D device test with the floor probe (home, 2026-11-06 11:30 CET; owner's "進めて" after
the night's HURTS)

## Why

On 2026-11-06 (marrakesh) v3 fold lost to SABRE at every t (R 2.07 / 3.17 / 2.97, HURTS). After the verdict (post
hoc), 66-87 % of A's MSE sat on the two ends of bridge q38 (q49 floor 0.55; coupler 48-49). The fold sends every
y-bond of a block through one bridge, so one bad element there decides. The fix tested here: before the main job,
read our own floor of every qubit each candidate translation touches, and pass over a candidate that has a low one.
No calibration number is read; the rule is a threshold and the fixed order (first that clears), not a score.

## Steps (one device, the night's daily-record device)

1. Fetch (daily record).
2. Probe job: `gpu/os3d_probe.py build DEVICE_RECORD PROBE` -> the floor at t = 3 of the first 4 qualifying fold
   translations in the fixed order, every touched qubit read (sites and bridges), 2000 shots (4 circuits; 5.3 s on
   the marrakesh record of 11-06). Submit, collect, then `gpu/os3d_probe.py choose PROBE` -> CHOICE.json.
3. **Rule:** the chosen translation is the first candidate whose touched qubits all read floor >= 0.8. If none
   does, the night's 3D test is recorded as "probe passed none" and run as on 11-06 (A = first translation vs B).
4. Main job: `gpu/os3d_compare_build.py DEVICE_RECORD OUT ANSWERS_OUT --choice PROBE/CHOICE.json`:
   A = fold at the chosen translation; A0 = fold at the first translation (as 11-06), added only when the probe
   passed some over; B = SABRE seed 0; t = 1, 2, 3; floor and mirror each; ring sentinel. 31 circuits (37.6 s) with
   A0, 22 (27.6 s) without.
5. Calibration beside at submit and at run (as 11-06; report only).
6. Score: `gpu/os3d_probe_score.py OUT ANSWERS_OUT`.

## Answers (sealed)

The same exact values as 11-06 under the tags present. SHA-256 of the file the builder writes: without A0
6b2d068c7dfb4bf62b4d7bc2df2a42b5a013e2520c8b2acc009d7c982e05a816; with A0
b51d02973823eb43f7b8e5a4ceb039bb857daf5683a2712b5f5e292dc175be87.

## Judged

- As 11-06 for each arm (READS, AGREES, BEATS) and R = MSE_A / MSE_B per t (HELPS <= 0.8, HURTS >= 1.25).
- When A0 is in the job: R_probe = MSE_A / MSE_A0 per t with the same thresholds (does the probe's choice help?).
- Beside: the probe's floors per candidate, the chosen index, retention, normalised error, CZ and layers, floor and
  mirror, sentinel, calibration beside.

## To fix before declaring (owner)

- Threshold 0.8 and k = 4 (tonight: sites of A 0.95 typical, q49 0.55; SABRE's sites 0.97-0.98).
- Whether the probe's floor depth is t = 3 (the deepest) as here.
- The probe needs its own job before the main one (two submits a night for this test).

## Expectation (not evidence)

On the 11-06 record the probe's candidate 0 is the translation that touched q29, q38, q49; candidates 1-3 avoid all
three. If q49 reads as it did tonight (0.55), the probe passes candidate 0 over. Whether the next translation then
beats SABRE is open: the post-hoc removal of q29 and q49 gave R 1.04 / 0.53 / 0.64, which is not a prediction.
