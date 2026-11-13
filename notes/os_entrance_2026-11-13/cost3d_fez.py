"""Cost of the entrance's generic 3D path on the ibm_fez 11-12 record (workplace, 2026-11-13g; desk only): fSim(pi/4, pi/2) or
RZZ(0.3) on 4 x M x N lattices written in colour layers, through psf_os.entrance.check. usage: PYTHONPATH=<psf-os> python cost3d_fez.py"""
import numpy as np, json, os
from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate
from psf_os import device as Dv, entrance as E, grid3d as G
dev = Dv.Device.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'results', 'xx91-2026-11-12', 'fetch_in', 'ibm_fez', 'dev'))
def fsim(t, p):
    c, s = np.cos(t), np.sin(t)
    return np.array([[1,0,0,0],[0,c,-1j*s,0],[0,-1j*s,c,0],[0,0,0,np.exp(-1j*p)]])
F = UnitaryGate(fsim(np.pi/4, np.pi/2), label="fsim")
def colour_circuit(M, N, cycles, gate):
    sites = G.sites(4, M, N); idx = {s: i for i, s in enumerate(sites)}
    layers = []
    for ax in range(3):
        for par in (0, 1):
            lay = []
            for s in sites:
                if s[ax] % 2 == par:
                    t = list(s); t[ax] += 1
                    if tuple(t) in idx: lay.append((idx[s], idx[tuple(t)]))
            if lay: layers.append(lay)
    qc = QuantumCircuit(len(sites))
    for q in range(1, len(sites), 2): qc.x(q)
    for _ in range(cycles):
        for lay in layers:
            for a, b in lay:
                qc.append(F, [a, b]) if gate == "fsim" else qc.rzz(0.3, a, b)
    return qc, len(layers)
out = {}
for M, N in ((2, 2), (3, 2), (4, 3)):
    for gate in ("fsim", "rzz"):
        for cyc in (1, 2):
            qc, nl = colour_circuit(M, N, cyc, gate)
            r = E.check(dev, [("c", qc)], shots=4000)
            c = r["cost"]["items"]["c"]
            out[f"4x{M}x{N} {gate} {cyc}"] = dict(c, layout=r["groups"][0]["placement"].get("layout"),
                                                   r0=r["groups"][0]["placement"].get("r0"))
            print(f"4x{M}x{N} {gate} cycles {cyc}: CZ {c['cz']} layers {c['cz_layers']} logical 2q layers {c['logical_2q_layers']} "
                  f"inflation {c['inflation']:.1f} swaps {c['swaps']} moves {c['bridge_moves']} rounds {c['schedule_rounds']}", flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cost3d_fez.json'), 'w'), indent=1)
