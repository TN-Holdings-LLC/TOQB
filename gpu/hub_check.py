"""Pre-run check of a Hubbard job (gpu/hub_build.py), noiseless, on the job's own compiled circuits (home, 2026-11-11).
Each compiled user circuit is reduced to its 2L chain qubits in chain order (physical -> chain label by the copy's
mapping, chain label -> logical index by build.json) and simulated without noise: statevector when 2L <= 12, else
Aer's matrix-product-state method (no truncation) for steps <= --mps-steps. Its per-qubit <Z> must equal the answers
(by chain label) within 1e-6 (MPS) / 1e-9 (statevector); its mirror must read all zeros; the floor is diagonal on
|0...0> (checked by the builder). Also printed: CZ count and CZ depth of the two arms of every step (must be equal).
Prints differences only, never answer values.
usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/hub_check.py OUT ANSWERS.json [--mps-steps 2] [--only TAG ...]
       (writes OUT/check.json)
"""
import argparse
import ast
import json
import os

import numpy as np


def load(path):
    from qiskit import qpy
    return qpy.load(open(path, "rb"))[0]


def reduced(c, phys_order):
    """The circuit on len(phys_order) qubits, qubit k = phys_order[k]; final measurements dropped."""
    from qiskit import QuantumCircuit
    pos = {p: k for k, p in enumerate(phys_order)}
    out = QuantumCircuit(len(phys_order))
    for ins in c.data:
        if ins.operation.name in ("measure", "barrier", "delay"):
            continue
        qs = [c.find_bit(q).index for q in ins.qubits]
        if any(q not in pos for q in qs):
            raise SystemExit(f"FAIL: a gate on qubit {qs} outside the chain")
        out.append(ins.operation, [pos[q] for q in qs])
    return out


def z_of(qc):
    from qiskit.quantum_info import Pauli
    from qiskit_aer import AerSimulator
    c = qc.copy()
    n = c.num_qubits
    for k in range(n):
        lab = ["I"] * n
        lab[n - 1 - k] = "Z"
        c.save_expectation_value(Pauli("".join(lab)), list(range(n)), label=f"z{k}")
    method = "statevector" if n <= 12 else "matrix_product_state"
    d = AerSimulator(method=method).run(c, shots=1).result().data()
    return np.array([float(np.real(d[f"z{k}"])) for k in range(n)]), method


def z_quimb(qc, chi=1024):
    """Per-qubit <Z> by quimb's CircuitMPS on two-qubit blocks (as gpu/hub_answers.py, but on the compiled circuit).
    11-11 night: Aer's MPS took about 25 min for L 30 at 4 steps here; quimb is used above --mps-steps."""
    import sys as _s
    _s.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "notes", "hubbard_2026-11-11"))
    import hub_cost as HC
    z, bond, err = HC.run_quimb(HC.blocks(qc), chi)
    return np.asarray(z), f"quimb chi {chi} (bond {bond}, error estimate {err:.1e})"


def cz_depth(c):
    return c.depth(filter_function=lambda i: i.operation.name == "cz")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("answers")
    ap.add_argument("--mps-steps", type=int, default=2)
    ap.add_argument("--quimb-steps", type=int, default=0, help="steps above --mps-steps up to this by quimb")
    ap.add_argument("--only", nargs="*", default=None, help="tags to check (default: all)")
    a = ap.parse_args()
    b = json.load(open(os.path.join(a.out, "build.json")))
    ans = json.load(open(a.answers))
    runs = os.path.join(a.out, "runs")
    res, ok = {}, True
    for tag in sorted(b["cz"]):
        if a.only and tag not in a.only:
            continue
        parts = tag.split("_")
        L, s = int(parts[0][1:]), int(next(p for p in parts[1:] if p.startswith("s"))[1:])
        rec = json.load(open(os.path.join(runs, f"p2d_{tag}.json")))
        m = rec["mapping"] if isinstance(rec["mapping"], dict) else ast.literal_eval(rec["mapping"])
        chain = b["chains"][str(L)]["labels"]
        phys = [int(m[str(q)]) for q in chain]
        cu = load(os.path.join(runs, f"p2d_{tag}.qpy"))
        r = dict(cz=b["cz"][tag], cz_depth=cz_depth(cu))
        if 2 * L <= 12 or s <= a.mps_steps or s <= a.quimb_steps:
            use_q = not (2 * L <= 12 or s <= a.mps_steps)
            z, method = (z_quimb if use_q else z_of)(reduced(cu, phys))
            e = np.array([ans[tag][str(q)] for q in chain])
            tol = 1e-9 if method == "statevector" else 1e-6
            r.update(method=method, worst=float(np.abs(z - e).max()))
            good = r["worst"] < tol
            zm, _ = (z_quimb if use_q else z_of)(reduced(load(os.path.join(runs, f"p2d_{tag}_mirror.qpy")), phys))
            r["mirror_worst"] = float(np.abs(zm - 1.0).max())
            good &= r["mirror_worst"] < tol
            r["ok"] = bool(good)
            ok &= good
        res[tag] = r
        print(f"{tag}: CZ {r['cz']} depth {r['cz_depth']}" +
              (f"; {r['method']} against the answers worst {r['worst']:.1e}, mirror {r['mirror_worst']:.1e} "
               f"{'PASS' if r['ok'] else 'FAIL'}" if "ok" in r else "; not simulated (deeper than --mps-steps)"),
              flush=True)
    for tag in list(res):
        if tag.endswith("_U4") and tag[:-2] + "U0" in res:
            t0 = tag[:-2] + "U0"
            same = res[tag]["cz"] == res[t0]["cz"] and res[tag]["cz_depth"] == res[t0]["cz_depth"]
            ok &= same
            print(f"{tag[:-3]}: arms CZ {res[tag]['cz']} / {res[t0]['cz']}, depth {res[tag]['cz_depth']} / "
                  f"{res[t0]['cz_depth']} {'EQUAL' if same else 'DIFFER'}")
    res["ALL"] = "PASS" if ok else "FAIL"
    json.dump(res, open(os.path.join(a.out, "check.json"), "w"), indent=1)
    print("ALL", res["ALL"])


if __name__ == "__main__":
    main()
