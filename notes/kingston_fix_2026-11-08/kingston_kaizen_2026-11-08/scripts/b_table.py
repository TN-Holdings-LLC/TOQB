"""B (1): per place and t, the retention, mirror and floor means of old / carry / line (scores.json), and the
compiled circuits' duration with kingston-like durations (FakeFez target as a stand-in), number of CZ and CZ layers."""
import json, sys
from qiskit import qpy
R = sys.argv[1]
s = json.load(open(f"{R}/kingston/scores.json"))["arms"]
print(f"{'arm':9} {'CZ':>4} {'ret':>6} {'mirror':>6} {'floor':>6}")
for c in range(4):
    for t in range(1, 5):
        row = []
        for h, v in (("d", "old"), ("c", "carry"), ("l", "line")):
            a = s[f"h3{h}{c}_t{t}"]
            row.append(f"{v} {a['cz']:3} ret {a['retention']:.3f} mir {a['mirror_mean']:.3f} fl {a['floor_mean']:.3f}")
        print(f"place {c} t {t}: " + " | ".join(row))
