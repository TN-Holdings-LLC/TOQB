"""Pre-run check of a utility job (gpu/utility_build.py) against its answers (home, 2026-11-10):
  1. theta_h = 0 and pi/2 (k = 0, 16; Clifford): every observable's compiled circuit, whole device, on Aer's stabilizer
     method (rz angles snapped, else FAIL), 400 shots: the parity of the measured bits must give the exact value
     (+-1 or 0 within 4 / sqrt(400)).
  2. every k for Z_106: the same embedded circuit built with only the gates inside the observable's light cone
     (utility_tn's schedule: every gate outside it cancels), compiled the same way, as a statevector on the cone:
     equals the answer to 1e-9. (A gate-order cone of the job's circuit spreads over the device because the order
     does not know that the ZZ commute; the Clifford points of 1 check the job's own circuits.)
usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/utility_check.py OUT ANSWERS.json   (writes OUT/check.json)
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from du91r_check import clifford  # noqa: E402


CONE_MAX = 25  # statevector of the pruned cone up to this many qubits (11-10: 20; 11-11: 25, so Z_106 at 5 steps is
#                checked at all 17 k; 25 qubits = 0.5 GB)


def parity_mean(counts, nbits):
    tot = sum(counts.values())
    return sum(v * (1 - 2 * (key.replace(" ", "").count("1") % 2)) for key, v in counts.items()) / tot


def cone_value(c):
    """<prod Z> on the measured bits (after the basis change in c), by a statevector on the backward cone."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp, Statevector
    meas = [c.find_bit(i.qubits[0]).index for i in c.data if i.operation.name == "measure"]
    body = [i for i in c.data if i.operation.name not in ("measure", "barrier", "delay")]
    cone, keep = set(meas), []
    for ins in reversed(body):
        qs = [c.find_bit(q).index for q in ins.qubits]
        if cone & set(qs):
            cone |= set(qs)
            keep.append((ins.operation, qs))
    act = sorted(cone)
    if len(act) > 20:
        return None, len(act)
    pos = {q: j for j, q in enumerate(act)}
    sub = QuantumCircuit(len(act))
    for op, qs in reversed(keep):
        sub.append(op, [pos[q] for q in qs])
    lab = ["I"] * len(act)
    for q in meas:
        lab[len(act) - 1 - pos[q]] = "Z"
    return float(np.real(Statevector(sub).expectation_value(SparsePauliOp("".join(lab))))), len(act)


def pruned_value(name, r, k, out):
    """The embedded circuit with the light-cone schedule only (per step: RX on qubits within t - s + 1 edges, the ZZ
    of edges touching qubits within t - s edges), compiled by utility_build.native, on a statevector of its qubits."""
    import utility_build as UB
    import utility_exact as UE
    import utility_tn as UT
    import rustworkx as rx
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp, Statevector
    obs, t, ex = UT.OBS[name]
    ee = UE.eagle_edges()
    g = rx.PyGraph()
    g.add_nodes_from(range(127))
    g.add_edges_from_no_data(ee)
    D = rx.distance_matrix(g)
    dist = {q: min(D[q][s] for s in obs) for q in range(127)}
    qs = sorted(q for q in range(127) if dist[q] <= t)
    if len(qs) > CONE_MAX:
        return None, len(qs)
    pos = {q: j for j, q in enumerate(qs)}
    th = k * math.pi / 32
    qc = QuantumCircuit(len(qs))
    for s in range(1, t + 1):
        rr = t - s
        for q in qs:
            if dist[q] <= rr + 1:
                qc.rx(th, pos[q])
        for a, b in ee:
            if min(dist[a], dist[b]) <= rr and a in pos and b in pos:
                qc.rz(-math.pi / 2, pos[a])
                qc.rz(-math.pi / 2, pos[b])
                qc.cz(pos[a], pos[b])
    if ex:
        for q in qs:
            if dist[q] <= 0:
                qc.rx(th, pos[q])
    lab = ["I"] * len(qs)
    for q, l in obs.items():
        lab[len(qs) - 1 - pos[q]] = l
    qc = UB.native(qc)
    if len(qs) <= 20:
        return float(np.real(Statevector(qc).expectation_value(SparsePauliOp("".join(lab))))), len(qs)
    # over 20 qubits qiskit.quantum_info is too slow (11-11: the check hit its 50 min limit); Aer statevector instead
    from qiskit_aer import AerSimulator
    qc.save_expectation_value(SparsePauliOp("".join(lab)), list(range(len(qs))), label="p")
    res = AerSimulator(method="statevector", precision="double").run(qc).result()
    return float(np.real(res.data()["p"])), len(qs)


def quimb_value(c, measured):
    """<prod Z> on the measured qubits of the job's own compiled circuit (whole device, final measurements removed) by
    quimb's light-cone contraction (generic gates, independent of utility_tn / reach_tn). 11-11, for cones over
    CONE_MAX, where the statevector check does not run."""
    import quimb.tensor as qtn
    c = c.copy()
    c.remove_final_measurements(inplace=True)
    circ = qtn.Circuit(c.num_qubits)
    for ins in c.data:
        if ins.operation.name in ("barrier", "delay"):
            continue
        circ.apply_gate_raw(ins.operation.to_matrix(), tuple(reversed([c.find_bit(q).index for q in ins.qubits])))
    Z = np.diag([1.0, -1.0])
    G = Z
    for _ in measured[1:]:
        G = np.kron(G, Z)
    where = measured[0] if len(measured) == 1 else tuple(measured)
    return complex(circ.local_expectation(G, where, optimize="auto-hq", simplify_sequence="ADCRS")).real


QUIMB_KS = (5, 11)


def main(out, ans_file):
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    answers = json.load(open(ans_file))
    rep = json.load(open(os.path.join(out, "report.json")))
    sim = AerSimulator(method="stabilizer")
    res, ok = {}, True
    for name, r in rep["observables"].items():
        if r["embedding"] is None:
            continue
        cs = qpy.load(open(os.path.join(out, "runs", f"u_{name}.qpy"), "rb"))
        for k in (0, 16):
            cnt = sim.run(clifford(cs[k]), shots=400, seed_simulator=5).result().get_counts()
            z, e = parity_mean(cnt, 0), answers[f"{name}_k{k:02d}"]
            good = abs(z - e) <= (1e-12 if abs(abs(e) - 1) < 1e-9 else 4 / math.sqrt(400))
            ok &= good
            res[f"{name}_k{k:02d}_clifford"] = dict(z=z, exact=e, ok=bool(good))
            print(f"{name} k {k:2d} stabilizer: {z:+.3f} exact {e:+.3f} {'PASS' if good else 'FAIL'}")
            # 11-11: the exact stabilizer expectation (0 or +-1 exactly) of the same compiled circuit, no sampling, so an
            # exact value of 0 is checked strictly too (the sampled check above allows 4 / sqrt(400))
            from qiskit.quantum_info import Pauli
            c2 = clifford(cs[k])
            c2.remove_final_measurements(inplace=True)
            lab = ["I"] * c2.num_qubits
            for q in r["measured"].values():
                lab[c2.num_qubits - 1 - int(q)] = "Z"
            c2.save_expectation_value(Pauli("".join(lab)), list(range(c2.num_qubits)), label="p")
            x = float(np.real(sim.run(c2, shots=1).result().data()["p"]))
            good2 = abs(x - e) <= 1e-9
            ok &= good2
            res[f"{name}_k{k:02d}_clifford_exact"] = dict(value=x, exact=e, ok=bool(good2))
            print(f"{name} k {k:2d} stabilizer exact: {x:+.3f} exact {e:+.3f} {'PASS' if good2 else 'FAIL'}")
        v0, w = pruned_value(name, r, 1, out)
        if v0 is not None:
            worst = 0.0
            for k in range(17):
                v, _ = pruned_value(name, r, k, out)
                worst = max(worst, abs(v - answers[f"{name}_k{k:02d}"]))
            good = worst < 1e-9
            ok &= good
            res[f"{name}_cone"] = dict(cone=w, worst=worst, ok=bool(good))
            print(f"{name} all 17 k by the {w}-qubit cone: worst {worst:.1e} {'PASS' if good else 'FAIL'}")
        else:
            meas = [int(q) for q in r["measured"].values()]
            worst = 0.0
            for k in QUIMB_KS:
                worst = max(worst, abs(quimb_value(cs[k], meas) - answers[f"{name}_k{k:02d}"]))
            good = worst < 1e-9
            ok &= good
            res[f"{name}_quimb"] = dict(cone=w, ks=list(QUIMB_KS), worst=worst, ok=bool(good))
            print(f"{name}: cone {w} qubits; k {QUIMB_KS} by quimb on the compiled job circuit: worst {worst:.1e} "
                  f"{'PASS' if good else 'FAIL'}")
    json.dump(dict(points=res, ok=bool(ok)), open(os.path.join(out, "check.json"), "w"), indent=1)
    print("ALL PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
