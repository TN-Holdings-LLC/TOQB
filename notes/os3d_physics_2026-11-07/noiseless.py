"""Pre-run check (no device, no noise): run every circuit of a built job on the qubits it uses with Aer's
statevector method, noiselessly, 4000 shots; circuits over --max-qubits (the 40-qubit ring sentinel) get a
placeholder count. Writes JOB/raw_counts.json and JOB/submission.json, so the scorer reads it like a device run:
every arm should READ, AGREE and BEAT with retention 1 within shot noise.

usage: python noiseless.py JOB_DIR [--max-qubits 30] [--workers 2]
"""
import argparse
import io
import json
import os
from concurrent.futures import ProcessPoolExecutor

from qiskit import QuantumCircuit, qpy
from qiskit_aer import AerSimulator


def _one(args):
    k, b, maxq = args
    (c,) = qpy.load(io.BytesIO(b))
    used = sorted({c.find_bit(q).index for i in c.data if i.operation.name not in ("barrier", "delay")
                   for q in i.qubits})
    if len(used) > maxq:
        return k, {"0" * c.num_clbits: 1}, len(used)
    m = {q: i for i, q in enumerate(used)}
    cc = QuantumCircuit(len(used), c.num_clbits)
    for i in c.data:
        if i.operation.name in ("barrier", "delay"):
            continue
        cc.append(i.operation, [m[c.find_bit(q).index] for q in i.qubits], [c.find_bit(x).index for x in i.clbits])
    sim = AerSimulator(method="statevector", max_parallel_threads=1)
    return k, sim.run(cc, shots=4000, seed_simulator=11 + k).result().get_counts(), len(used)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    ap.add_argument("--max-qubits", type=int, default=30)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    circs = qpy.load(open(os.path.join(a.job, "circuits.qpy"), "rb"))
    tasks = []
    for k, c in enumerate(circs):
        b = io.BytesIO()
        qpy.dump(c, b)
        tasks.append((k, b.getvalue(), a.max_qubits))
    rows = {}
    with ProcessPoolExecutor(a.workers) as ex:
        for k, counts, nq in ex.map(_one, tasks):
            rows[k] = dict(pub=k, counts=counts)
    json.dump(dict(job_id="noiseless", submitted="-", local=True, simulator="aer_statevector_noiseless"),
              open(os.path.join(a.job, "submission.json"), "w"))
    json.dump(dict(fetched="-", job_id="noiseless", status="DONE", rows=[rows[k] for k in range(len(circs))]),
              open(os.path.join(a.job, "raw_counts.json"), "w"))
    print(f"== NOISELESS FINISHED ({len(circs)} circuits)")


if __name__ == "__main__":
    main()
