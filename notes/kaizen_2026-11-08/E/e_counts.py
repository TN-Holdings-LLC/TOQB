"""E: what differs between the Heisenberg and Ising device circuits (the fez jobs compared in simproto):
gate counts, ALAP schedule length with FakeFez durations, idle time on touched qubits, share of time a touched qubit
is idle, and how many CZ act while a qubit is in superposition is not computed here (a later step)."""
import json, sys
from qiskit import qpy
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDelay
from qiskit_ibm_runtime.fake_provider import FakeFez

P = sys.argv[1]
tgt = FakeFez().target
dt = tgt.dt
for key in ("heisB", "isingA"):
    circs = qpy.load(open(f"{P}/{key}.qpy", "rb")); names = json.load(open(f"{P}/{key}_names.json"))
    for name, c in zip(names, circs):
        if key == "isingA" and "th06" not in name:
            continue
        touched = sorted({c.find_bit(q).index for i in c.data if i.operation.name not in ("barrier", "delay") for q in i.qubits})
        ops = c.count_ops()
        s = PassManager([ALAPScheduleAnalysis(target=tgt), PadDelay(target=tgt)]).run(c)
        dur = s.duration * dt if s.duration else 0
        idle = 0.0
        for i in s.data:
            if i.operation.name == "delay" and s.find_bit(i.qubits[0]).index in touched:
                idle += i.operation.duration * dt
        nq = len(touched)
        print(f"{name:22} qubits {nq:2}  cz {ops.get('cz', 0):4}  sx {ops.get('sx', 0):4}  x {ops.get('x', 0):3}  rz {ops.get('rz', 0):4}"
              f"  duration {dur * 1e6:6.2f} us  idle share {idle / (nq * dur):.2f}  sx per cz {ops.get('sx', 0) / max(ops.get('cz', 1), 1):.2f}")
