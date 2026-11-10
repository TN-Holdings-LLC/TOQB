"""Pre-run check of a dual-unitary build (gpu/du51_build.py): every h = 0 user circuit (Clifford: J = b = pi/4, h = 0)
as compiled for the device, simulated at full size by Aer's stabilizer method (rz angles snapped to multiples of
pi/2 and written as Clifford gates; any other angle is a FAIL), shots 400. For each measured bit, the mean <Z> (the
circuit reads X through its final basis change) against the sealed answers on that label: the light-cone site must
read the exact +-1 in every shot; every other bit must be within 4 / sqrt(shots) of its exact value (0 off the cone).
Written for the N = 91 rerun (2026-11-10); the 11-09 check was the same test done by hand.

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/du91r_check.py OUT_DIR ANSWERS.json   (writes OUT_DIR/check.json)
"""
import json
import math
import os
import sys

import numpy as np

SHOTS = 400


def clifford(c):
    from qiskit import QuantumCircuit
    out = QuantumCircuit(c.num_qubits, c.num_clbits)
    for ins in c.data:
        name = ins.operation.name
        qs = [out.qubits[c.find_bit(q).index] for q in ins.qubits]
        cs = [out.clbits[c.find_bit(b).index] for b in ins.clbits]
        if name == "rz":
            k = float(ins.operation.params[0]) / (math.pi / 2)
            if abs(k - round(k)) > 1e-9:
                raise ValueError(f"rz({ins.operation.params[0]}) is not Clifford")
            for _ in range(int(round(k)) % 4):
                out.s(qs[0])
        elif name in ("barrier", "delay"):
            continue
        else:
            out.append(ins.operation, qs, cs)
    return out


def main(out, answers_file):
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    answers = json.load(open(answers_file))
    sim = AerSimulator(method="stabilizer")
    res, ok_all = {}, True
    for job in sorted(d for d in os.listdir(out) if os.path.isdir(os.path.join(out, d, "runs"))):
        runs = os.path.join(out, job, "runs")
        for f in sorted(os.listdir(runs)):
            if not (f.startswith("p2d_") and f.endswith(".json")) or "_floor" in f or "_mirror" in f:
                continue
            rec = json.load(open(os.path.join(runs, f)))
            tag = rec["tag"]
            if "_h00_" not in tag:
                continue
            c = qpy.load(open(os.path.join(runs, rec["export"]["qpy"]), "rb"))[0]
            counts = sim.run(clifford(c), shots=SHOTS, seed_simulator=7).result().get_counts()
            labels = rec["labels"]
            z = np.zeros(len(labels))
            for key, v in counts.items():
                bits = key.replace(" ", "")[::-1]
                for k in range(len(labels)):
                    z[k] += v * (1 - 2 * int(bits[k]))
            z /= SHOTS
            ex = np.array([answers[tag][str(q)] for q in labels])
            cone = [k for k in range(len(labels)) if abs(abs(ex[k]) - 1) < 1e-12]
            off = [k for k in range(len(labels)) if k not in cone]
            cone_ok = all(abs(z[k] - ex[k]) < 1e-12 for k in cone)
            off_dev = float(max(abs(z[k] - ex[k]) for k in off)) if off else 0.0
            ok = cone_ok and off_dev <= 4 / math.sqrt(SHOTS) and len(cone) == 1
            ok_all &= ok
            res[f"{job}/{tag}"] = dict(cone_labels=[labels[k] for k in cone], cone_z=[float(z[k]) for k in cone],
                                       cone_exact=[float(ex[k]) for k in cone], off_max_dev=off_dev, ok=bool(ok))
            print(f"{job}/{tag}: cone label {[labels[k] for k in cone]} z {[round(float(z[k]), 3) for k in cone]} exact "
                  f"{[float(ex[k]) for k in cone]}; off-cone max |z - exact| {off_dev:.3f}: {'PASS' if ok else 'FAIL'}")
    json.dump(dict(points=res, ok=bool(ok_all), shots=SHOTS), open(os.path.join(out, "check.json"), "w"), indent=1)
    print("ALL PASS" if ok_all else "FAIL")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
