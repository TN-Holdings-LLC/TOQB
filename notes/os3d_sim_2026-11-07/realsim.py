"""A device-like simulation of a built v3.1 job (2026-11-07; not declared, not a device result): FakeFez's noise model
(gate errors with thermal relaxation, readout asymmetry) plus relaxation while qubits wait (the circuits are scheduled
ALAP with FakeFez's gate durations, the idle gaps padded with delays and RelaxationNoisePass adds T1/T2 decay on them).
The 11-07 device run showed that waiting qubits relax: deep probes washed out, which the uniform model could not show.

Writes JOB/raw_counts.json and JOB/submission.json (local) so gpu/os3d_v31_score.py reads the run as a device run.

Circuits on more than --max-qubits qubits (the 40-qubit sentinel) do not fit a statevector: they are skipped and
written as a placeholder (marked in skipped.json), and a failure of one circuit no longer stops the others.
--device GPU uses Aer's GPU build (qiskit-aer-gpu), one worker per GPU.

usage: python realsim.py PSF_OS RUN_DIR [--shots 600] [--workers N] [--only NAME,...] [--max-qubits 30]
                         [--device CPU|GPU]
"""
import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def _one(args):
    k, qpy_bytes, shots, seed, max_q, device = args
    import io
    from qiskit import qpy
    from qiskit.transpiler import PassManager
    from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDelay
    from qiskit.circuit import Delay
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, RelaxationNoisePass
    from qiskit_ibm_runtime.fake_provider import FakeFez
    sys.path.insert(0, HERE)
    import sim3d as S
    c = qpy.load(io.BytesIO(qpy_bytes))[0]
    be = FakeFez()
    tgt = be.target
    sched = PassManager([ALAPScheduleAnalysis(target=tgt), PadDelay(target=tgt)]).run(c)
    props = [tgt.qubit_properties[q] for q in range(tgt.num_qubits)]
    t1s = [p.t1 for p in props]
    t2s = [min(p.t2, 2 * p.t1) for p in props]
    noisy = RelaxationNoisePass(t1s, t2s, dt=tgt.dt, op_types=[Delay])(sched)
    # qubits the circuit itself uses (before padding: PadDelay puts delays on every idle device qubit)
    touched = sorted({c.find_bit(q).index for ins in c.data if ins.operation.name not in ("barrier", "delay")
                      for q in ins.qubits})
    if len(touched) > max_q:
        return k, None, len(touched), "skipped: too many qubits for a statevector"
    m = {q: i for i, q in enumerate(touched)}
    from qiskit import QuantumCircuit
    cc = QuantumCircuit(len(touched), noisy.num_clbits)
    for ins in noisy.data:
        if ins.operation.name == "barrier" or any(noisy.find_bit(q).index not in m for q in ins.qubits):
            continue          # delays (and their relaxation) on qubits the circuit never uses
        cc.append(ins.operation, [m[noisy.find_bit(q).index] for q in ins.qubits],
                  [noisy.find_bit(b).index for b in ins.clbits])
    nm = S.remap_noise(NoiseModel.from_backend(be), touched)
    ro = S.readout_maps(NoiseModel.from_backend(be), touched)
    opts = dict(method="statevector", noise_model=nm, seed_simulator=seed)
    if device == "GPU":
        opts.update(device="GPU", batched_shots_gpu=True)
    sim = AerSimulator(**opts)
    counts = sim.run(cc, shots=shots).result().get_counts(0)
    # readout asymmetry, per measured qubit (classical flips with the backend's p(1|0), p(0|1))
    meas = {}
    for ins in cc.data:
        if ins.operation.name == "measure":
            meas[cc.find_bit(ins.clbits[0]).index] = cc.find_bit(ins.qubits[0]).index
    rng = np.random.default_rng(seed)
    out = {}
    for key, v in counts.items():
        bits = list(key.replace(" ", ""))
        n = len(bits)
        for _ in range(v):
            b = list(bits)
            for cl, q in meas.items():
                p10, p01 = ro.get(q, (0.0, 0.0))
                i = n - 1 - cl
                if b[i] == "0" and rng.random() < p10:
                    b[i] = "1"
                elif b[i] == "1" and rng.random() < p01:
                    b[i] = "0"
            kk = "".join(b)
            out[kk] = out.get(kk, 0) + 1
    return k, out, len(touched), ""


def _safe(args):
    try:
        return _one(args)
    except Exception as e:      # one failed circuit must not discard the others
        return args[0], None, -1, f"failed: {type(e).__name__}: {str(e)[:200]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("psf_os")
    ap.add_argument("run")
    ap.add_argument("--shots", type=int, default=600)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--only", default=None)
    ap.add_argument("--max-qubits", type=int, default=30)
    ap.add_argument("--device", default="CPU", choices=["CPU", "GPU"])
    a = ap.parse_args()
    sys.path.insert(0, a.psf_os)
    import io
    from qiskit import qpy
    job = os.path.join(a.run, "job")
    man = json.load(open(os.path.join(job, "manifest.json")))
    circs = qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))
    names = [man["cells"][p["cell"]]["name"] for p in man["pubs"]]
    only = set(a.only.split(",")) if a.only else None
    tasks = []
    for k, c in enumerate(circs):
        if only and names[k] not in only:
            continue
        b = io.BytesIO()
        qpy.dump(c, b)
        tasks.append((k, b.getvalue(), a.shots, 1000 + k, a.max_qubits, a.device))
    rows, skipped = {}, {}
    with ProcessPoolExecutor(a.workers) as ex:
        for k, counts, nq, note in ex.map(_safe, tasks):
            if counts is None:
                skipped[names[k]] = note
            else:
                rows[k] = dict(pub=k, counts=counts)
            print(f"{k:3} {names[k]:28} qubits {nq} {note}", flush=True)
    json.dump(skipped, open(os.path.join(job, "skipped.json"), "w"), indent=1)
    failed = [n for n, v in skipped.items() if v.startswith("failed")]
    if failed:
        print("FAILED circuits:", failed)
    full = [rows.get(k, dict(pub=k, counts={"0" * circs[k].num_clbits: 1})) for k in range(len(circs))]
    json.dump(dict(job_id="realsim", submitted="-", local=True, backend="fake_fez"),
              open(os.path.join(job, "submission.json"), "w"))
    json.dump(dict(fetched="-", job_id="realsim", status="DONE", rows=full), open(os.path.join(job, "raw_counts.json"), "w"))
    print("== REALSIM FINISHED")


if __name__ == "__main__":
    main()
