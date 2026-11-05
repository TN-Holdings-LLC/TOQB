"""Noiseless check of the exploratory job's forward circuits (raw and twirled, readout twirl undone) against answers."""
import json, sys
import numpy as np
from qiskit import QuantumCircuit, qpy
from qiskit.quantum_info import Pauli, Statevector
from qiskit_aer import AerSimulator
sys.path.insert(0, "gpu")
import twirl_explore as T
from practice_circuits import CHAIN
out, answers = sys.argv[1], json.load(open(sys.argv[2]))

def load(pid, role):
    rec = json.load(open(f"{out}/runs/x_{pid}_{role}.json"))
    return rec, qpy.load(open(f"{out}/runs/x_{pid}_{role}.qpy", "rb"))

def sign_of(c, k, q_phys, rec):
    # the readout X of instance k on the clbit of q_phys flips the sign of <Z> measured before it is undone
    j = rec["labels"].index(next(int(l) for l, p in rec["mapping"].items() if p == q_phys))
    return -1 if T.flips(len(rec["labels"]), k)[j] else 1

for role in ("raw", "tw"):
    rec, cs = load("D02", role)
    adj = {}
    for a, b in rec["edges"]:
        adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
    phys = {int(k): v for k, v in rec["mapping"].items()}
    worst = 0
    for k, c in enumerate(cs):
        for q in rec["labels"][::5]:
            ball, fr = {q}, {q}
            for _ in range(3):
                fr = {y for x in fr for y in adj.get(x, ())} - ball; ball |= fr
            pb = {phys[x]: i for i, x in enumerate(sorted(ball))}
            small = QuantumCircuit(len(pb))
            for ins in c.data:
                if ins.operation.name in ("measure", "barrier"): continue
                ix = [c.find_bit(x).index for x in ins.qubits]
                if all(x in pb for x in ix): small.append(ins.operation, [pb[x] for x in ix])
            i = pb[phys[q]]
            z = float(Statevector(small).expectation_value(Pauli("I" * (len(pb) - 1 - i) + "Z" + "I" * i)).real)
            z *= sign_of(c, k, phys[q], rec)
            worst = max(worst, abs(z - answers["D02"][str(q)]))
    print("D02", role, "instances", len(cs), "max |<Z> - answer| =", f"{worst:.2e}")

sim = AerSimulator(method="matrix_product_state")
for role in ("raw", "tw"):
    rec, cs = load("FX-A", role)
    phys = {int(k): v for k, v in rec["mapping"].items()}
    order = [phys[q] for q in CHAIN]; idx = {p: i for i, p in enumerate(order)}
    worst = 0
    for k, c in enumerate(cs[:3]):
        small = QuantumCircuit(len(order))
        for ins in c.data:
            if ins.operation.name in ("measure", "barrier"): continue
            small.append(ins.operation, [idx[c.find_bit(x).index] for x in ins.qubits])
        for i in range(len(order)):
            small.save_expectation_value(Pauli("Z"), [i], label=f"z{i}")
        r = sim.run(small).result().data()
        for i, q in enumerate(CHAIN):
            z = float(r[f"z{i}"]) * sign_of(c, k, order[i], rec)
            worst = max(worst, abs(z - answers["FX-A"][str(q)]))
    print("FX-A", role, "instances checked 3, max |<Z> - answer| =", f"{worst:.2e}")
