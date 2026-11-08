"""D: fractional RZZ (Heron r2) for the Heisenberg bond, an estimate without a device.

U(k dt) = exp(-i k dt (XX + YY + ZZ)) = RXX(2 k dt) RYY(2 k dt) RZZ(2 k dt) (the three terms commute);
RXX, RYY are RZZ conjugated by single-qubit Cliffords. So every bond block is 3 fractional RZZ pulses, at angle
2 k dt for a block in place, and for a block riding on a swap: SWAP . U(k dt) = exp(-i (k dt - pi/4)(XX + YY + ZZ))
up to a phase, angle 2 (k dt - pi/4), close to -pi/2 for small dt (as hard as a CZ). The moves onto and off a bridge
stay CX (CZ). Error per pulse is not in the calibration record: three stated assumptions, nothing fitted:
  F1  a fractional pulse has the error of a CZ (whatever its angle);
  F2  error proportional to |angle| / (pi/2) times the CZ error;
  F3  half the CZ error, whatever the angle.
Duration: the same as a CZ (FakeFez's cz duration) in all three; the single-qubit layers are counted as in the CZ form.
Output: per arm the two-qubit error budget sum(e) and exp(-sum) (a crude retention proxy that ignores idle decay)."""
import json, sys
import numpy as np
from psf_os import device as Dv
import heis3d as H
import line_merge as LM

dev = Dv.Device.load(sys.argv[1])
props = json.load(open(sys.argv[2]))
cz_err = []
for g in props["gates"]:
    if g["gate"] == "cz":
        e = next((p["value"] for p in g["parameters"] if p["name"] == "gate_error"), None)
        if e is not None and e < 0.5:
            cz_err.append(e)
ecz = float(np.median(cz_err))
print(f"fez calibration 2026-11-06 23:22 CET: median CZ error {ecz:.2e} over {len(cz_err)} couplers")
dt = 0.05
for t in (1, 2, 3, 4):
    qc, placed, used, log, where, ops = LM.physical_line_merged(dev, t, dt)
    inplace, riding, moves, ang_in, ang_ride = 0, 0, 0, [], []
    for op in ops:
        if op[0] in ("y", "yy"):
            k = 1 if op[0] == "y" else op[2]
            inplace += 1; ang_in.append(2 * k * dt); moves += 4
        else:
            _, e, k, s = op
            for _ in (0, 1):     # both lines
                if k == 0:
                    moves += 3      # an empty swap (none in the line layout)
                elif s:
                    riding += 1; ang_ride.append(abs(2 * (k * dt - np.pi / 4)))
                else:
                    inplace += 1; ang_in.append(2 * k * dt)
    cz_form = 3 * (inplace + riding) + moves
    b_cz = cz_form * ecz
    f = lambda a, mode: ecz if mode == 1 else (ecz * a / (np.pi / 2) if mode == 2 else ecz / 2)
    out = {}
    for mode in (1, 2, 3):
        e = moves * ecz + 3 * sum(f(a, mode) for a in ang_in) + 3 * sum(f(a, mode) for a in ang_ride)
        out[mode] = e
    print(f"t {t}: blocks in place {inplace} (angles {min(ang_in):.2f}-{max(ang_in):.2f}), riding {riding} (angle {np.mean(ang_ride):.2f}),"
          f" CX moves {moves} | CZ form: {cz_form} CZ, budget {b_cz:.3f} exp(-) {np.exp(-b_cz):.3f} |"
          f" fractional F1 {out[1]:.3f} ({np.exp(-out[1]):.3f})  F2 {out[2]:.3f} ({np.exp(-out[2]):.3f})"
          f"  F3 {out[3]:.3f} ({np.exp(-out[3]):.3f})")
