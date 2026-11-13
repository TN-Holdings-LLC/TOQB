"""Cost probe: one site's <Z> of a honeycomb strip by psf-os's light-cone tensor network (exact_tn), to see whether
the exact answers past the MPS's reach are computable (workplace, 2026-11-13; desk only). Prints cone, largest
intermediate, seconds; the value only as a check against the MPS where both exist (2x15, t 3)."""
import json
import signal
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


dev = sys.argv[1]
Ed, bad = H.device_edges(dev)
for s in sys.argv[2:]:
    st, t = s.split("@")
    R, c = map(int, st.split("x"))
    phys, bonds = H.strip(Ed, R, c, bad)
    N = len(phys)
    layers = H.colour(bonds)
    bits = H.OA.strings(N, 1, 0.5, 20261112)[0][1]
    qc = circuit(N, layers, int(t), bits)
    site = N // 2                              # the first site right of the wall
    signal.signal(signal.SIGALRM, H._alarm)
    signal.alarm(300)
    t0 = time.time()
    try:
        v, r = E.expectation(qc, {site: "Z"}, max_size=2 ** 26, search_time=20.0)
        print(f"{s}: N {N}, site {site}: cone {r['cone_qubits']} qubits, largest intermediate 2^{r['log2_max_intermediate']}, "
              f"cost 10^{r['log10_cost']}, search {r['search_s']} s, contract {r['contract_s']} s, total "
              f"{time.time() - t0:.0f} s; value {v:+.6f}", flush=True)
    except E.TooLarge as err:
        print(f"{s}: N {N}: refused by the guard: {err.reason} ({time.time() - t0:.0f} s)", flush=True)
    except (H.Over, SystemError):
        print(f"{s}: N {N}: over 300 s, stopped", flush=True)
    finally:
        signal.alarm(0)
