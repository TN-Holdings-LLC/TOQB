"""Pre-run check of the Clifford twins in a job built with --twin (home, 2026-11-13): each twin run is re-read, its
non-RZ schedule compared with its user run (must be identical), every RZ angle checked to be a multiple of pi/2, and
its per-qubit <Z> recomputed by Aer's stabilizer method (independent of psf_os.twin.z_exact) against the twin
answers (must agree to 1e-9). Prints differences only.
usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/twin_check.py OUT TWIN_ANSWERS.json   (writes OUT/twin_check.json)"""
import ast
import json
import os
import sys

import numpy as np


def main(out, ans_path):
    from qiskit import QuantumCircuit, qpy
    from qiskit.quantum_info import Pauli
    from qiskit_aer import AerSimulator
    from psf_os import twin as TW
    runs = os.path.join(out, "runs")
    ans = json.load(open(ans_path))
    res, ok = {}, True
    for tag in sorted(ans):
        cu = qpy.load(open(os.path.join(runs, f"p2d_{tag}.qpy"), "rb"))[0]
        ct = qpy.load(open(os.path.join(runs, f"p2d_{tag}_twin.qpy"), "rb"))[0]
        rec = json.load(open(os.path.join(runs, f"p2d_{tag}_twin.json")))
        m = rec["mapping"] if isinstance(rec["mapping"], dict) else ast.literal_eval(rec["mapping"])
        phys = [int(m[str(q)]) for q in rec["labels"]]
        same = TW.check_same_schedule(cu, ct)
        quarter = all(abs(float(i.operation.params[0]) / (np.pi / 2) - round(float(i.operation.params[0]) / (np.pi / 2)))
                      < 1e-12 for i in ct.data if i.operation.name == "rz")
        touched = sorted({ct.find_bit(q).index for i in ct.data if i.operation.name not in ("barrier", "measure")
                          for q in i.qubits} | set(phys))
        pos = {p: k for k, p in enumerate(touched)}
        r = QuantumCircuit(len(touched))
        for i in ct.data:
            if i.operation.name in ("barrier", "measure", "delay"):
                continue
            r.append(i.operation, [pos[ct.find_bit(q).index] for q in i.qubits])
        n = len(touched)
        for k, p in enumerate(phys):
            lab = ["I"] * n
            lab[n - 1 - pos[p]] = "Z"
            r.save_expectation_value(Pauli("".join(lab)), list(range(n)), label=f"z{k}")
        d = AerSimulator(method="stabilizer").run(r, shots=1).result().data()
        z = np.array([float(np.real(d[f"z{k}"])) for k in range(len(phys))])
        e = np.array([ans[tag][str(q)] for q in rec["labels"]])
        worst = float(np.abs(z - e).max())
        good = same and quarter and worst < 1e-9
        ok &= good
        res[tag] = dict(same_schedule=same, rz_quarter_turns=quarter, worst=worst, cz=rec.get("cz"), ok=good)
        print(f"{tag}_twin: CZ {rec.get('cz')}, same schedule {same}, RZ multiples of pi/2 {quarter}, "
              f"Aer stabilizer against the answers worst {worst:.1e} {'PASS' if good else 'FAIL'}", flush=True)
    res["ALL"] = "PASS" if ok else "FAIL"
    json.dump(res, open(os.path.join(out, "twin_check.json"), "w"), indent=1)
    print("ALL", res["ALL"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
