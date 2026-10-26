"""Review 4: is fold:pend's duration already at the per-qubit lower bound? Per qubit: busy time (sum of its own gate
durations, measure excluded) and idle (ALAP, between first and last op). The hub qubits (cycle nodes with a
pendant) carry 4 two-qubit gates per layer, the others 2. usage: python r4_bound.py TOQB_DIR"""
import sys, statistics
import numpy as np
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[1] + "/../review")
from toqb import fold as F, task_loop as TL
from toqb.devices import get_device
from qiskit.transpiler import generate_preset_pass_manager
t = get_device("snapshot:marrakesh").target
pm = generate_preset_pass_manager(1, target=t, initial_layout=list(range(t.num_qubits)), routing_method="none", seed_transpiler=0)
def dur(name, qs):
    if name in ("barrier", "rz", "delay", "measure"):
        return 0.0
    p = t[name].get(tuple(qs)) if name in t.operation_names else None
    return float(p.duration) if p is not None and p.duration is not None else 0.0
czs = [p.duration for q, p in t["cz"].items() if q is not None and p is not None and p.duration]
sxs = [p.duration for q, p in t["sx"].items() if q is not None and p is not None and p.duration]
print(f"Target durations: cz median {statistics.median(czs)*1e9:.0f} ns (range {min(czs)*1e9:.0f}-{max(czs)*1e9:.0f}), sx median {statistics.median(sxs)*1e9:.0f} ns")
L = 16
for n in (13, 15, 17, 18):
    m, shape, cyc, pend = F.pend_place(t, n)
    rng = np.random.default_rng(n)
    qc = TL.model_circuit(TL.angle_list(rng.uniform(-1, 1, TL.n_params(n, L)), rng.uniform(-1, 1, n), n, L, np.pi / 2), n, L)
    c = pm.run(F.pend_circuit(qc, cyc, pend, t.num_qubits)[0])
    ins = [(i.operation.name, [c.find_bit(q).index for q in i.qubits]) for i in c.data if i.operation.name != "barrier"]
    busy, n2q, nsx = {}, {}, {}
    tcur = {}
    for nm, qs in ins:
        s0 = max(tcur.get(q, 0.0) for q in qs)
        for q in qs:
            tcur[q] = s0 + dur(nm, qs); busy[q] = busy.get(q, 0) + dur(nm, qs)
            if len(qs) == 2: n2q[q] = n2q.get(q, 0) + 1
            if nm == "sx": nsx[q] = nsx.get(q, 0) + 1
    T = max(tcur.values())
    hubs = [cyc[p] for p in pend]
    others = [q for q in cyc if q not in hubs]
    pq = list(pend.values())
    def row(lbl, qs):
        return f"{lbl}: busy {min(busy[q] for q in qs)*1e6:.2f}-{max(busy[q] for q in qs)*1e6:.2f} us, 2q/layer {min(n2q[q] for q in qs)/L:.0f}-{max(n2q[q] for q in qs)/L:.0f}, sx/layer {min(nsx.get(q,0) for q in qs)/L:.1f}-{max(nsx.get(q,0) for q in qs)/L:.1f}"
    print(f"n {n}: duration (ASAP, measure excluded) {T*1e6:.3f} us; {row('hubs', hubs)}; {row('pendants', pq)}; {row('other cycle', others)}")
