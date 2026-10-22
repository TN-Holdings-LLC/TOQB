"""Post hoc diagnostic (2026-10-22): the calibration of the qubits and couplers each cell used, in the snapshot the
twin was built on (2026-10-13) against the one fetched after the job (12:21 CEST, in effect during the run).

    python -m toqb.device_map_posthoc JOB_DIR FETCH_DIR
"""
import json, pickle, numpy as np
from qiskit import qpy
from toqb.devices import get_device
import sys
J, F = sys.argv[1], sys.argv[2]
snap = get_device("snapshot:marrakesh").target
today = pickle.load(open(f"{F}/target.pkl", "rb"))
man = json.load(open(f"{J}/manifest.json"))
first = {}
for i, p in enumerate(man["pubs"]):
    first.setdefault(p["cell"], i)
circs = qpy.load(open(f"{J}/circuits.qpy", "rb"))
def err(t, name, q):
    try:
        e = t[name][q].error
        return e
    except KeyError:
        return None
def t1(t, q):
    qp = t.qubit_properties[q] if t.qubit_properties else None
    return (qp.t1 if qp and qp.t1 else None, qp.t2 if qp and qp.t2 else None)
for cid, c in enumerate(man["cells"]):
    qc = circs[first[cid]]
    qs = sorted({qc.find_bit(q).index for ins in qc.data for q in ins.qubits if ins.operation.name != "barrier"})
    pairs = sorted({tuple(qc.find_bit(q).index for q in ins.qubits) for ins in qc.data if len(ins.qubits) == 2})
    meas = {qc.find_bit(ins.clbits[0]).index: qc.find_bit(ins.qubits[0]).index for ins in qc.data if ins.operation.name == "measure"}
    def summ(t):
        ro = [err(t, "measure", (q,)) for q in qs]; sx = [err(t, "sx", (q,)) for q in qs]
        cz = [err(t, "cz", p) for p in pairs]
        t1s = [t1(t, q)[0] for q in qs]
        return (np.mean(ro), max(ro), np.mean(sx), max(sx), np.mean(cz), max(cz), np.median([x for x in t1s if x]) * 1e6)
    s, d = summ(snap), summ(today)
    print(f"{c['name']}: {len(qs)} qubits {qs}, {len(pairs)} couplers, readout qubit {meas[0]}")
    print(f"  readout err mean/max  snap {s[0]:.4f}/{s[1]:.4f}  today {d[0]:.4f}/{d[1]:.4f}")
    print(f"  sx err mean/max       snap {s[2]:.5f}/{s[3]:.5f}  today {d[2]:.5f}/{d[3]:.5f}")
    print(f"  cz err mean/max       snap {s[4]:.4f}/{s[5]:.4f}  today {d[4]:.4f}/{d[5]:.4f}")
    print(f"  T1 median (us)        snap {s[6]:.0f}  today {d[6]:.0f}")
    q0 = meas[0]
    print(f"  readout qubit {q0}: readout err snap {err(snap,'measure',(q0,)):.4f} today {err(today,'measure',(q0,)):.4f}; T1 snap {t1(snap,q0)[0]*1e6:.0f} today {t1(today,q0)[0]*1e6:.0f} us")
    worst = sorted(((err(today, 'cz', p), p, err(snap, 'cz', p)) for p in pairs), reverse=True)[:3]
    print("  worst cz today (today, pair, snap):", [(round(a, 4), p, round(b, 4)) for a, p, b in worst])
