"""1b. Bridge traffic: CZ on every coupler that touches a bridge qubit (labels 16-19, 36-39 on Heron r2), fold vs
line, place 0 and 1, t 4; and the 2026-11-06 fez calibration record (the only error record at hand; not the 11-10
day) for those bridge qubits and couplers: T1, T2, readout error, CZ error."""
import json, sys
from collections import Counter
from qiskit import qpy
R, props_f = sys.argv[1], sys.argv[2]
bridges = set(range(16, 20)) | set(range(36, 40))
pd = json.load(open(props_f))
def qv(q, n):
    return next((x["value"] for x in pd["qubits"][q] if x["name"] == n), None)
cze = {tuple(sorted(g["qubits"])): next((p["value"] for p in g["parameters"] if p["name"] == "gate_error"), None)
       for g in pd["gates"] if g["gate"] == "cz"}
for c in (0, 1):
    for lay in ("f", "l"):
        (circ,) = qpy.load(open(f"{R}/ibm_fez/runs/p2d_q32{lay}{c}_t4.qpy", "rb"))
        cz = Counter(tuple(sorted(circ.find_bit(q).index for q in i.qubits)) for i in circ.data if i.operation.name == "cz")
        bt = Counter()
        for (a, b), n in cz.items():
            for x in (a, b):
                if x in bridges:
                    bt[x] += n
        print(f"place {c} {'fold' if lay == 'f' else 'line'} t4: CZ per bridge qubit " +
              ", ".join(f"q{b}: {n}" for b, n in sorted(bt.items())) +
              " | bridge couplers " + ", ".join(f"{k}:{n}" for k, n in sorted(cz.items()) if set(k) & bridges))
print("fez record 2026-11-06 (not the run day):")
for b in sorted(bridges):
    if b < 40:
        print(f"  q{b}: T1 {qv(b, 'T1')}, T2 {qv(b, 'T2')}, readout {qv(b, 'readout_error')}")
for k in sorted(cze):
    if set(k) & {16, 17, 36, 37} :
        print(f"  cz {k}: error {cze[k]}")
