"""Diagonal (hyper-edge) form of utility_tn.network (home VS Claude, 2026-11-10): an R_ZZ gate is diagonal, so it
adds no new index; it is a 2 x 2 weight w[i, j] = exp(i pi/4 z_i z_j) on the two qubits' current indices (hyper-
edges: an index may appear in more than two tensors). R_X still opens a new index. The same light cone and join as
utility_tn.network. Checked against utility_exact.tn_value on small cases (check)."""
import math, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import utility_tn as T, utility_exact as UE


def network_diag(obs, t, extra_rx, edges):
    import rustworkx as rx_
    g = rx_.PyGraph(); g.add_nodes_from(range(127)); g.add_edges_from_no_data(edges)
    D = rx_.distance_matrix(g)
    dist = {q: min(D[q][s] for s in obs) for q in range(127)}
    layers = []
    for s in range(1, t + 1):
        r = t - s
        layers.append(("rx", sorted(q for q in range(127) if dist[q] <= r + 1)))
        layers.append(("zz", [(a, b) for a, b in edges if min(dist[a], dist[b]) <= r]))
    if extra_rx:
        layers.append(("rx", sorted(q for q in range(127) if dist[q] <= 0)))
    qubits = sorted({q for kind, xs in layers for q in (xs if kind == "rx" else [v for e in xs for v in e])} | set(obs))
    inputs, slots = [], []
    for side in ("k", "b"):
        cur = {q: f"{side}{q}_0" for q in qubits}
        n = {q: 0 for q in qubits}
        for q in qubits:
            inputs.append((cur[q],)); slots.append(("ket0",))
        for kind, xs in layers:
            if kind == "rx":
                for q in xs:
                    n[q] += 1
                    new = f"{side}{q}_{n[q]}"
                    inputs.append((new, cur[q])); slots.append(("rx", side == "b"))
                    cur[q] = new
            else:
                for a, b in xs:
                    inputs.append((cur[a], cur[b])); slots.append(("zzd", side == "b"))
        if side == "k":
            ket_final = dict(cur)
        else:
            bra_final = dict(cur)
    ren = {}
    for q in qubits:
        if q in obs:
            inputs.append((bra_final[q], ket_final[q])); slots.append(("pauli", obs[q]))
        else:
            ren[bra_final[q]] = ket_final[q]
    inputs = [tuple(ren.get(i, i) for i in ix) for ix in inputs]
    size = {i: 2 for ix in inputs for i in ix}
    return inputs, (), size, slots, len(qubits)


def arrays_diag(slots, theta):
    rx = np.array([[math.cos(theta / 2), -1j * math.sin(theta / 2)], [-1j * math.sin(theta / 2), math.cos(theta / 2)]])
    w = np.exp(1j * math.pi / 4 * np.array([[1, -1], [-1, 1]]))        # exp(-i (-pi/2)/2 z z) on (z_a, z_b)
    out = []
    for sl in slots:
        if sl[0] == "ket0":
            out.append(np.array([1.0 + 0j, 0.0]))
        elif sl[0] == "rx":
            out.append(rx.conj() if sl[1] else rx)
        elif sl[0] == "zzd":
            out.append(w.conj() if sl[1] else w)
        else:
            out.append(UE.P1[sl[1]])
    return out


def check():
    import cotengra as ctg
    edges = UE.eagle_edges()
    worst = 0.0
    for obs, t, ex in (({106: "Z"}, 3, False), ({13: "X", 9: "Y", 8: "Z"}, 2, True), (UE.W10, 3, False)):
        inputs, output, size, slots, nq = network_diag(obs, t, ex, edges)
        for th in (0.3, 0.9, math.pi / 2):
            a = complex(ctg.array_contract(arrays_diag(slots, th), inputs, output, size_dict=size, optimize="auto")).real
            b = UE.tn_value(obs, edges, th, t, ex)[0]
            worst = max(worst, abs(a - b))
    print(f"diagonal form against tn_value: worst {worst:.2e}")


def plan(name, max_time, target, par):
    import cotengra as ctg
    obs, t, ex = T.OBS[name]
    inputs, output, size, slots, nq = network_diag(obs, t, ex, UE.eagle_edges())
    t0 = time.time()
    opt = ctg.HyperOptimizer(methods=["kahypar", "greedy"], max_time=max_time, max_repeats=10 ** 6, minimize="flops",
                             slicing_opts=dict(target_size=2 ** target), parallel=par, progbar=False)
    tree = opt.search(inputs, output, size)
    sl = list(tree.sliced_inds)
    print(f"{name} (diagonal form): {len(inputs)} tensors; search {time.time() - t0:.0f} s; slices {2 ** len(sl)}, width "
          f"{tree.contraction_width():.1f}, total cost 10^{math.log10(tree.contraction_cost()):.2f}", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "check":
        check()
    else:
        plan(sys.argv[2], float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
