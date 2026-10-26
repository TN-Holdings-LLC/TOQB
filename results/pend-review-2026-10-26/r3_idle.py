"""Review 3 (request 2, estimate only): per-qubit idle time of fold:pend's compiled circuit (L = 16, n = 13-18,
snapshot:marrakesh Target durations), as emitted today and with one formula rule for the order of commuting plain
CZs ("chain edge first"). Nothing here is chosen by error values; the rule depends only on the ring and the pendant
positions. Idle = the qubit's delays between its first and its last operation after ALAP scheduling.
usage: python r3_idle.py TOQB_DIR"""
import sys
import numpy as np
sys.path.insert(0, sys.argv[1])
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from toqb import fold as F, task_loop as TL
from toqb.devices import get_device

def pend_circuit_chain_first(qc, cyc, pend, nq):
    """fold.pend_circuit with one change: among the plain CZs ready in a step, those that are the 'other' ring edge
    of a pendant block still to come are emitted first (in their own rounds), then the rest. All plain CZs commute,
    so the circuit is the same unitary; only each qubit's order of its CZs changes."""
    n, layers, final, meas = F.read_ring(qc)
    m = len(cyc)
    oc, op, r = [None] * m, {}, 0
    for p in range(m):
        oc[p] = r; r += 1
        if p in pend:
            op[p] = r; r += 1
    def where():
        w = {v: cyc[p] for p, v in enumerate(oc)}; w.update({v: pend[p] for p, v in op.items()}); return w
    start = where()
    out = QuantumCircuit(nq, qc.num_clbits)
    def other_edge(p):
        u, v = oc[p], op[p]
        return frozenset((u, (u - 1) % n)) if (u + 1) % n == v else frozenset((u, (u + 1) % n))
    for layer in layers:
        w = where()
        for i in range(n):
            for o in layer[i]:
                out.append(o, [w[i]])
        need = {frozenset((i, (i + 1) % n)) for i in range(n)}
        while need:
            progress = False
            chain = {other_edge(p) for p in op if frozenset((oc[p], op[p])) in need}
            ready = [p for p in range(m) if frozenset((oc[p], oc[(p + 1) % m])) in need]
            for group in ([p for p in ready if frozenset((oc[p], oc[(p + 1) % m])) in chain],
                          [p for p in ready if frozenset((oc[p], oc[(p + 1) % m])) not in chain]):
                rounds = []
                for p in group:
                    for rd in rounds:
                        if all({p, (p + 1) % m}.isdisjoint({q, (q + 1) % m}) for q in rd):
                            rd.append(p); break
                    else:
                        rounds.append([p])
                for rd in rounds:
                    for p in rd:
                        out.cz(cyc[p], cyc[(p + 1) % m]); need.discard(frozenset((oc[p], oc[(p + 1) % m])))
                    progress = True
            for p in sorted(op):
                u, v = oc[p], op[p]
                e = frozenset((u, v))
                if e in need and other_edge(p) not in need:
                    a, b = cyc[p], pend[p]
                    out.h(b); out.cx(b, a); out.cx(a, b); out.h(a)
                    oc[p], op[p] = v, u
                    need.discard(e); progress = True
            if not progress:
                raise F.FoldRefused("no step")
    w = where()
    for i in range(n):
        for o in final[i]:
            out.append(o, [w[i]])
    for q, c in meas:
        out.measure(w[q], c)
    return out, [start[i] for i in range(n)], [w[i] for i in range(n)]

dev = get_device("snapshot:marrakesh"); t = dev.target
pm = generate_preset_pass_manager(1, target=t, initial_layout=list(range(t.num_qubits)), routing_method="none", seed_transpiler=0)
def dur(name, qs):
    if name in ("barrier", "rz", "delay"):
        return 0.0
    p = t[name].get(tuple(qs)) if name in t.operation_names else None
    return float(p.duration) if p is not None and p.duration is not None else 0.0

def idle(c):
    """ALAP schedule from the circuit's per-qubit order with the Target's durations (measurements aligned at the
    end): per qubit, the idle time between its first and its last non-measure operation; and the duration."""
    ins = [(i.operation.name, [c.find_bit(q).index for q in i.qubits]) for i in c.data if i.operation.name != "barrier"]
    # ASAP forward for the total length
    tcur = {}
    for nm, qs in ins:
        s0 = max((tcur.get(q, 0.0) for q in qs), default=0.0)
        for q in qs:
            tcur[q] = s0 + dur(nm, qs)
    T = max(tcur.values())
    # ALAP: backward pass
    tl = {}
    seg = {}
    for nm, qs in reversed(ins):
        e = min((tl.get(q, T) for q in qs), default=T)
        s0 = e - dur(nm, qs)
        for q in qs:
            tl[q] = s0
            if nm != "measure":
                seg.setdefault(q, []).append((s0, e))
    res = {}
    for q, sg in seg.items():
        a, b = min(x[0] for x in sg), max(x[1] for x in sg)
        res[q] = (b - a) - sum(x[1] - x[0] for x in sg)
    return res, T

L = 16
print(f"{'n':>3} {'variant':<12} {'duration us':>11} {'idle sum us':>11} {'idle max us':>11} {'worst qubits (us)':<40}")
for n in range(13, 19):
    m, shape, cyc, pend = F.pend_place(t, n)
    rng = np.random.default_rng(n)
    qc = TL.model_circuit(TL.angle_list(rng.uniform(-1, 1, TL.n_params(n, L)), rng.uniform(-1, 1, n), n, L, np.pi / 2), n, L)
    for name, fn in (("as emitted", F.pend_circuit), ("chain first", pend_circuit_chain_first)):
        hc, init, fin = fn(qc, cyc, pend, t.num_qubits)
        c = pm.run(hc)
        res, total = idle(c)
        worst = sorted(res.items(), key=lambda kv: -kv[1])[:4]
        role = lambda q: ("P" if q in pend.values() else "C")  # noqa: E731
        print(f"{n:>3} {name:<12} {total*1e6:>11.3f} {sum(res.values())*1e6:>11.2f} {max(res.values())*1e6:>11.2f} "
              + ", ".join(f"{role(q)}{q}:{v*1e6:.2f}" for q, v in worst))
