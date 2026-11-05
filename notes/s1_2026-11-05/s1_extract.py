"""S1 (post hoc, not a test): per-qubit table of the 2026-11-04 P6-shaped device runs (raw <Z>, own floor, answer).
usage: PYTHONPATH=<psf-os>:<TOQB> python notes/s1_2026-11-05/s1_extract.py OUT.json"""
import json, sys
import numpy as np
sys.path.insert(0, "gpu")
import p6_score as P  # noqa: E402
from psf_os import ising2d as I  # noqa: E402

RUNS = {"corr_fez": "results/corr-2026-11-04", "corr_marrakesh": "results/corr-marrakesh-2026-11-04",
        "p6_fez": "results/p6-device-2026-11-04", "p6_marrakesh": "results/p6-marrakesh-2026-11-04"}


def main(out):
    from psf_os import job as J
    from psf_os.kim import z_values
    res = {"qubits": I.QUBITS, "runs": {}}
    ans = {tx: P.answers(float(tx)) for tx in ("0.53", "0.3", "0.8")}
    res["answers"] = {tx: {str(t): a for t, a in A.items()} for tx, A in ans.items()}
    for name, d in RUNS.items():
        jd, runs = f"{d}/V/job", f"{d}/V/runs"
        sc = I.score(jd, runs)
        mir = {}
        for _, (rec, cc) in J.read(jd, runs).items():
            if rec.get("psfos_job", {}).get("kind") == "mirror2d":
                tx = f"{float(rec['psfos_job']['theta_x']):g}"
                mir[tx] = {str(p["t"]): z_values(cc[(p["input"], "z")], len(I.QUBITS))[0].tolist() for p in rec["points"]}
        res["runs"][name] = {"z": {tx: {str(t): list(map(float, v)) for t, v in sc[tx].items()} for tx in sc},
                             "mirror": mir}
        print(name, {tx: sorted(int(t) for t in sc[tx]) for tx in sc}, "mirror", {k: sorted(v) for k, v in mir.items()})
    json.dump(res, open(out, "w"))


if __name__ == "__main__":
    main(sys.argv[1])
