"""Two mirrors (2026-11-08): expsim2.py plus --twirl (a random Pauli frame around every CZ, one frame per chunk,
P_after = CZ P_before CZ^dagger so the ideal circuit is unchanged; the stated coherent error RZZ(EPS) sits right after
the CZ, inside the frame; frame gates are noiseless, as if merged into neighbouring single-qubit gates) and --sx-dx
DELTA (a stated coherent over-rotation RX(DELTA) after every sx). Stage 1 (schedule, relaxation, noise model) is built
once per circuit and process; the frame is applied per chunk.

E probes (2026-11-08): expsim.py with two stated, unfitted probe switches, --t2-scale S (every T2 times S,
capped at 2 T1, before the model is built) and --cz-zz EPS (an extra coherent RZZ(EPS) after every CZ, no noise on it).
They test which mechanism the Heisenberg/Ising gap is sensitive to; they are not a calibration.

Trajectory-expectation simulator, prototype (2026-11-08, VS Claude; concept and seed: home Claude's realsim --expect).

Goal: estimate quickly, without a device, how much of the answer a device keeps. Not declared, not a device result.

Noise (nothing fitted, numbers as the model gives them):
  - FakeFez's noise model (gate errors with thermal relaxation), or a saved BackendProperties calibration (--props),
    built exactly as realsim.py builds it: ALAP schedule with FakeFez's gate durations, idle gaps padded with delays,
    RelaxationNoisePass adds T1/T2 decay on the delays; then restricted to the qubits the circuit touches.
  - readout asymmetry applied afterwards in closed form: <Z>_read = (1 - p10 - p01) <Z> + (p01 - p10).

Instead of sampling shots, each noise trajectory gives the exact <Z> of every measured qubit (Aer
save_expectation_value with pershot=True, so every trajectory is kept and the spread is a number, not a guess).
Speed: the trajectories of one circuit are split into chunks spread over worker processes, each chunk with its own
seed, so one circuit uses many cores. The noise model of the device is built once per process.

usage: python expsim.py INPUT.qpy NAMES.json OUT.json [--traj 160] [--chunk 20] [--workers N] [--props P.json]
Writes OUT.json: per circuit the readout-corrected <Z> of every trajectory (list of lists, clbit order), the compute
seconds per trajectory, and the preparation seconds.
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
_BASE = {}      # per process: props file -> (target, t1s, t2s, base noise model)
_PREP = {}      # per process: (circuit index, props) -> (sim, circuit, meas, readout)


def _base(props_file, t2s_scale=1.0):
    if (props_file, t2s_scale) in _BASE:
        return _BASE[(props_file, t2s_scale)]
    from qiskit_aer.noise import NoiseModel
    from qiskit_ibm_runtime.fake_provider import FakeFez
    be = FakeFez()
    tgt = be.target
    if props_file:
        # as realsim.py: gate errors, readout, T1/T2 from the calibration; durations stay FakeFez's. Aer needs a
        # frequency and T1/T2 on every qubit: filled in memory only (T2 = T1; the median when T1 is missing too).
        from qiskit_ibm_runtime.models import BackendProperties
        pd = json.load(open(props_file))

        def val(ql, n):
            return next((x["value"] for x in ql if x["name"] == n), None)
        med = {n: float(np.median([v for v in (val(ql, n) for ql in pd["qubits"]) if v is not None])) for n in ("T1", "T2")}
        unit = {n: next(x["unit"] for ql in pd["qubits"] for x in ql if x["name"] == n) for n in ("T1", "T2")}
        for ql in pd["qubits"]:
            if val(ql, "frequency") is None:
                ql.append(dict(name="frequency", value=5.0, unit="GHz", date=pd["last_update_date"]))
            if val(ql, "T1") is None:
                ql.append(dict(name="T1", value=med["T1"], unit=unit["T1"], date=pd["last_update_date"]))
            if val(ql, "T2") is None:
                ql.append(dict(name="T2", value=val(ql, "T1"), unit=unit["T1"], date=pd["last_update_date"]))
            if t2s_scale != 1.0:
                for x in ql:
                    if x["name"] == "T2":
                        x["value"] = min(x["value"] * t2s_scale, 2 * val(ql, "T1"))
        bp = BackendProperties.from_dict(pd)
        t1s = [bp.t1(q) for q in range(len(bp.qubits))]
        t2s = [min(bp.t2(q), 2 * bp.t1(q)) for q in range(len(bp.qubits))]
        base = NoiseModel.from_backend_properties(bp, dt=tgt.dt)
    else:
        props = [tgt.qubit_properties[q] for q in range(tgt.num_qubits)]
        t1s = [p.t1 for p in props]
        t2s = [min(p.t2, 2 * p.t1) for p in props]
        base = NoiseModel.from_backend(be)
    _BASE[(props_file, t2s_scale)] = (tgt, t1s, t2s, base)
    return _BASE[(props_file, t2s_scale)]


_STAGE1 = {}


def _stage1(k, qpy_bytes, props_file, t2s_scale=1.0):
    key = (k, props_file, t2s_scale)
    if key in _STAGE1:
        return _STAGE1[key]
    import io
    from qiskit import qpy
    from qiskit.circuit import Delay
    from qiskit.transpiler import PassManager
    from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDelay
    from qiskit_aer.noise import RelaxationNoisePass
    sys.path.insert(0, HERE)
    import sim3d as S
    tgt, t1s, t2s, base = _base(props_file, t2s_scale)
    c = qpy.load(io.BytesIO(qpy_bytes))[0]
    sched = PassManager([ALAPScheduleAnalysis(target=tgt), PadDelay(target=tgt)]).run(c)
    noisy = RelaxationNoisePass(t1s, t2s, dt=tgt.dt, op_types=[Delay])(sched)
    touched = sorted({c.find_bit(q).index for ins in c.data if ins.operation.name not in ("barrier", "delay")
                      for q in ins.qubits})
    m = {q: i for i, q in enumerate(touched)}
    body, meas = [], {}
    for ins in noisy.data:
        if ins.operation.name == "barrier" or any(noisy.find_bit(q).index not in m for q in ins.qubits):
            continue
        qs = [m[noisy.find_bit(q).index] for q in ins.qubits]
        if ins.operation.name == "measure":
            meas[noisy.find_bit(ins.clbits[0]).index] = qs[0]
        else:
            body.append((ins.operation, qs))
    nm = S.remap_noise(base, touched)
    ro = S.readout_maps(base, touched)
    _STAGE1[key] = (body, meas, nm, ro, len(touched))
    return _STAGE1[key]


_ERR = {}


def _err_gate(kind, angle):
    """The stated coherent error as a noiseless UnitaryGate. The fez record lists rzz and rx as calibrated gates, so a
    plain rzz / rx would also get that gate's error from the noise model (found 2026-11-08: the first two-mirror run
    and the E probe 'czzz' carried one full rzz error per CZ). A UnitaryGate is not in the noise model."""
    from qiskit.circuit.library import UnitaryGate
    key = (kind, angle)
    if key not in _ERR:
        if kind == "zz":
            ph = np.exp(-1j * angle / 2)
            m = np.diag([ph, ph.conjugate(), ph.conjugate(), ph])
        else:
            c, s_ = np.cos(angle / 2), np.sin(angle / 2)
            m = np.array([[c, -1j * s_], [-1j * s_, c]])
        _ERR[key] = UnitaryGate(m, label="err_" + kind)
    return _ERR[key]


_PAULI = {}


def _pauli_gate(x, z):
    from qiskit.circuit.library import UnitaryGate
    if (x, z) not in _PAULI:
        mat = np.eye(2, dtype=complex)
        if x:
            mat = np.array([[0, 1], [1, 0]], complex) @ mat
        if z:
            mat = np.array([[1, 0], [0, -1]], complex) @ mat
        _PAULI[(x, z)] = UnitaryGate(mat, label="frame")      # noiseless: not a basis gate of the noise model
    return _PAULI[(x, z)]


def _prepare(k, qpy_bytes, props_file, t2s_scale=1.0, zz=0.0, twirl_seed=None, sxdx=0.0):
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Pauli
    from qiskit_aer import AerSimulator
    body, meas, nm, ro, nq = _stage1(k, qpy_bytes, props_file, t2s_scale)
    rng = np.random.default_rng(twirl_seed) if twirl_seed is not None else None
    ce = QuantumCircuit(nq)
    for op, qs in body:
        if op.name == "cz" and rng is not None:
            xa, za, xb, zb = (int(v) for v in rng.integers(0, 2, 4))
            if xa or za:
                ce.append(_pauli_gate(xa, za), [qs[0]])
            if xb or zb:
                ce.append(_pauli_gate(xb, zb), [qs[1]])
            ce.append(op, qs)
            if zz:
                ce.append(_err_gate("zz", zz), qs)
            # CZ (X_a) CZ^dag = X_a Z_b, CZ (X_b) CZ^dag = Z_a X_b; Z unchanged
            pa, pb = (xa, za ^ xb), (xb, zb ^ xa)
            if pa[0] or pa[1]:
                ce.append(_pauli_gate(*pa), [qs[0]])
            if pb[0] or pb[1]:
                ce.append(_pauli_gate(*pb), [qs[1]])
            continue
        ce.append(op, qs)
        if zz and op.name == "cz":
            ce.append(_err_gate("zz", zz), qs)
        if sxdx and op.name == "sx":
            ce.append(_err_gate("x", sxdx), [qs[0]])
    cls = sorted(meas)
    for cl in cls:
        ce.save_expectation_value(Pauli("Z"), [meas[cl]], label=f"z{cl}", pershot=True)
    sim = AerSimulator(method="statevector", noise_model=nm, max_parallel_threads=1)
    return sim, ce, cls, [ro.get(meas[cl], (0.0, 0.0)) for cl in cls], nq


def _chunk(args):
    k, qpy_bytes, seed, n, props_file, t2s_scale, zz, twirl, sxdx = args
    try:
        t0 = time.time()
        sim, ce, cls, ro, nq = _prepare(k, qpy_bytes, props_file, t2s_scale, zz, seed if twirl else None, sxdx)
        t1 = time.time()
        d = sim.run(ce, shots=n, seed_simulator=seed).result().data()
        t2 = time.time()
        z = np.array([np.real(np.asarray(d[f"z{cl}"], dtype=complex)) for cl in cls])     # (clbits, n)
        a = np.array([1 - p10 - p01 for p10, p01 in ro])[:, None]
        b = np.array([p01 - p10 for p10, p01 in ro])[:, None]
        return k, (a * z + b).T.tolist(), t1 - t0, t2 - t1, nq, ""
    except Exception as e:      # one failed chunk must not discard the others
        return k, None, 0.0, 0.0, -1, f"failed: {type(e).__name__}: {str(e)[:300]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("qpy")
    ap.add_argument("names")
    ap.add_argument("out")
    ap.add_argument("--traj", type=int, default=160)
    ap.add_argument("--chunk", type=int, default=20)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--props", default=None)
    ap.add_argument("--only", default=None, help="comma-separated names")
    ap.add_argument("--seed", type=int, default=0, help="seed offset (independent repeat runs)")
    ap.add_argument("--t2-scale", type=float, default=1.0)
    ap.add_argument("--cz-zz", type=float, default=0.0)
    ap.add_argument("--twirl", action="store_true")
    ap.add_argument("--sx-dx", type=float, default=0.0)
    a = ap.parse_args()
    import io
    from qiskit import qpy
    circs = qpy.load(open(a.qpy, "rb"))
    names = json.load(open(a.names))
    if a.only:
        keep = [i for i, n in enumerate(names) if n in a.only.split(",")]
        circs, names = [circs[i] for i in keep], [names[i] for i in keep]
    props = os.path.abspath(a.props) if a.props else None
    blobs = []
    for c in circs:
        b = io.BytesIO()
        qpy.dump(c, b)
        blobs.append(b.getvalue())
    tasks = []
    for k in range(len(circs)):
        for j in range(0, a.traj, a.chunk):
            tasks.append((k, blobs[k], 7919 * (k + 1) + j + 1000003 * a.seed, min(a.chunk, a.traj - j), props, a.t2_scale, a.cz_zz, a.twirl, a.sx_dx))
    tasks.sort(key=lambda t: -circs[t[0]].size())     # biggest circuits first: the pool ends evenly
    res = {k: dict(z=[], prep=[], comp=[], nq=None, notes=[]) for k in range(len(circs))}
    t0 = time.time()
    print(f"start {time.strftime('%F %T')}  circuits {len(circs)}  traj {a.traj}  chunk {a.chunk}  tasks {len(tasks)}"
          f"  workers {a.workers}  noise {os.path.basename(props) if props else 'FakeFez'}", flush=True)
    with ProcessPoolExecutor(a.workers) as ex:
        done = 0
        for k, z, tp, tc, nq, note in ex.map(_chunk, tasks):
            r = res[k]
            done += 1
            if z is None:
                r["notes"].append(note)
                print(f"FAILED chunk of {names[k]}: {note}", flush=True)
                continue
            r["z"] += z
            r.setdefault("chunks", []).append(len(z))
            r["prep"].append(tp)
            r["comp"].append(tc)
            r["nq"] = nq
            if len(r["z"]) == a.traj:
                print(f"{names[k]:22} qubits {nq}  traj {len(r['z'])}  {sum(r['comp']) / a.traj:.3f} s/traj"
                      f"  (+ prep {max(r['prep']):.1f} s)  at {time.time() - t0:.0f} s", flush=True)
    wall = time.time() - t0
    out = dict(twirl=a.twirl, sx_dx=a.sx_dx, t2_scale=a.t2_scale, cz_zz=a.cz_zz, noise=os.path.basename(props) if props else "FakeFez", traj=a.traj, chunk=a.chunk, workers=a.workers,
               wall_seconds=wall, circuits={})
    for k, r in res.items():
        out["circuits"][names[k]] = dict(nq=r["nq"], cz=circs[k].count_ops().get("cz", 0), z=r["z"],
                                         sec_per_traj=sum(r["comp"]) / max(len(r["z"]), 1),
                                         prep_seconds=max(r["prep"]) if r["prep"] else None, notes=r["notes"], chunks=r.get("chunks", []))
    json.dump(out, open(a.out, "w"))
    failed = sum(len(r["notes"]) for r in res.values())
    print(f"wall {wall:.1f} s")
    print("== EXPSIM FAILED" if failed else "== EXPSIM FINISHED")


if __name__ == "__main__":
    main()
