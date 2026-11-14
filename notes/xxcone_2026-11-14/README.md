
## Desk check after the repeat (no device): plain local noise does not make the gap

`stim_noise.py` (output `stim_noise.txt`) runs the recorded theta = pi/2 circuits (Clifford) of the repeat in stim
with one uniform local noise model (CZ depolarising 0.003, single-qubit 0.0003, readout 0.015; nothing taken from
the device): the gap r(33) - r(81) stays within +-0.004 in every block at every depth, against up to +0.12 on the
device. In this circuit a measured Z follows its particle's path; a uniform noise puts the same number of errors on a
path whether the chain is 33 or 81 long. So the light-cone reading as first written ("more errors inside a growing
light cone") does not hold under uniform noise; the device gap needs elements that differ.

`stim_ext.py` (output `stim_ext.txt`) is an illustration, not a fit: the same model with the CZ error tripled on
couplers touching the extension (positions 33-80 of the N = 81 chain). A gap appears, grows with depth and moves
inward (far block +0.024 only at 64 layers), as on the device, but its order differs (mid above near from 16 layers;
on the device near first). Which elements of the extension are worse, and how, is not measured here (the device's
calibration is not read). The whole-device floor (our own readout record) shows a heavier tail on the extension
qubits (mean 1 - z(|0>) 0.039 against 0.020 on 11-14), but readout acts at the end of a path and does not explain the
gap by itself.
