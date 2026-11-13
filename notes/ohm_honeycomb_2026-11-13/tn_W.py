"""W of a honeycomb strip by the light-cone tensor network (psf-os exact_tn): every right-half <Z> of every string and
its complement, for the strips and cycles past the MPS's 1-minute reach (workplace, 2026-11-13; desk only). Writes one
JSON line per (strip, cycles) with W, W_mixed (every Z 0, as home), the ratio, the largest intermediate and the time.
usage: python tn_W.py DEVICE_JSON OUT.jsonl STRIP@T [STRIP@T ...] [--K 2]"""
import json
import sys
import time

import numpy as np

sys.path.insert(0, ".")
import hc_estimate as H  # noqa: E402
from psf_os import exact_tn as E  # noqa: E402



def circuit(N, layers, cycles, bits):
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import UnitaryGate
    G = UnitaryGate(H.OA.fsim(H.THETA, H.PHI))
    qc = QuantumCircuit(N)
    for k, b in enumerate(bits):
        if b:
            qc.x(k)
    for _ in range(cycles):
        for lay in layers:
            for a, b in lay:
                qc.append(G, [a, b])
    return qc


args = [a for a in sys.argv[1:] if not a.startswith("--")]
K = int(sys.argv[sys.argv.index("--K") + 1]) if "--K" in sys.argv else 2
dev, out = args[0], args[1]
Ed, bad = H.device_edges(dev)
for s in args[2:]:
    st, t = s.split("@")
    R, c = map(int, st.split("x"))
    phys, bonds = H.strip(Ed, R, c, bad)
    N = len(phys)
    layers = H.colour(bonds)
    strs = H.OA.strings(N, K, 0.5, 20261112)
    t0 = time.time()
    Ms, big = {}, 0.0
    for name, bits in strs:
        qc = circuit(N, layers, int(t), bits)
        vals, reps = E.z_sites(qc, range(N // 2, N), info=True, max_size=2 ** 26, search_time=10.0)
        big = max(big, max(r.get("log2_max_intermediate", 0) for r in reps))
        Ms[name] = float(sum((1 - v) / 2 for v in vals) - sum(bits[N // 2:]))
        print(f"  {s} {name}: M {Ms[name]:+.3f} ({time.time() - t0:.0f} s)", flush=True)
    ks = sorted({n[1:] for n in Ms})
    W = float(np.mean([(Ms["s" + k] - Ms["c" + k]) / 2 for k in ks]))
    m0 = {n: sum(b[N // 2:]) for n, b in strs}
    Wm = float(np.mean([(m0["c" + k] - m0["s" + k]) / 2 for k in ks]))
    row = dict(strip=st, cycles=int(t), N=N, K=K, W=W, W_mixed=Wm, ratio=W / Wm, log2_max_intermediate=big,
               seconds=round(time.time() - t0, 1))
    print(json.dumps(row), flush=True)
    with open(out, "a") as f:
        f.write(json.dumps(row) + "\n")
