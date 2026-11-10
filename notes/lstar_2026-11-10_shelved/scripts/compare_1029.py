"""Compare the narrowed L* build with the 10-29 kingston P1 records (n = 20, same arm, same L): two-qubit gate count,
the measured map (clbit -> physical qubit), the active qubit count, and the QPY sha256 (10-29: qpy_sha256.txt)."""
import json, os, sys
new, old = sys.argv[1], sys.argv[2]
sha_old = {}
for l in open(os.path.join(old, "qpy_sha256.txt")):
    h, p = l.split()
    sha_old[os.path.basename(p)] = h
allsame = True
for arm in ("fold_rule", "qiskit_2_blind_template"):
    for L in (24, 50, 100):
        nm = f"kcharge_n20_L{L}_h0.6-{arm}"
        a = json.load(open(os.path.join(new, "runs1", nm + ".json")))
        b = json.load(open(os.path.join(old, "runs1", nm + ".json")))
        same_map = a["charge"]["measured_qubits"] == b["charge"]["measured_qubits"]
        same_q2 = a["q2"] == b["q2"]
        same_sha = a["export"]["sha256"] == sha_old.get(nm + ".qpy")
        allsame &= same_map and same_q2
        print(f"{nm:46s} q2 {a['q2']} vs {b['q2']} {'SAME' if same_q2 else 'DIFF'} | measured map "
              f"{'SAME' if same_map else 'DIFF'} | active {a['active']} vs {b['active']} | qpy sha256 "
              f"{'SAME' if same_sha else 'differs'} | us {a['us']} vs {b['us']} | version new {a['version'][:60]!r} old {b['version'][:60]!r}")
        if not same_map:
            print("   new", [a["charge"]["measured_qubits"][str(k)] for k in range(20)])
            print("   old", [b["charge"]["measured_qubits"][str(k)] for k in range(20)])
print("ALL q2 and measured maps SAME" if allsame else "SOME DIFFER")
