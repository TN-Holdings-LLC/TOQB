"""Task X2 (DRAFT): the user circuits against the closed form (noiseless), and their cost through run2d.
  - statevector, chain relabelled 0..N-1: N = 11 (t <= 5) and N = 21 (t 4, 8, 10), h in H_VALUES;
  - Aer MPS on N = 51, 71, 91 at t 4 and 8 (every site);
  - run2d (user2d.build_batch, unchanged) on the 11-05 fez record: compiled CZ, CZ layers, circuits, time model.
usage: PYTHONPATH=<psf-os>:. python notes/du91_2026-11-06/checks.py OUT.json"""
import json
import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from daily import du91 as X  # noqa: E402


def values(qc, method):
    from qiskit.quantum_info import Pauli
    from qiskit_aer import AerSimulator
    c = qc.remove_final_measurements(inplace=False)
    n = c.num_qubits
    for k in range(n):
        c.save_expectation_value(Pauli("Z"), [k], label=f"z{k}")  # p4 ends with H on every site: Z here is X before
    r = AerSimulator(method=method).run(c).result().data()
    return [float(r[f"z{k}"]) for k in range(n)]


def main(out):
    import practice_circuits as PC
    res = dict(statevector={}, mps={}, run2d={})
    for n, ts in ((11, (1, 2, 3, 4, 5)), (21, (4, 8, 10))):
        for h in X.H_VALUES:
            for t in ts:
                v = values(PC.p4(t, X.PI4, chain=list(range(n)), h=h), "statevector")
                d = max(abs(a - b) for a, b in zip(v, X.exact(n, t, h)))
                res["statevector"][f"N{n}_h{h}_t{t}"] = d
    print("statevector max", max(res["statevector"].values()), flush=True)
    for n in X.WIDTHS:
        for t in (4, 8):
            for h in (0.0, 0.15):
                v = values(PC.p4(t, X.PI4, chain=list(range(n)), h=h), "matrix_product_state")
                d = max(abs(a - b) for a, b in zip(v, X.exact(n, t, h)))
                res["mps"][f"N{n}_h{h}_t{t}"] = d
                print(f"MPS N {n} t {t} h {h}: max |sim - exact| {d:.2e}", flush=True)
    from psf_os import device as D
    from psf_os import job as J
    from psf_os import report2d as R2
    from psf_os import user2d as U
    from qiskit import qpy
    dev = D.Device.load("results/daily/2026-11-05/ibm_fez/dev")
    for n in X.WIDTHS:
        p = X.place(dev, n)
        if p["shape"] is None:
            res["run2d"][str(n)] = "no shape qualifies on the 11-05 fez record"
            continue
        sh = next(s for s in X.SHAPES if s[0] == p["shape"])
        items = [(f"N{n}_t{t:02d}", X.circuit(n, 0.15, t, sh)) for t in X.T_STEPS]
        with tempfile.TemporaryDirectory() as tmp:
            rep = U.build_batch(dev, items, tmp, shots=4000, max_seconds=10 ** 6)
            rows = {}
            for tag, r in rep["items"].items():
                with open(os.path.join(tmp, "runs", f"p2d_{tag}.qpy"), "rb") as f:
                    rows[tag] = dict(cz=r["cz"], cz_layers=R2.cz_layers(qpy.load(f)[0]), copy=r["copy"])
            res["run2d"][str(n)] = dict(shape=p["shape"], copy=[p["drow"], p["dcol"]], rows=rows,
                                        circuits_one_h=rep["circuits"], seconds_one_h=rep["qpu_seconds_model"],
                                        seconds_four_h=round(J.qpu_seconds(3 * 4 * len(X.T_STEPS) + 4, 4000), 1))
        print(n, json.dumps(res["run2d"][str(n)])[:400], flush=True)
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    sys.path.insert(0, "gpu")
    main(sys.argv[1])
