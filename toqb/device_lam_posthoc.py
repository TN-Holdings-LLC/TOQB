"""Post hoc diagnostic (2026-10-22, after the device results; not a hypothesis, not part of C r9): the shrink of the
device's answers against the trained model's exact noiseless output on the test points, z_device ~ lam z_ideal + delta,
beside the twin's (lam, delta) fixed before submission. No labels are used; fitting on the test points makes it a
diagnostic only (an undamping with these values would be in-sample).

    python -m toqb.device_lam_posthoc JOB_DIR
"""
import json, sys, numpy as np
from toqb import s2r2 as S2, undamp as U
from toqb.s2rc_device import p1_of_counts
J = sys.argv[1]; RUNS = "results/device-2026-10-22/runs"
man = json.load(open(f"{J}/manifest.json")); raw = json.load(open(f"{J}/raw_counts.json"))
und = {c["name"]: c for c in json.load(open(f"{J}/undamp.json"))["cells"]}
rows = {r["pub"]: r["counts"] for r in raw["rows"]}
for cid, c in enumerate(man["cells"]):
    rec = json.load(open(f"{RUNS}/{c['name']}.json"))
    _, _, Xte, yte = S2.teacher_data2(rec["task"])
    zi = U.ideal_z(np.array(rec["final_mean"]), Xte, rec["task"])
    zd = np.zeros(len(Xte))
    for i, pub in enumerate(man["pubs"]):
        if pub["cell"] == cid:
            zd[pub["point"]] = 1 - 2 * p1_of_counts(rows[i])
    assert list(np.asarray(yte, int)) == list(c["labels"])
    lam, delta, rms = U.fit(zd, zi)
    print(f"{c['name']:36s} twin lam {und[c['name']]['lam']:.3f} delta {und[c['name']]['delta']:+.3f} | device (test points, post hoc) lam {lam:.3f} delta {delta:+.3f} rms {rms:.3f} | corr {np.corrcoef(zd, zi)[0,1]:.3f}")
