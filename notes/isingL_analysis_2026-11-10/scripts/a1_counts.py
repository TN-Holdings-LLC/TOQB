"""1. Counts on the 4 x 3 x 2 arms (fez job of 2026-11-10, read only): touched qubits, CZ per coupler, CZ layers, ALAP
duration and idle time per touched qubit (FakeFez gate durations as the stand-in for fez's; fez is a Heron r2 too)."""
import json, sys
from collections import Counter
import numpy as np
from qiskit import qpy
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDelay
from qiskit_ibm_runtime.fake_provider import FakeFez

R = sys.argv[1]
tgt = FakeFez().target
dt = tgt.dt
rep = json.load(open(f"{R}/ibm_fez/report.json"))["arms"]
out = {}
for c in (0, 1):
    for t in (1, 2, 3, 4):
        row = {}
        for lay in ("f", "l"):
            tag = f"q32{lay}{c}_t{t}"
            (circ,) = qpy.load(open(f"{R}/ibm_fez/runs/p2d_{tag}.qpy", "rb"))
            touched = sorted({circ.find_bit(q).index for i in circ.data if i.operation.name not in ("barrier", "delay", "measure") for q in i.qubits})
            cz = Counter(tuple(sorted(circ.find_bit(q).index for q in i.qubits)) for i in circ.data if i.operation.name == "cz")
            s = PassManager([ALAPScheduleAnalysis(target=tgt), PadDelay(target=tgt)]).run(circ.remove_final_measurements(inplace=False))
            idle = Counter()
            for i in s.data:
                if i.operation.name == "delay":
                    q = s.find_bit(i.qubits[0]).index
                    if q in touched:
                        idle[q] += i.operation.duration * dt
            dur = s.duration * dt
            sq = Counter(i.operation.name for i in circ.data if len(i.qubits) == 1)
            row[lay] = dict(touched=touched, cz_total=sum(cz.values()), couplers=len(cz), cz_max=max(cz.values()),
                            top=cz.most_common(4), layers=rep[tag]["cz_layers"], duration_us=dur * 1e6,
                            idle_mean_us=float(np.mean([idle[q] for q in touched])) * 1e6,
                            idle_max_us=max(idle[q] for q in touched) * 1e6, idle=dict(idle), sx=sq.get("sx", 0))
        f, l = row["f"], row["l"]
        same = set(f["touched"]) == set(l["touched"])
        print(f"place {c} t {t}: same qubits {same} ({len(f['touched'])}/{len(l['touched'])}) | CZ {f['cz_total']}/{l['cz_total']} "
              f"couplers {f['couplers']}/{l['couplers']} max per coupler {f['cz_max']}/{l['cz_max']} | layers {f['layers']}/{l['layers']} | "
              f"duration {f['duration_us']:.1f}/{l['duration_us']:.1f} us | idle mean {f['idle_mean_us']:.1f}/{l['idle_mean_us']:.1f} "
              f"max {f['idle_max_us']:.1f}/{l['idle_max_us']:.1f} us | sx {f['sx']}/{l['sx']}   (fold/line)")
        if t == 4:
            print(f"      top couplers fold {f['top']}  line {l['top']}")
        out[f"c{c}_t{t}"] = {k: {kk: vv for kk, vv in v.items() if kk != 'idle'} | {"idle": {str(q): x for q, x in v["idle"].items()}} for k, v in row.items()}
json.dump(out, open("a1_counts.json", "w"), indent=1, default=str)
