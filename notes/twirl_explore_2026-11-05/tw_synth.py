"""Synthetic-noise check of the exploratory correction (raw mirror vs twirled mirror) on small P6-form and P4-form
pieces. Noise strengths chosen here (not fitted to any device): CZ depolarizing p2, one-qubit p1, readout flip r,
and a coherent error attached to every CZ: rzz(eps) on the pair and rz(delta) on both (inside the CZ window)."""
import sys, json
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector, Pauli
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError
sys.path.insert(0, "gpu")
import twirl_explore as T
from psf_os import user2d as U, mirror2d as M

def p6_piece(t, tx=0.53, tz=0.1, tzz=1.0):
    n = 10
    edges = [(0,1),(1,2),(2,3),(3,4),(0,5),(4,6),(5,7),(6,9),(7,8),(8,9)]
    qc = QuantumCircuit(n)
    for _ in range(t):
        for q in range(n): qc.rx(tx, q); qc.rz(tz, q)
        for a, b in edges: qc.rzz(tzz, a, b)
    return qc
def p4_piece(t, n=9, h=0.15, b=np.pi/4-0.3):
    qc = QuantumCircuit(n); qc.h(0)
    for i in range(1, n-1, 2): qc.h(i); qc.cx(i, i+1)
    for k in range(t):
        for i in range(k % 2, n-1, 2):
            qc.rz(2*h, i); qc.rzz(np.pi/2, i, i+1); qc.rx(2*b, i); qc.rx(2*b, i+1); qc.rzz(np.pi/2, i, i+1); qc.rz(2*h, i)
    for q in range(n): qc.h(q)
    return qc

def comp(qc):
    from psf_os.compile import rzz_exact
    return transpile(rzz_exact(qc), basis_gates=["cz", "rz", "sx", "x"], optimization_level=1, seed_transpiler=0)

def inject(c, eps, delta):
    out = c.copy_empty_like()
    for ins in c.data:
        out.append(ins.operation, ins.qubits, ins.clbits)
        if ins.operation.name == "cz" and (eps or delta):
            a, b = ins.qubits
            if eps: out.rzz(eps, a, b)
            if delta: out.rz(delta, a); out.rz(delta, b)
    return out

def run(c, nm, n):
    c = c.copy(); c.remove_final_measurements()
    c.save_density_matrix()
    rho = AerSimulator(method="density_matrix", noise_model=nm).run(c).result().data()["density_matrix"]
    return np.array([float(np.real(rho.expectation_value(Pauli("I"*(n-1-j)+"Z"+"I"*j)))) for j in range(n)])

def scenario(name, logical, eps, delta, p2=0.004, p1=0.0005, r=0.02):
    n = logical.num_qubits
    ans = Statevector(logical).probabilities_dict()
    exact = np.array([sum(p*(1-2*int(k[n-1-j])) for k, p in ans.items()) for j in range(n)])
    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(depolarizing_error(p2, 2), ["cz"])
    nm.add_all_qubit_quantum_error(depolarizing_error(p1, 1), ["sx", "x"])
    cu = comp(logical); cm = comp(M.mirror(logical, list(range(n))).remove_final_measurements(inplace=False))
    fl = U.floor_of(cu); fl2 = U.floor_of(cm)
    def ev(cs):  # readout flip r applied analytically: <Z> -> (1-2r) <Z>
        return (1 - 2*r) * np.mean([run(inject(c, eps, delta), nm, n) for c in cs], 0)
    d = dict(labels=list(range(n)),
             raw=ev([cu]), tw=ev([T.twirl(cu, k) for k in range(T.K)]), floor=ev([fl]),
             mraw=ev([cm]), mtw=ev([T.twirl(cm, k) for k in range(T.K)]), floor2=ev([fl2]))
    res = T.correct(d, {str(j): exact[j] for j in range(n)})
    print(f"{name:34}", "  ".join(f"{k} {res[k]['diff']:+.3f}" for k in ("raw", "tw", "floor_only_tw", "corr_raw", "corr_tw")),
          f"| g raw {res['g_raw']:.3f} tw {res['g_tw']:.3f}")

for name, lg in (("P6 piece t3", p6_piece(3)), ("P6 piece t3 tx0.8", p6_piece(3, tx=0.8)), ("P4 piece N9 t6", p4_piece(6))):
    scenario(name + " dep only", lg, 0, 0)
    scenario(name + " +ZZ 0.05", lg, 0.05, 0)
    scenario(name + " +detune 0.05", lg, 0, 0.05)
    scenario(name + " +both", lg, 0.05, 0.05)
