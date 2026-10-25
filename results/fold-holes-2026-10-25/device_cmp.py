"""Compile-only comparison (analysis, 2026-10-25): the hole schedule on a device cycle against the zipper (a25) and
Qiskit level 2, TOQB's model circuit, snapshot:marrakesh. The cycle is found by VF2 here (prototype only)."""
import json, sys, os
import numpy as np
import rustworkx as rx
from qiskit import QuantumCircuit, transpile
sys.path.insert(0, os.environ.get('TOQB', '.')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from toqb import task_loop as TL
from toqb.devices import get_device
from toqb.metrics import metrics
from holes import place

CYCLES = [12, 20, 24, 28, 32, 36, 40]


def split_layers(qc, n):
    """TOQB's model circuit as (per layer: list of 1q instructions per logical qubit), final 1q ops, measures."""
    layers, cur, czs, meas = [], [[] for _ in range(n)], 0, []
    for ins in qc.data:
        nm = ins.operation.name
        qs = [qc.find_bit(q).index for q in ins.qubits]
        if nm == "cz":
            czs += 1
            if czs == n:
                layers.append(cur); cur = [[] for _ in range(n)]; czs = 0
        elif nm == "measure":
            meas.append((qs[0], qc.find_bit(ins.clbits[0]).index))
        elif nm == "barrier":
            continue
        else:
            assert len(qs) == 1, nm
            cur[qs[0]].append(ins.operation)
    return layers, cur, meas


def holes_physical(qc, n, cyc, nq, ncl):
    m = len(cyc); occ = place(n, m)
    layers, final, meas = split_layers(qc, n)
    out = QuantumCircuit(nq, ncl)
    for layer in layers:
        pos = {r: p for p, r in enumerate(occ) if r is not None}
        for r in range(n):
            for op in layer[r]:
                out.append(op, [cyc[pos[r]]])
        edges = [p for p in range(m) if occ[p] is not None and occ[(p + 1) % m] is not None
                 and ((occ[p] + 1) % n == occ[(p + 1) % m] or (occ[(p + 1) % m] + 1) % n == occ[p])]
        # commuting CZs in rounds of disjoint pairs (greedy colouring along the cycle), so the schedule is not a chain
        rounds = []
        for p in edges:
            for rd in rounds:
                if all({p, (p + 1) % m}.isdisjoint({q, (q + 1) % m}) for q in rd):
                    rd.append(p); break
            else:
                rounds.append([p])
        for rd in rounds:
            for p in rd:
                out.cz(cyc[p], cyc[(p + 1) % m])
        starts = [p for p in range(m) if occ[p] is None and occ[(p - 1) % m] is not None]
        for p in starts:
            pa, pb = (p - 1) % m, (p + 1) % m
            k = 1
            while occ[pb] is None:
                pb = (pb + 1) % m; k += 1
            cur = pa
            for _ in range(k):
                nx = (cur + 1) % m
                out.cx(cyc[cur], cyc[nx]); out.cx(cyc[nx], cyc[cur])
                occ[nx], occ[cur] = occ[cur], None
                cur = nx
            out.cz(cyc[cur], cyc[pb])
    pos = {r: p for p, r in enumerate(occ) if r is not None}
    for r in range(n):
        for op in final[r]:
            out.append(op, [cyc[pos[r]]])
    for q, c in meas:
        out.measure(cyc[pos[q]], c)
    return out


def main():
    dev = get_device("snapshot:marrakesh")
    T = dev.target
    G = rx.PyGraph(); G.add_nodes_from(range(T.num_qubits))
    for qa, p in T["cz"].items():
        if qa is not None and (p is None or p.error is None or p.error < 1):
            a, b = sorted(qa)
            if not G.has_edge(a, b):
                G.add_edge(a, b, None)
    found = {}
    for m in CYCLES:
        it = rx.vf2_mapping(G, rx.generators.cycle_graph(m), subgraph=True, induced=False, id_order=False,
                            call_limit=5_000_000)
        try:
            mp = next(it)  # device node -> cycle node
            inv = {v: k for k, v in mp.items()}
            found[m] = [inv[i] for i in range(m)]
        except StopIteration:
            pass
    print("cycles found:", sorted(found))
    rng = np.random.default_rng(20261025)
    rows = []
    for n in [int(v) for v in sys.argv[1].split(',')]:
        for L in (16,):
            theta = rng.uniform(-1, 1, TL.n_params(n, L)); x = rng.uniform(-1, 1, n)
            qc = TL.model_circuit(TL.angle_list(theta, x, n, L, np.pi / 2), n, L)
            m = min(c for c in found if c >= n)
            ph = holes_physical(qc, n, found[m], T.num_qubits, qc.num_clbits)
            tc = transpile(ph, target=T, initial_layout=list(range(T.num_qubits)), optimization_level=1,
                           routing_method="none", seed_transpiler=1)
            mt = metrics(tc, dev)
            rows.append(dict(n=n, L=L, m=m, holes=m - n, q2=int(mt["q2"]), duration_us=round(mt["duration_s"] * 1e6, 2),
                             q2_per_layer=round(mt["q2"] / L, 2)))
            print(json.dumps(rows[-1]), flush=True)
    json.dump(rows, open("holes_cost.json", "w"), indent=1)


if __name__ == "__main__":
    main()
