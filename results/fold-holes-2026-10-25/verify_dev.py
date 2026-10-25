import sys, numpy as np, rustworkx as rx
import os; sys.path.insert(0, os.environ.get('TOQB', '.')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from toqb import task_loop as TL
from toqb.devices import get_device
from device_cmp import holes_physical


def p1_all(c, nlog=None):
    act = sorted({c.find_bit(q).index for i in c.data for q in i.qubits if i.operation.name not in ("barrier", "delay")})
    idx = {q: k for k, q in enumerate(act)}
    s, meas = QuantumCircuit(len(act)), {}
    for i in c.data:
        nm = i.operation.name
        if nm in ("barrier", "delay"): continue
        if nm == "measure":
            meas[c.find_bit(i.clbits[0]).index] = idx[c.find_bit(i.qubits[0]).index]; continue
        s.append(i.operation, [idx[c.find_bit(q).index] for q in i.qubits])
    sv = Statevector(s)
    return [float(sv.probabilities([meas[k]])[1]) for k in sorted(meas)]


dev = get_device("snapshot:marrakesh"); T = dev.target
G = rx.PyGraph(); G.add_nodes_from(range(T.num_qubits))
for qa in T["cz"]:
    if qa is not None:
        a, b = sorted(qa)
        if not G.has_edge(a, b): G.add_edge(a, b, None)
mp = next(rx.vf2_mapping(G, rx.generators.cycle_graph(12), subgraph=True, induced=False, id_order=False))
cyc = [{v: k for k, v in mp.items()}[i] for i in range(12)]
rng = np.random.default_rng(5)
for n in (9, 10, 11):
    for L in (2, 4):
        qc = TL.model_circuit(TL.angle_list(rng.uniform(-1, 1, TL.n_params(n, L)), rng.uniform(-1, 1, n), n, L, np.pi / 2), n, L)
        ph = holes_physical(qc, n, cyc, T.num_qubits, qc.num_clbits)
        tc = transpile(ph, target=T, initial_layout=list(range(T.num_qubits)), optimization_level=1, routing_method="none")
        a, b = p1_all(tc), p1_all(qc)
        print(n, L, "clbits", len(a), "max |dP1|", max(abs(x - y) for x, y in zip(a, b)))
