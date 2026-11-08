"""B (2): (a) per-site agreement with the exact answer (MSE over sites, from scores) for old / line, and the measured
m_s against the exact m_s; (b) CZ per coupler of the compiled user circuits (old vs line) at t = 4 for places 1 and 2,
with the per-qubit floor and mirror values of the same arms (cards)."""
import json, sys
from collections import Counter
from qiskit import qpy
from psf_os import user2d as U
R = sys.argv[1]
s = json.load(open(f"{R}/kingston/scores.json"))["arms"]
print("== (a) MSE over sites and m_s (measured / exact)")
for c in range(4):
    for t in (3, 4):
        parts = []
        for h, v in (("d", "old"), ("c", "carry"), ("l", "line")):
            a = s[f"h3{h}{c}_t{t}"]
            parts.append(f"{v}: mse {a['mse']:.4f} m_s {a['m_s']:.3f}/{a['m_s_exact']:.3f}")
        print(f"place {c} t {t}: " + " | ".join(parts))
print("== (b) CZ per coupler, t = 4 (compiled user circuits), top 8 couplers by line CZ; per-qubit floor / mirror")
cards = U.cards(f"{R}/kingston/job", f"{R}/kingston/runs", None)
for c in (1, 2):
    cnt = {}
    for h, v in (("d", "old"), ("l", "line")):
        (circ,) = qpy.load(open(f"{R}/kingston/runs/p2d_h3{h}{c}_t4.qpy", "rb"))
        cnt[v] = Counter(tuple(sorted(circ.find_bit(q).index for q in i.qubits)) for i in circ.data if i.operation.name == "cz")
    top = sorted(cnt["line"], key=lambda k: -cnt["line"][k])[:8]
    print(f"place {c}: couplers used old {len(cnt['old'])}, line {len(cnt['line'])}; max per coupler old {max(cnt['old'].values())}, line {max(cnt['line'].values())}")
    print("   " + "  ".join(f"{k}:{cnt['line'][k]}/{cnt['old'].get(k, 0)}" for k in top) + "   (line/old)")
    for h, v in (("d", "old"), ("l", "line")):
        cd = cards[f"h3{h}{c}_t4"]
        q = sorted(cd["qubits"], key=lambda x: x["mirror"])[:4]
        print(f"   {v}: lowest mirror qubits (site: floor, mirror) " + "  ".join(f"{x['q']}: {x['floor']:.2f},{x['mirror']:.2f}" for x in q))
