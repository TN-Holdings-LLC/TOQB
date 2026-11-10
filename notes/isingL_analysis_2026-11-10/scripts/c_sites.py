"""3b. Per-site view of the simulation (FakeFez, not tuned) beside the device, place 0, t 1-4: squared error per
site for fold and line (simulated mean over 20 trajectories vs the device), the line-minus-fold excess per site,
and the sites where the device's excess sits (13, 14, 15). Also FakeFez's own numbers on the bridge qubits and the
qubits under the device's worst line sites (FakeFez's snapshot, not the run day)."""
import json, sys
import numpy as np
base = sys.argv[1]
s = json.load(open(f"{base}/pod_out/out/q32.json"))["circuits"]
ans = json.load(open(f"{base}/ckit/inputs/q32_answers.json"))
dev = json.load(open(f"{base}/work/a2_map.json"))
out = {}
for t in (1, 2, 3, 4):
    sim, dv = {}, {}
    for lay in ("f", "l"):
        tag = f"q32{lay}0_t{t}"
        z = np.asarray(s["p2d_" + tag]["z"])[:, :24].mean(0)
        ex = np.array([ans[tag][str(q)] for q in range(24)])
        sim[lay] = (z - ex) ** 2
    d = dev[f"c0_t{t}"]
    assert d["sites"] == list(range(24)) or [int(x) for x in d["sites"]] == list(range(24))
    dv["f"], dv["l"] = np.array(d["sq_err_fold"]), np.array(d["sq_err_line"])
    xs, xd = sim["l"] - sim["f"], dv["l"] - dv["f"]
    r = float(np.corrcoef(xs, xd)[0, 1])
    top_d = list(np.argsort(-xd)[:3]); top_s = list(np.argsort(-xs)[:3])
    print(f"t {t}: line worse at sim {int((xs > 0).sum())}/24, device {int((xd > 0).sum())}/24 sites; "
          f"corr(sim excess, device excess) over sites {r:+.2f}; top-3 excess sites device {top_d} sim {top_s}")
    print("   site: sim sq err fold/line | device sq err fold/line")
    for q in (13, 14, 15):
        print(f"   {q:2}: {sim['f'][q]:.3f}/{sim['l'][q]:.3f} | {dv['f'][q]:.3f}/{dv['l'][q]:.3f}")
    out[f"t{t}"] = dict(sim_fold=sim["f"].tolist(), sim_line=sim["l"].tolist(), corr=r)
json.dump(out, open(f"{base}/work/c_sites.json", "w"), indent=1)
from qiskit_ibm_runtime.fake_provider import FakeFez
p = FakeFez().properties()
print(f"FakeFez snapshot ({p.last_update_date}):")
for q in (3, 16, 17, 20, 23, 24, 36, 37):
    print(f"  q{q}: T1 {p.t1(q)*1e6:.0f} us, T2 {p.t2(q)*1e6:.0f} us, readout {p.readout_error(q):.4f}")
for a, b in ((3, 16), (16, 23), (7, 17), (17, 27), (21, 36), (25, 37)):
    try:
        e = p.gate_error("cz", [a, b])
    except Exception:
        e = p.gate_error("cz", [b, a])
    print(f"  cz ({a}, {b}): error {e:.4f}")
