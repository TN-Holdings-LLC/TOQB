# Is the device's error structured or random? (workplace, 2026-11-13; desk only, nothing corrected)

Owner: "ノイズに規則性があるかランダム化を計測できる？". `noise_structure.py` reads the released hub_score records
(hubbard 11-11, hubbard-big 11-11, hub-dt 11-12, xx91 11-12; 36 circuits, all ibm_fez) and splits each circuit's
per-qubit values as z = r e + rest (rest orthogonal to the exact values e; notes/paper9/r_thread_2026-11-13).

## Results (`noise_structure.json`)

1. **Not shot noise.** The rest's variance is 6.7 to 240 times the shot variance of the same circuit (4000 shots).
   A purely random error from the finite number of shots would give about 1: the "wrong shape" part is a systematic
   error of the device, not sampling.
2. **Tied to the place, and it stays.** The same circuit on the same physical qubits of ibm_fez on two days (hubbard
   11-11 L20_s4_U4 and hub-dt 11-12 L20_T1.0_s4; equal exact values, equal placement): the two rests correlate 0.63.
   Home's check of the Ohm circuits on two devices (fez, kingston) found 0.04-0.16 (`results/ohm-kingston-2026-11-12`):
   the pattern follows the qubits used, not the circuit.
3. **Neighbours sometimes err together.** Correlation of the rest between neighbouring qubits on the chain: -0.36 to
   +0.57; at 2 steps often about +0.5 (blocks of adjacent qubits off in the same direction).

So, within these records (one device, one pair of days), the error beyond the uniform shrink is mostly a place-bound
habit that persists from day to day, not random fluctuation.

## How to measure it properly (proposal, not declared)

One job per day, each part read raw and never used to correct:
- the same circuit on the same place, repeated in the job (within a day);
- the same circuit translated to other places (circuit-bound against place-bound);
- the same jobs on other days and devices (drift);
- twirling on and off for one circuit (whether randomised compiling turns the habit into random error; the project
  runs with twirling off, so this would be a declared exception for measurement only).
Then the rest splits into circuit, place, day and random parts.
