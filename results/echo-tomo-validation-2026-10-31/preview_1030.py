"""Post-hoc look at 30 October (kingston rerun, rule only): block signals over D = 24, 50, 100 (hz averaged) and the
connected ZZ correlation of neighbour pairs at D = 24, hz 0. Not a test; it informs the stage-1 draft.
    PYTHONPATH=. python results/echo-tomo-validation-2026-10-31/preview_1030.py"""
import json
import numpy as np
from toqb import defect_list as DL, echo_tomo as ET

J = "results/device-2026-10-30/rerun-rule-only/job"
R = "results/device-2026-10-30/rerun-rule-only/runs"
SEG = [3, 4, 5, 6, 7, 17, 27, 28, 29, 38, 49, 50, 51, 52, 53, 54, 55, 59]
A, B = SEG[:9], SEG[9:]
for D in (24, 50, 100):
    pr = DL.job_profiles(J, R, D=D)[0]
    phys, a = pr[40]
    m = lambda qs: a[[j for j, q in enumerate(phys) if q in qs]].mean()  # noqa: E731
    rest = a[[j for j, q in enumerate(phys) if q not in SEG]].mean()
    print(f"D {D}: block A {m(A):+.3f}, block B {m(B):+.3f}, rest {rest:+.3f}, n20 {pr[20][1].mean():+.3f}")
man = json.load(open(J + "/manifest.json"))
rows = DL._load_counts(J)
for n in (20, 40):
    name = f"kecho_n{n}_D24_hz0_h0.6-fold_rule"
    cid = [i for i, c in enumerate(man["cells"]) if c["name"] == name][0]
    rec = json.load(open(f"{R}/{name}.json"))
    phys = [int(rec["echo"]["measured_qubits"][str(j)]) for j in range(n)]
    cc = {rec["points"][p["point"]]["input"]: rows[k]["counts"] for k, p in enumerate(man["pubs"])
          if p["cell"] == cid and rec["points"][p["point"]]["setting"] == "echo"}
    c = ET.connected(cc, n)
    if n == 20:
        print(f"n 20 D 24 connected ZZ, all pairs: {c.mean():.3f}")
        continue
    s = set(SEG)
    ins = [j for j in range(n) if phys[j] in s and phys[(j + 1) % n] in s]
    out = [j for j in range(n) if phys[j] not in s and phys[(j + 1) % n] not in s]
    inb = [j for j in range(n) if phys[j] in B and phys[(j + 1) % n] in B]
    print(f"n 40 D 24 connected ZZ: dead-run pairs {c[ins].mean():.3f} ({len(ins)}), block B pairs {c[inb].mean():.3f} "
          f"({len(inb)}), healthy pairs {c[out].mean():.3f} sd {c[out].std(ddof=1):.3f} ({len(out)})")
