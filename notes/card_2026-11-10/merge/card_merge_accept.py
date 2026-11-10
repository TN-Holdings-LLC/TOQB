"""Acceptance of psf_os.card's merge option (2026-11-10): for the acceptance cards of card_accept.py (kicked Ising,
Heisenberg textbook and heisE's own orders on the kingston 11-08 record, Schwinger N 6 M1), the merged circuit's exact
answers equal the term-by-term circuit's and the existing module's (1e-10); CZ per step and per Heisenberg bond.
Prints differences and counts only.

usage: PYTHONPATH=<psf-os>:<TOQB>/gpu:<this folder> python card_merge_accept.py TOQB
"""
import json
import os
import sys

import card_accept as A
from psf_os import card as C

TOL = 1e-10


def cz(card, merge):
    return C.circuit(card, merge=merge).count_ops().get("cz", 0)


def compare(tag, card, ref):
    e0, e1 = C.exact(card), C.exact(card, merge=True)
    d01, d1r = A.maxdiff(e1, e0), A.maxdiff(e1, ref)
    return d01, d1r


def main():
    toqb = sys.argv[1]
    worst = 0.0
    print("== A kicked Ising 4x2x2, theta 0.6 (one ZZ per pair: nothing to merge)")
    from psf_os import grid3d as G
    for t in (1, 2, 3, 4):
        card = A.ising_card(t)
        d01, d1r = compare(f"A t{t}", card, {f"Z_{q}": v for q, v in G.exact(4, 2, 2, t, 0.6).items()})
        worst = max(worst, d01, d1r)
        print(f"t {t}: merged - plain {d01:.1e}, merged - grid3d {d1r:.1e}; CZ plain {cz(card, False)}, merged "
              f"{cz(card, True)}")
    import heis3d as H
    from psf_os import device as Dv
    dt, delta = 0.05, 1.0
    print("== B1 Heisenberg 4x2x2 textbook order")
    for t in (1, 2, 3, 4):
        card, groups, order = A.heis_textbook_card(t, dt, delta)
        log = [bd for _ in range(t) for g in order for bd in groups[g]]
        d01, d1r = compare(f"B1 t{t}", card, {f"Z_{k}": v for k, v in H.exact_from_log(4, 2, 2, log, dt, delta).items()})
        worst = max(worst, d01, d1r)
        c0, c1 = cz(card, False), cz(card, True)
        print(f"t {t}: merged - plain {d01:.1e}, merged - heis3d {d1r:.1e}; CZ plain {c0} ({c0 / len(log):.0f} per "
              f"bond), merged {c1} ({c1 / len(log):.2f} per bond)")
    rec = os.path.join(toqb, "results", "os3d-heisE-kingston-2026-11-08")
    dev = Dv.Device.load(os.path.join(rec, "fetch_in", "ibm_kingston", "dev"))
    table = json.load(open(os.path.join(rec, "answers", "heis_answers_Ek.json")))
    print("== B2 heisE orders on the kingston 11-08 record (merged against heis3d.exact_from_log and the released table)")
    from psf_os import grid3d as GG
    cands, avoid = [], []
    while len(cands) < 4:
        try:
            _, _, _, _, where = H.physical(dev, 2, 2, 1, dt, delta, avoid=avoid, carry=False)
        except GG.Refused:
            break
        cands.append(dict(index=len(cands), r0=where["r0"], c0=where["c0"], avoid=list(avoid)))
        avoid.append((where["r0"], where["c0"]))
    for c in cands:
        for head, carry, vname in (("h3d", False, "old"), ("h3c", True, "carry"), ("h3l", "line", "line")):
            for t in (1, 2, 3, 4):
                if carry == "line":
                    _, _, _, log, _ = H.physical_line(dev, t, dt, delta, avoid=c["avoid"])
                else:
                    _, _, _, log, _ = H.physical(dev, 2, 2, t, dt, delta, avoid=c["avoid"], carry=carry)
                tag = f"{head}{c['index']}_t{t}"
                card, _ = A.heis_log_card(log, t, dt, delta)
                e1 = C.exact(card, merge=True)
                ref = {f"Z_{k}": v for k, v in H.exact_from_log(4, 2, 2, log, dt, delta).items()}
                tab = {f"Z_{k}": v for k, v in table[tag].items()}
                d1, d2 = A.maxdiff(e1, ref), A.maxdiff(e1, tab)
                worst = max(worst, d1, d2)
                c1 = cz(card, True)
                print(f"{tag} ({vname}): merged - heis3d {d1:.1e}, merged - table {d2:.1e}; CZ merged {c1} "
                      f"({c1 / len(log):.2f} per bond)")
    import schwinger as S
    m1 = next(p for p in S.PARAMS if p[0] == "M1")
    print("== C Schwinger N 6, M1")
    for steps in (1, 2):
        card, _ = A.schwinger_card(6, steps, m1, S.DT)
        z = S.z_sites(S.trotter(6, steps, m1), 6, steps)
        d01, d1r = compare(f"C {steps}", card, {f"Z_{k}": z[k] for k in range(6)})
        worst = max(worst, d01, d1r)
        print(f"steps {steps}: merged - plain {d01:.1e}, merged - schwinger {d1r:.1e}; CZ plain {cz(card, False)}, "
              f"merged {cz(card, True)} (schwinger.py: {S.trotter(6, steps, m1).count_ops().get('cx')} CX with routing)")
    print("== example cards (examples/cards): merged - plain")
    ex = os.path.join(os.path.dirname(C.__file__), "..", "examples", "cards")
    for f in sorted(os.listdir(ex)):
        if f.startswith("refused"):
            continue
        card = C.load(os.path.join(ex, f))
        d = A.maxdiff(C.exact(card, merge=True), C.exact(card))
        worst = max(worst, d)
        print(f"{f}: merged - plain {d:.1e}; CZ plain {cz(card, False)}, merged {cz(card, True)}")
    print(f"== MERGE ACCEPTANCE: worst {worst:.1e} ({'MATCH' if worst <= TOL else 'DIFFERS'}, tolerance {TOL:g})")


if __name__ == "__main__":
    main()
