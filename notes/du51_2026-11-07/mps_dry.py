"""Pre-run check of the N = 51 jobs (no device, no noise): run the compiled circuits of a built job noiselessly with
Aer's matrix-product-state method on the qubits each circuit uses, for the points up to depth TMAX (deeper ones and
their floors and mirrors, and the ring sentinel, get a placeholder count), and write JOB/raw_counts.json and JOB/submission.json so that
gpu/du51_score.py reads the dry run like a device run. Build the job with --dry-clifford-sentinel (Clifford ring).

usage: python mps_dry.py JOB_DIR [TMAX] [WORKERS]
"""
import json
import os
import re
import sys

from qiskit import QuantumCircuit, qpy
from qiskit_aer import AerSimulator


def _one(args):
    k, qpy_bytes, chain = args
    import io
    (c,) = qpy.load(io.BytesIO(qpy_bytes))
    used = sorted({c.find_bit(q).index for i in c.data if i.operation.name not in ("barrier", "delay")
                   for q in i.qubits})
    # MPS order = chain order (the placed chain from build.json): the clbits follow the sorted labels, which put
    # chain neighbours far apart (the snake turns back on every row) and blow up the bond dimension
    order = [q for q in chain if q in used] + [q for q in used if q not in chain]
    m = {q: i for i, q in enumerate(order)}
    cc = QuantumCircuit(len(order), c.num_clbits)
    for i in c.data:
        if i.operation.name in ("barrier", "delay"):
            continue
        cc.append(i.operation, [m[c.find_bit(q).index] for q in i.qubits], [c.find_bit(b).index for b in i.clbits])
    sim = AerSimulator(method="matrix_product_state", max_parallel_threads=1)
    return k, sim.run(cc, shots=4000, seed_simulator=7 + k).result().get_counts(), len(order)


def main(job, tmax=8, workers=8):
    import io
    from concurrent.futures import ProcessPoolExecutor
    man = json.load(open(os.path.join(job, "manifest.json")))
    chain = json.load(open(os.path.join(job, "..", "..", "build.json")))["chain"]
    circs = qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))
    names = [man["cells"][p["cell"]]["name"] for p in man["pubs"]]
    rows = {k: dict(pub=k, counts={"0" * c.num_clbits: 1}) for k, c in enumerate(circs)}
    tasks = []
    for k, (c, n) in enumerate(zip(circs, names)):
        mt = re.match(r"p2d_du\d+_h\d+_t(\d+)", n)     # any N (du51_, du71_): the first prefix test missed du71
        deep = mt is not None and int(mt.group(1)) > tmax
        if deep or n.startswith("ksent"):      # placeholder: deeper points and the ring sentinel are not checked
            continue
        b = io.BytesIO()
        qpy.dump(c, b)
        tasks.append((k, b.getvalue(), chain))
    with ProcessPoolExecutor(workers) as ex:
        for k, counts, nq in ex.map(_one, tasks):
            rows[k] = dict(pub=k, counts=counts)
            print(f"{k:3} {names[k]:30} qubits {nq}", flush=True)
    json.dump(dict(job_id="mps_dry", submitted="-", local=True, simulator="aer_mps_noiseless"),
              open(os.path.join(job, "submission.json"), "w"))
    json.dump(dict(fetched="-", job_id="mps_dry", status="DONE", rows=[rows[k] for k in range(len(circs))]),
              open(os.path.join(job, "raw_counts.json"), "w"))
    print("== MPS DRY FINISHED")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 8, int(sys.argv[3]) if len(sys.argv) > 3 else 8)
