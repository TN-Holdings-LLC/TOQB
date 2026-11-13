# Ohm's law on raw Heron: where the line stops (home, 2026-11-13 09:50 JST; owner chose to close the device line here)

Owner 2026-11-13 09:4x JST: option (c), "ここで区切る". No further Ohm device runs are planned; this note records why.

## Records

- `results/ohm-2026-11-12` (fez) and `results/ohm-kingston-2026-11-12` (kingston): 40 qubits, fSim(pi/4, phi), 3 and 6
  cycles (CZ 18 / 36 layers for A1, A2). The transferred magnetization M did not read in 11 of 12 arm-cycle cells
  (kingston A0 at 6 cycles read, 0.375); every circuit's per-qubit Z read; the W exponent order A0 > A1 > A2 held on
  both devices.
- Why (`notes/ohm_postsel_2026-11-12`, counts in the records; no verdict changed): the device Z is the exact Z shrunk
  towards 0 (60-86% of the MSE is a uniform shrink); M sums 20 right-half qubits whose errors point the same way;
  57-83% of the M error comes from shots whose number of 1s changed (losses and gains about equal; even the floor
  circuit shows a 1 in 50% / 32% of shots at 40 qubits). The remaining place-to-place ripple differs between devices.
- Desk (`notes/ohm3d_desk_2026-11-12`, `notes/ohm_sim_2026-11-12`, `notes/ohm_honeycomb_2026-11-13`): 10 cycles do
  not help (noise grows, A1/A2 answers past MPS); 3D costs 60-165 CZ layers per step on heavy-hex and saturates at
  computable sizes; the native honeycomb strip enlarges the signal, and at 56 qubits its answers are computable to 4
  cycles (light-cone network), but with tonight's per-layer mixing the M line is reached only on a kingston-like day and
  not on a fez-like one (rough, using p 0.15 / 0.24 at 18 / 36 layers and W / W_mixed 0.20 / 0.28), and 2 to 4 cycles
  is too short a window for a transport exponent.

## Conclusion (within these records)

On raw Heron, at the sizes where the exact answer is computable, the transport quantity of the Ohm question (a small
difference carried by a sum over many qubits) does not read once the circuit has interaction (A1, A2), while each
qubit's Z does. The obstacle is the uniform shrink (readout and gates, growing with qubits measured and with CZ
layers), not the circuit and not the placement alone. Google's 2024 run read the same kind of quantity with the native
fSim gate (a third of the layers) and post-selection on the number of excitations; both are outside this project's
raw rule.

Open if the line is reopened: the honeycomb strip on a low-noise day (declared as such), or a special-condition
placement reported beside the raw result.
