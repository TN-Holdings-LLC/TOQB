"""Diagnostic only (not a result): per-trajectory spread of the echo twin, one record, CPU."""
import sys, json, os, time
import numpy as np
from qiskit import qpy
sys.path.insert(0, os.environ.get("TOQB_DIR", "."))
from toqb import s2r as S, traj2 as T2, kising_charge as KC
rec, T, which, zz = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
r = json.load(open(rec)); d = os.path.dirname(rec)
p = dict(r["standin"]);
if zz != "keep": p["zz_hz"] = float(zz)
st = S.StandIn(**p)
cs = qpy.load(open(os.path.join(d, r["export"]["qpy"]), "rb"))
eng = T2.Engine(); n = 20; seed = 20261030
idx = [int(i) for i in which.split(",")]
out = {}
for k in idx:
    c = cs[k]; t0 = time.time()
    rr, _ = st.prepared(c); pl = T2.plan(c, rr, st.target, over=st.params["over"])
    meas = sorted(pl.meas, key=lambda m: m[1])
    psi, _ = eng.run(pl, pl.angles(c)[None, :], T, seed * 1009)
    Z = []
    for (q, cl, p01, p10) in meas:
        p1 = np.asarray(eng._p1(psi, pl.n, q), float).reshape(-1)
        Z.append((1 - p01 - p10) * (1 - 2 * p1) + (p10 - p01))
    Z = np.array(Z)  # (clbits, T)
    pt = r["points"][k]
    zin = 1 - 2 * np.array(KC.input_bits(pt["input"], n))
    sgn = -zin if pt["setting"] == "echo" else zin
    m = (sgn[:, None] * Z).sum(0)
    out[k] = m.tolist()
    print(k, pt, "mean m", m.mean(), "sd", m.std(ddof=1), f"{time.time()-t0:.0f}s", flush=True)
json.dump(out, open(sys.argv[5], "w"))
