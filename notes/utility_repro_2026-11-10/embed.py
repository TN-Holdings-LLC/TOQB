"""Embeddings of IBM Eagle's 127-qubit graph in a Heron r2 device record, and whether each observable's light cone
avoids the failed elements (home, 2026-11-10). usage: python embed.py DEVICE_JSON [...]"""
import json
import sys

import rustworkx as rx
from qiskit_ibm_runtime import fake_provider as fp

OBS = {"Z106_t4": ([106], 4), "w10_t5": ([13, 29, 31, 9, 30, 8, 12, 17, 28, 32], 5),
       "w17_t5": ([37, 41, 52, 56, 57, 58, 62, 79, 75, 38, 40, 42, 63, 72, 80, 90, 91], 5), "Z62_t20": ([62], 20)}


def graph_of(edges, n):
    g = rx.PyGraph()
    g.add_nodes_from(range(n))
    g.add_edges_from_no_data(sorted({tuple(sorted(e)) for e in edges}))
    return g


def main(paths):
    eagle = graph_of(fp.FakeSherbrooke().configuration().coupling_map, 127)
    D = rx.distance_matrix(eagle)
    for p in paths:
        d = json.load(open(p))
        full = graph_of([tuple(e) for e in d["couplers"]], d["num_qubits"])
        fc = {tuple(sorted(e)) for e in d["failed_couplers"]}
        fq = set(d["failed_qubits"])
        maps = []
        for m in rx.vf2_mapping(full, eagle, subgraph=True, induced=False, id_order=True):
            if frozenset(m) not in {frozenset(x) for x in maps}:
                maps.append(m)            # heron -> eagle
        for k, m in enumerate(maps):
            bad_q = {m[q] for q in fq if q in m}
            bad_e = {(m[a], m[b]) for a, b in fc if a in m and b in m and eagle.has_edge(m[a], m[b])}
            out = []
            for name, (sup, r) in OBS.items():
                cone = {q for q in range(127) if min(D[q][s] for s in sup) <= r}
                hit = [q for q in bad_q if q in cone] + [e for e in bad_e if e[0] in cone or e[1] in cone]
                out.append(f"{name} {'clear' if not hit else 'hit'}")
            print(d["name"], "embedding", k, "|", "; ".join(out))


if __name__ == "__main__":
    main(sys.argv[1:])
