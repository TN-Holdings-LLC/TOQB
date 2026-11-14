"""Exploratory, after the verdicts (not declared): is r lower at N = 81 because of size, or because of the qubits?
r = sum z e / sum e^2 on subsets of qubits: the qubits the N = 33 and N = 81 chains share, in each circuit, and the
N = 81 chain's other qubits. usage: python notes/xxsize_2026-11-14/split.py   (from the repository root)"""
import json

import numpy as np

STEPS = (2, 4, 8, 12, 16)


def r(z, e):
    return float(np.dot(z, e) / np.dot(e, e))


for d in ("ibm_marrakesh", "ibm_fez"):
    base = f"results/xxsize-2026-11-14-{d[4:]}"
    lab = {n: json.load(open(f"{base}/{d}_n{n}/build.json"))["chains"][str(n)]["labels"] for n in (33, 81)}
    sc = {n: json.load(open(f"{base}/{d}_n{n}/scores.json"))["circuits"] for n in (33, 81)}
    shared = [q for q in lab[33] if q in set(lab[81])]
    rest = [q for q in lab[81] if q not in set(lab[33])]
    print(f"\n{d}: {len(shared)} shared qubits; N = 81 has {len(rest)} others")
    print("theta steps layers | N33 all | N33 on shared | N81 on shared | N81 on others | N81 all")
    for th in ("0785", "1571"):
        for s in STEPS:
            row = []
            for n, qs in ((33, lab[33]), (33, shared), (81, shared), (81, rest), (81, lab[81])):
                c = sc[n][f"N{n}_th{th}_s{s:02d}"]
                idx = [lab[n].index(q) for q in qs]
                row.append(r(np.array(c["z"])[idx], np.array(c["exact"])[idx]))
            print(f"{'pi/4' if th == '0785' else 'pi/2'} {s:2d} {4 * s:2d} | " + " | ".join(f"{x:.3f}" for x in row))
