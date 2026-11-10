"""Acceptance of psf_os.card (2026-11-10): existing problems rewritten as cards; the exact answers of the circuits made
from the cards must equal those of the existing modules (difference <= 1e-10). The existing modules are only read.

  A  kicked Ising 4x2x2, theta 0.6, t 1-4          against psf_os.grid3d.exact
  B  Heisenberg XXX 4x2x2, dt 0.05, t 1-4, Neel    against TOQB gpu/heis3d.exact_from_log
       B1 a textbook order (bonds coloured into 6 commuting groups)
       B2 the heisE layouts (old, carry, line) on the 11-08 ibm_kingston record, every candidate, the bond order of
          each layout as per-step group orders; also against the released answer table heis_answers_Ek.json
  C  Schwinger N 6, M1, 1 and 2 steps              against TOQB gpu/schwinger.z_sites of its own circuit
For B2 and C the same cards with one order for every step (the base format) are also computed, to show whether the
per-step orders are needed. Only differences are printed, no answer values.

usage: PYTHONPATH=<psf-os>:<TOQB>/gpu python card_accept.py TOQB OUT
"""
import json
import os
import sys

import numpy as np

from psf_os import card as C

TOL = 1e-10


def maxdiff(a, b):
    return max(abs(a[k] - b[k]) for k in b)


def verdict(d):
    return "MATCH" if d <= TOL else "DIFFERS"


def dump(card, out, name):
    with open(os.path.join(out, name), "w", encoding="utf-8", newline="\n") as f:
        json.dump(card, f, indent=1)


# --- A: kicked Ising ---------------------------------------------------------------------------------------------

def ising_card(t, theta=0.6, size=(4, 2, 2)):
    n = int(np.prod(size))
    return {"card": 1, "name": f"kicked Ising {'x'.join(map(str, size))}, theta {theta}, t {t}",
            "lattice": {"kind": "grid3d", "size": list(size)},
            "hamiltonian": {"terms": [
                {"pauli": "ZZ", "on": "edges", "coef": -np.pi / 4, "group": "zz"},   # RZZ(-pi/2) = exp(+i pi/4 ZZ)
                {"pauli": "X", "on": "sites", "coef": theta / 2, "group": "x"}]},     # RX(theta) = exp(-i theta/2 X)
            "initial": {"bits": "0" * n},
            "time": {"dt": 1.0, "steps": t, "order": ["zz", "x"]},
            "measure": [{"op": "Z", "sites": "all"}]}


def part_a(out):
    from psf_os import grid3d as G
    print("== A kicked Ising 4x2x2, theta 0.6 (psf_os.grid3d.exact)")
    worst = 0.0
    for t in (1, 2, 3, 4):
        card = ising_card(t)
        if t == 1:
            dump(card, out, "kicked_ising_4x2x2.json")
        e = C.exact(card)
        ref = {f"Z_{q}": v for q, v in G.exact(4, 2, 2, t, 0.6).items()}
        d = maxdiff(e, ref)
        worst = max(worst, d)
        print(f"t {t}: 16 sites, max |card - grid3d| {d:.1e}  {verdict(d)}")
    return worst


# --- B: Heisenberg -----------------------------------------------------------------------------------------------

def heis_terms(bonds_by_group, delta):
    terms = []
    for g, bonds in bonds_by_group.items():
        for a, b in bonds:
            for p, c in (("XX", 1.0), ("YY", 1.0), ("ZZ", delta)):
                terms.append({"pauli": p, "sites": [a, b], "coef": c, "group": g})
    return terms


def neel_bits(L, M, N):
    import itertools
    return "".join("1" if (x + y + z) % 2 else "0" for x, y, z in itertools.product(range(L), range(M), range(N)))


def heis_textbook_card(t, dt=0.05, delta=1.0, size=(4, 2, 2)):
    import itertools
    L, M, N = size
    coords = list(itertools.product(range(L), range(M), range(N)))
    idx = {c: i for i, c in enumerate(coords)}
    groups = {}
    for c in coords:
        for ax in range(3):
            d = list(c)
            d[ax] += 1
            if tuple(d) in idx:
                groups.setdefault(f"ax{ax}p{c[ax] % 2}", []).append((idx[c], idx[tuple(d)]))
    order = sorted(groups)
    return {"card": 1, "name": f"Heisenberg XXX {L}x{M}x{N}, dt {dt}, t {t}, Neel, textbook order",
            "lattice": {"kind": "grid3d", "size": [L, M, N]},
            "hamiltonian": {"terms": heis_terms(groups, delta)},
            "initial": {"bits": neel_bits(L, M, N)},
            "time": {"dt": dt, "steps": t, "order": order},
            "measure": [{"op": "Z", "sites": "all"}]}, groups, order


def heis_log_card(log, t, dt, delta=1.0, size=(4, 2, 2), name=""):
    """Per bond one group (its XX, YY, ZZ commute); the layout's bond order split into t per-step orders."""
    L, M, N = size
    per = len(log) // t
    if per * t != len(log):
        raise ValueError("log length not a multiple of t")
    groups = {}
    for a, b in log[:per]:
        groups[f"b{min(a, b)}_{max(a, b)}"] = [(min(a, b), max(a, b))]
    orders = [[f"b{min(a, b)}_{max(a, b)}" for a, b in log[s * per:(s + 1) * per]] for s in range(t)]
    card = {"card": 1, "name": name, "lattice": {"kind": "grid3d", "size": [L, M, N]},
            "hamiltonian": {"terms": heis_terms(groups, delta)},
            "initial": {"bits": neel_bits(L, M, N)},
            "time": {"dt": dt, "steps": t, "orders": orders},
            "measure": [{"op": "Z", "sites": "all"}]}
    return card, orders


def part_b(toqb, out):
    import heis3d as H
    from psf_os import device as Dv
    from psf_os import grid3d as G
    dt, delta = 0.05, 1.0
    print(f"== B1 Heisenberg XXX 4x2x2, dt {dt}, Neel, textbook order (heis3d.exact_from_log of the same bond order)")
    worst = 0.0
    for t in (1, 2, 3, 4):
        card, groups, order = heis_textbook_card(t, dt, delta)
        if t == 1:
            dump(card, out, "heisenberg_4x2x2_textbook.json")
        log = [bd for _ in range(t) for g in order for bd in groups[g]]
        e = C.exact(card)
        ref = {f"Z_{k}": v for k, v in H.exact_from_log(4, 2, 2, log, dt, delta).items()}
        d = maxdiff(e, ref)
        worst = max(worst, d)
        print(f"t {t}: {len(log)} bonds, 6 groups, max |card - heis3d| {d:.1e}  {verdict(d)}")
    rec = os.path.join(toqb, "results", "os3d-heisE-kingston-2026-11-08")
    devdir = os.path.join(rec, "fetch_in", "ibm_kingston", "dev")
    dev = Dv.Device.load(devdir)
    table = json.load(open(os.path.join(rec, "answers", "heis_answers_Ek.json")))
    print(f"== B2 heisE layouts on the 11-08 ibm_kingston record ({dev.name}), dt {dt}: per-step orders from the bond "
          f"logs; against heis3d.exact_from_log and the released table heis_answers_Ek.json")
    cands, avoid = [], []
    while len(cands) < 4:   # as gpu/heis3d_build.py finds its candidates
        try:
            _, _, _, _, where = H.physical(dev, 2, 2, 1, dt, delta, avoid=avoid, carry=False)
        except G.Refused:
            break
        cands.append(dict(index=len(cands), r0=where["r0"], c0=where["c0"], avoid=list(avoid)))
        avoid.append((where["r0"], where["c0"]))
    worst_one = 0.0
    periodic = {}
    for c in cands:
        for head, carry, vname in (("h3d", False, "old"), ("h3c", True, "carry"), ("h3l", "line", "line")):
            for t in (1, 2, 3, 4):
                if carry == "line":
                    _, _, _, log, where = H.physical_line(dev, t, dt, delta, avoid=c["avoid"])
                else:
                    _, _, _, log, where = H.physical(dev, 2, 2, t, dt, delta, avoid=c["avoid"], carry=carry)
                tag = f"{head}{c['index']}_t{t}"
                card, orders = heis_log_card(log, t, dt, delta, name=f"heisE {vname} candidate {c['index']} "
                                             f"(r0 {c['r0']}, c0 {c['c0']}) t {t} on {dev.name}")
                ok = all(sorted(o) == sorted(orders[0]) for o in orders)
                if not ok:
                    raise SystemExit(f"STOP: {tag}: a step does not apply every bond once")
                if (c["index"], vname, t) == (0, "line", 4):
                    dump(card, out, "heisenberg_4x2x2_heisE_line_kingston_c0_t4.json")
                e = C.exact(card)
                ref = {f"Z_{k}": v for k, v in H.exact_from_log(4, 2, 2, log, dt, delta).items()}
                tab = {f"Z_{k}": v for k, v in table[tag].items()}
                d1, d2 = maxdiff(e, ref), maxdiff(e, tab)
                worst = max(worst, d1, d2)
                distinct = len({tuple(o) for o in orders})
                periodic.setdefault(vname, set()).add(distinct)
                one = dict(card, time=dict(dt=dt, steps=t, order=orders[0]))
                d3 = maxdiff(C.exact(one), ref)
                worst_one = max(worst_one, d3)
                print(f"{tag} ({vname}, r0 {c['r0']}, c0 {c['c0']}): {len(log)} bonds, {distinct} distinct step "
                      f"order(s); card - heis3d {d1:.1e}, card - table {d2:.1e}  {verdict(max(d1, d2))}; with one "
                      f"order (step 1's) for every step {d3:.1e}")
    print(f"B2: distinct step orders per layout over t 1-4: "
          f"{ {k: sorted(v) for k, v in periodic.items()} }; one order for every step: worst {worst_one:.1e}")
    return worst


# --- C: Schwinger -----------------------------------------------------------------------------------------------

def schwinger_card(n, steps, params, dt):
    import schwinger as S
    _, w, J, m, eps0 = params
    A, h, hop = S.couplings(n, w, J, m, eps0)
    terms = [{"pauli": "Z", "sites": [k - 1], "coef": v, "group": "z"} for k, v in h.items() if v != 0]
    at = list(range(1, n + 1))
    layers = [p0 for _ in range(n // 2) for p0 in (0, 1)][:n]
    names = []
    for j, p0 in enumerate(layers):   # step 1's layers as groups of site pairs (disjoint, so they commute)
        g = f"layer{j + 1}"
        names.append(g)
        for p in range(p0, n - 1, 2):
            a, b = sorted((at[p], at[p + 1]))
            if A[(a, b)] != 0:
                terms.append({"pauli": "ZZ", "sites": [a - 1, b - 1], "coef": A[(a, b)], "group": g})
            if b - a == 1:
                terms += [{"pauli": q, "sites": [a - 1, b - 1], "coef": hop, "group": g} for q in ("XX", "YY")]
            at[p], at[p + 1] = at[p + 1], at[p]
    edges = [[a, b] for a in range(n) for b in range(a + 1, n)]
    bits = "".join("1" if k % 2 == 0 else "0" for k in range(1, n + 1))   # bare vacuum: X on the even sites
    card = {"card": 1, "name": f"Schwinger N {n}, {params[0]}, dt {dt}, {steps} step(s)",
            "lattice": {"kind": "graph", "sites": n, "edges": edges},
            "hamiltonian": {"terms": terms},
            "initial": {"bits": bits},
            "time": {"dt": dt, "steps": steps, "orders": [["z"] + names, ["z"] + names[::-1]]},
            "measure": [{"op": "Z", "sites": "all"}]}
    return card, names


def part_c(out):
    import schwinger as S
    m1 = next(p for p in S.PARAMS if p[0] == "M1")
    print(f"== C Schwinger N 6, M1, dt {S.DT} (schwinger.z_sites of schwinger.trotter's circuit)")
    worst = 0.0
    for steps in (1, 2):
        card, names = schwinger_card(6, steps, m1, S.DT)
        if steps == 2:
            dump(card, out, "schwinger_N6_M1.json")
        rep = C.check(card)
        e = C.exact(card)
        z = S.z_sites(S.trotter(6, steps, m1), 6, steps)
        ref = {f"Z_{k}": z[k] for k in range(6)}
        d = maxdiff(e, ref)
        worst = max(worst, d)
        one = dict(card, time=dict(dt=S.DT, steps=steps, order=card["time"]["orders"][0]))
        d1 = maxdiff(C.exact(one), ref)
        print(f"steps {steps}: {rep['terms']} terms, groups {rep['groups']}; max |card - schwinger| {d:.1e}  "
              f"{verdict(d)}; with one order for every step {d1:.1e}")
    return worst


def main():
    toqb, out = sys.argv[1], sys.argv[2]
    os.makedirs(out)
    wa = part_a(out)
    wb = part_b(toqb, out)
    wc = part_c(out)
    print(f"== ACCEPTANCE: A {verdict(wa)} (worst {wa:.1e}), B {verdict(wb)} (worst {wb:.1e}), C {verdict(wc)} "
          f"(worst {wc:.1e}); tolerance {TOL:g}")


if __name__ == "__main__":
    main()
