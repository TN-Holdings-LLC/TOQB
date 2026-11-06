"""Offline design of a fixed spread template (owner 2026-11-06: spread the load over every bridge instead of one;
a template designed once, then used as a rule by translation; nothing is searched at placement time).

Design space: static layouts of the 4 x 2 x 2 lattice in a window of Heron r2 (rows 0..R-1, all columns and the
bridges between them). Every bond is a parity chain through empty qubits along a fixed shortest path
(2 (d - 1) + 1 CZ). Objective, in order: no unreachable bond, at most Q touched qubits (for the simulators), the
largest number of bonds through one qubit (the load), then CZ per step. Simulated annealing from many seeds on all
cores; the Pareto front (best CZ for each load) is written out.

usage: python embank_search.py OUT.json [--rows 4] [--minutes 30] [--max-qubits 30] [--workers N]
"""
import argparse
import collections
import json
import math
import multiprocessing as mp
import os
import random
import time

import embank as E


def window(rows):
    keep = set()
    for r in range(rows):
        keep |= {20 * r + c for c in range(16)}
        if r < rows - 1:
            keep |= {20 * r + 16 + k for k in range(4)}
    edges = {e for e in E.heron_edges() if e[0] in keep and e[1] in keep}
    adj = collections.defaultdict(list)
    for a, b in sorted(edges):
        adj[a].append(b)
        adj[b].append(a)
    return sorted(keep), adj


def routes(place, adj, bonds):
    """Shortest path through empty qubits per bond (fixed tie-break: neighbours in label order)."""
    data = set(place)
    out = []
    for i, j in bonds:
        a, b = place[i], place[j]
        prev = {a: None}
        q = collections.deque([a])
        while q:
            u = q.popleft()
            if u == b:
                break
            for w in adj[u]:
                if w not in prev and (w == b or w not in data):
                    prev[w] = u
                    q.append(w)
        if b not in prev:
            out.append(None)
            continue
        path = [b]
        while prev[path[-1]] is not None:
            path.append(prev[path[-1]])
        out.append(path[::-1])
    return out


def cost(place, adj, bonds, max_qubits):
    rs = routes(place, adj, bonds)
    bad = sum(r is None for r in rs)
    load = collections.Counter()
    cz, touched = 0, set(place)
    for r in rs:
        if r is None:
            continue
        cz += 2 * (len(r) - 2) + 1
        for u in r[1:-1]:
            load[u] += 1
        touched |= set(r)
    ml = max(load.values()) if load else 0
    over = max(0, len(touched) - max_qubits)
    return (bad, over, ml, cz), dict(bad=bad, touched=len(touched), max_load=ml, cz=cz)


def anneal(args):
    seed, rows, minutes, max_qubits = args
    rnd = random.Random(seed)
    qubits, adj = window(rows)
    rowq = [q for q in qubits if q % 20 < 16]
    sites, bonds = E.lattice()
    n = len(sites)
    place = rnd.sample(rowq, n)
    key, info = cost(place, adj, bonds, max_qubits)
    w = lambda k: 1e5 * k[0] + 1e4 * k[1] + 300 * k[2] + k[3]
    cur = w(key)
    front = {}
    t_end = time.time() + 60 * minutes
    T0, it = 200.0, 0
    while time.time() < t_end:
        it += 1
        T = T0 * (1 - min(1.0, (time.time() - (t_end - 60 * minutes)) / (60 * minutes))) + 0.5
        new = list(place)
        if rnd.random() < 0.5:
            i = rnd.randrange(n)
            free = [q for q in rowq if q not in new]
            new[i] = rnd.choice(free)
        else:
            i, j = rnd.sample(range(n), 2)
            new[i], new[j] = new[j], new[i]
        k2, inf2 = cost(new, adj, bonds, max_qubits)
        v2 = w(k2)
        if v2 <= cur or rnd.random() < math.exp((cur - v2) / T):
            place, key, info, cur = new, k2, inf2, v2
            if key[0] == 0 and key[1] == 0:
                ml = key[2]
                if ml not in front or key[3] < front[ml]["cz"]:
                    front[ml] = dict(info, place=list(place), seed=seed)
    return front, it


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--rows", type=int, default=4)
    ap.add_argument("--minutes", type=float, default=30)
    ap.add_argument("--max-qubits", type=int, default=30)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()
    with mp.Pool(a.workers) as pool:
        res = pool.map(anneal, [(s, a.rows, a.minutes, a.max_qubits) for s in range(a.workers)])
    front, its = {}, 0
    for f, it in res:
        its += it
        for ml, v in f.items():
            if ml not in front or v["cz"] < front[ml]["cz"]:
                front[ml] = v
    out = dict(rows=a.rows, minutes=a.minutes, max_qubits=a.max_qubits, workers=a.workers, iterations=its,
               front=[front[k] for k in sorted(front)])
    json.dump(out, open(a.out, "w"), indent=1)
    for v in out["front"]:
        print(f"max load {v['max_load']}: CZ/step {v['cz']}  touched {v['touched']}  (seed {v['seed']})")
    print(f"iterations {its}")


if __name__ == "__main__":
    main()
