"""Three mirrors (prototype; workplace, 2026-11-09; owner's idea "三面鏡"; simulator only, not declared, no device).

Front mirror: the compiled circuit U and its inverse (as today's mirror). U is compiled once as psf-os compiles a
user circuit (rzz_exact, RuleCompiler) and then split: left mirror = the instructions that touch no bridge qubit (x-
and z-bonds, swaps, the RX layers) and their inverse; right mirror = the instructions that touch a bridge (the
y-bonds, CX . RZZ . CX through a bridge) and their inverse; each mirrored without optimisation
(grid3d.mirror_of_compiled), so CZ(F) = CZ(L) + CZ(Rt); ideal reading +1 on every site. A readout-only circuit R (measure the sites) is the
fourth. If the errors of the two parts act independently, the mean readings should satisfy F * R ~ L * Rt
(each reading carries one readout factor). delta = F - L * Rt / R measures how much the parts act on each other.

Criteria fixed before any run (2026-11-09 01:39 CET):
  C1. Gate-local noise only (depolarizing on cz / sx / x): |delta| <= 2 SE (the product rule holds by itself).
  C2. With an always-on ZZ between coupled qubits (a fixed assumption, zeta rad per CZ layer, noise-free, not read from
      any device): delta < 0 beyond 2 SE at zeta = 0.02.
  C3. On a device, delta at zeta = 0.02 resolved at 2 SE with at most 1.5 x the device time of today's arm (user,
      floor, mirror: 3 circuits x 4000 shots), by the shot-noise estimate below.
Not a correction and not a model fit: the readings are reported, never used to change an answer or a noise model.

usage: PYTHONPATH=<psf-os> python three_mirrors.py DEVICE_RECORD OUT.json [--layout line] [--ts 1,2] [--traj 300]
"""
import argparse
import json
import time

import numpy as np


def compiled(dev, rc, qc, phys):
    """The placed circuit compiled as psf-os compiles a user circuit (rzz_exact, RuleCompiler), with the measurements."""
    from qiskit import QuantumCircuit
    from psf_os import user2d as U
    from psf_os.compile import rzz_exact
    full = QuantumCircuit(dev.num_qubits)
    full.compose(qc, qubits=list(range(qc.num_qubits)), inplace=True)
    return rc.pm.run(U.with_measure(rzz_exact(full), phys))


def parts(cu, bridges):
    """(row part, bridge part) of the COMPILED circuit, measurements dropped: an instruction goes to the bridge part if
    it touches a bridge qubit. Splitting after compiling keeps every physical gate of the front mirror in exactly one
    side mirror (CZ of F = CZ of L + CZ of Rt); splitting before compiling let the compiler merge gates of the bridge
    part that the row gates keep apart in U (seen in the first probe: 24 CZ instead of 48)."""
    rows, br = cu.copy_empty_like(), cu.copy_empty_like()
    for ins in cu.data:
        if ins.operation.name in ("measure", "barrier"):
            continue
        qs = {cu.find_bit(q).index for q in ins.qubits}
        (br if qs & bridges else rows).append(ins.operation, ins.qubits, ins.clbits)
    return rows, br


def mirror(rc, part, phys):
    """part, barrier, part^dagger, Z readout of phys, translated to the basis without optimisation."""
    from psf_os import grid3d as G
    return G.mirror_of_compiled(rc, part, phys)


def readout_only(dev, phys):
    from qiskit import QuantumCircuit
    c = QuantumCircuit(dev.num_qubits, len(phys))
    for k, p in enumerate(phys):
        c.measure(p, k)
    return c


def compact(c, couplers, zeta):
    """Touched qubits only; measurements removed (site k -> qubit); with zeta > 0 an RZZ(zeta) unitary (noise-free) on
    every coupler among the touched qubits after each layer that holds a two-qubit gate."""
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import RZZGate, UnitaryGate
    from qiskit.converters import circuit_to_dag, dag_to_circuit
    touched = sorted({c.find_bit(q).index for ins in c.data if ins.operation.name != "barrier" for q in ins.qubits})
    m = {q: i for i, q in enumerate(touched)}
    site = {}
    body = QuantumCircuit(len(touched))
    for ins in c.data:
        if ins.operation.name == "barrier":
            continue
        qs = [m[c.find_bit(q).index] for q in ins.qubits]
        if ins.operation.name == "measure":
            site[c.find_bit(ins.clbits[0]).index] = qs[0]
        else:
            body.append(ins.operation, qs)
    if zeta <= 0:
        return body, site
    pairs = [(m[a], m[b]) for a, b in couplers if a in m and b in m]
    zz = UnitaryGate(RZZGate(zeta).to_matrix(), label="zz")
    out = QuantumCircuit(len(touched))
    for layer in circuit_to_dag(body).layers():
        sub = dag_to_circuit(layer["graph"])
        out.compose(sub, inplace=True)
        if any(len(i.qubits) == 2 for i in sub.data):
            for a, b in pairs:
                out.append(zz, [a, b])
    return out, site


def reading(c, couplers, zeta, nm, traj, seed):
    """Mean over sites of <Z>, per trajectory: (mean, standard error over trajectories, number of qubits)."""
    from qiskit.quantum_info import SparsePauliOp
    from qiskit_aer import AerSimulator
    body, site = compact(c, couplers, zeta)
    n = body.num_qubits
    op = SparsePauliOp.from_sparse_list([("Z", [site[k]], 1.0 / len(site)) for k in site], num_qubits=n)
    body.save_expectation_value(op, list(range(n)), label="m", pershot=True)
    vals = np.real(np.array(AerSimulator(noise_model=nm, method="statevector", seed_simulator=seed)
                            .run(body, shots=traj).result().data()["m"]))
    return float(vals.mean()), float(vals.std(ddof=1) / np.sqrt(len(vals))), n


def noise(p2=0.005, p1=0.0002, pr=0.015):
    from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error
    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(depolarizing_error(p2, 2), ["cz"])
    nm.add_all_qubit_quantum_error(depolarizing_error(p1, 1), ["sx", "x"])
    return nm, pr  # readout as a factor (1 - 2 pr) on every reading, applied below


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("device")
    ap.add_argument("out")
    ap.add_argument("--layout", default="line")
    ap.add_argument("--L", type=int, default=4)
    ap.add_argument("--M", type=int, default=2)
    ap.add_argument("--N", type=int, default=2)
    ap.add_argument("--theta", type=float, default=0.6)
    ap.add_argument("--ts", default="1,2")
    ap.add_argument("--zetas", default="0,0.005,0.02")
    ap.add_argument("--traj", type=int, default=300)
    a = ap.parse_args()
    from psf_os import device as Dv
    from psf_os import grid3d as G
    from psf_os.compile import RuleCompiler
    from psf_os import mirror2d as Mi
    dev = Dv.Device.load(a.device)
    rc = RuleCompiler(dev)
    nm, pr = noise()
    ro = 1 - 2 * pr
    rows = []
    for t in (int(v) for v in a.ts.split(",")):
        qc, placed, used, _, where = G.physical(dev, a.L, a.M, a.N, t, a.theta, layout=a.layout, info=True)
        phys = [placed[s] for s in range(a.L * a.M * a.N)]
        bridges = sorted(set(used) - set(phys))
        cu = compiled(dev, rc, qc, phys)
        rp, bp = parts(cu, set(bridges))
        circs = dict(F=mirror(rc, cu, phys), L=mirror(rc, rp, phys), Rt=mirror(rc, bp, phys), R=readout_only(dev, phys))
        cz = {k: Mi.cz_count(v) for k, v in circs.items()}
        for zeta in (float(v) for v in a.zetas.split(",")):
            t0 = time.time()
            r = {}
            for k, c in circs.items():
                mean, se, nq = reading(c, dev.couplers, zeta, nm, a.traj, seed=11)
                r[k] = (mean * ro, se * ro)
            F, L, Rt, R = (r[k][0] for k in ("F", "L", "Rt", "R"))
            sF, sL, sRt, sR = (r[k][1] for k in ("F", "L", "Rt", "R"))
            delta = F - L * Rt / R
            se = float(np.sqrt(sF ** 2 + (Rt / R * sL) ** 2 + (L / R * sRt) ** 2 + (L * Rt / R ** 2 * sR) ** 2))
            row = dict(layout=where["layout"], r0=where["r0"], c0=where["c0"], t=t, zeta=zeta, traj=a.traj, cz=cz,
                       bridges=bridges, F=F, L=L, Rt=Rt, R=R, se=dict(F=sF, L=sL, Rt=sRt, R=sR), delta=delta,
                       delta_se=se, seconds=round(time.time() - t0, 1))
            rows.append(row)
            print(f"{where['layout']} t{t} zeta {zeta:<6} CZ F {cz['F']} L {cz['L']} Rt {cz['Rt']}  F {F:.4f} L {L:.4f} "
                  f"Rt {Rt:.4f} R {R:.4f}  delta {delta:+.4f} +- {se:.4f} ({delta / se:+.1f} SE)  {row['seconds']} s",
                  flush=True)
    json.dump(rows, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
