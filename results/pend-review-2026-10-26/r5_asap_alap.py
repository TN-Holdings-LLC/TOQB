"""Review 5: idle per qubit under ASAP against ALAP placement of the same circuit (fold:pend as emitted, L = 16).
usage: python r5_asap_alap.py TOQB_DIR"""
import sys
import numpy as np
sys.path.insert(0, sys.argv[1])
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
def windows(ins, alap):
    seq = list(reversed(ins)) if alap else ins
    tc, seg = {}, {}
    for nm, qs in seq:
        s0 = max(tc.get(q, 0.0) for q in qs)
        for q in qs:
            tc[q] = s0 + dur(nm, qs)
            if nm != "measure":
                seg.setdefault(q, []).append((s0, s0 + dur(nm, qs)))
    return {q: (max(e for _, e in sg) - min(s for s, _ in sg)) - sum(e - s for s, e in sg) for q, sg in seg.items()}
L = 16
for n in range(13, 19):
    m, shape, cyc, pend = F.pend_place(t, n)
    rng = np.random.default_rng(n)
    qc = TL.model_circuit(TL.angle_list(rng.uniform(-1, 1, TL.n_params(n, L)), rng.uniform(-1, 1, n), n, L, np.pi / 2), n, L)
    c = pm.run(F.pend_circuit(qc, cyc, pend, t.num_qubits)[0])
    ins = [(i.operation.name, [c.find_bit(q).index for q in i.qubits]) for i in c.data if i.operation.name != "barrier"]
    a, b = windows(ins, False), windows(ins, True)
    print(f"n {n}: idle sum ASAP {sum(a.values())*1e6:.2f} us, ALAP {sum(b.values())*1e6:.2f} us; mean per qubit ASAP {np.mean(list(a.values()))*1e6:.2f}, ALAP {np.mean(list(b.values()))*1e6:.2f} us")
