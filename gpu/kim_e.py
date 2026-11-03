"""P5 stage E (prereg/drafts-2026-11-03/kim_e_note.md): the suspect-qubit lattice (psf_os.kim.region suspect=True) on
one device. Builds one job folder, the CPU answers and the pod's input.

  --stages C : theta 0, 0.4, 0.8, 1.0 at t = 6, 7, 8                       (job K: ibm_kingston)
  --stages BC: theta 0, 0.4, 0.8, 1.0 at t = 1..8                          (job X: the other device)
  then the sentinel (echo D = 24 on the n = 40 ring). 4000 shots, "stay".
Answers: theta 0 trivial; t <= 5 CPU cones; t = 6-8 from the pod (gpu/kim_answers_pod.sh with LAT=lattice.json).

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/kim_e.py FETCH_DIR REGISTRY.json|none OUT_DIR --stages C|BC [--dry-clifford-sentinel]
"""
import datetime as dt
import hashlib
import json
import os
import pickle
import sys
from zoneinfo import ZoneInfo

import numpy as np

from psf_os import allocate as A
from psf_os import circuits as C
from psf_os import device as Dv
from psf_os import job as J
from psf_os import kim as K
from psf_os import registry as R
from psf_os import sentinel
from psf_os.compile import RuleCompiler, measured_qubits

FETCH, REG, OUT = sys.argv[1:4]
STAGES = sys.argv[sys.argv.index("--stages") + 1]
DRY = "--dry-clifford-sentinel" in sys.argv
SPEC = dict(kind="echo_clifford", D=24) if DRY else None
P2 = float(np.pi / 2)
THETAS = (0.0, 0.4, 0.8, 1.0)
TS = {"C": [6, 7, 8], "BC": [1, 2, 3, 4, 5, 6, 7, 8]}[STAGES]
SHOTS, RING, MAX_S = 4000, 40, 70


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


if os.path.exists(OUT):
    raise SystemExit(f"STOP: {OUT} exists")
f = json.load(open(os.path.join(FETCH, "fetch.json")))
target = pickle.load(open(os.path.join(FETCH, "target.pkl"), "rb"))
dev = Dv.from_target(target, f["backend"], source=dict(fetch=f.get("fetched"), target_sha256=f.get("target_sha256")))
now = dt.datetime.now(ZoneInfo("Europe/Zurich")).replace(tzinfo=None, microsecond=0)
avoid = R.avoid_paths(R.load(REG), dev.name, now) if REG != "none" else []
dev_v, masked = A.mask(dev, avoid, reason=f"registry at {now.isoformat(sep=' ')}")
rc = RuleCompiler(dev_v)
runs = os.path.join(OUT, "V", "runs")
for th in THETAS:
    rec = K.build(dev_v, dict(theta=th, ts=TS, shots=SHOTS, tag="e", suspect=True), runs, compiler=rc)
    if not rec["valid"]:
        raise SystemExit(f"STOP: theta {th} not accepted: {rec['echo']['q2_circuits']}")
mq = measured_qubits(rc.compile(C.model_circuit(list(np.zeros(C.n_model_angles(RING, 1))), RING, 1)))
ring = [int(mq[j]) for j in range(RING)]
sentinel.build(dev_v, runs, ring, SHOTS, rc, spec=SPEC)
man = J.assemble(dev_v, runs, os.path.join(OUT, "V", "job"), max_seconds=MAX_S)
assert man.get("stay") is True
q, e = K.region(dev_v, suspect=True)
ans = {f"{th:.6f}": {str(t): K.answers(q, e, th, t) for t in TS if t <= 5 or th == 0.0} for th in THETAS}
af = os.path.join(OUT, "answers_cpu.json")
json.dump(dict(qubits=q, edges=[list(x) for x in e], answers=ans), open(af, "w"))
cone = {str(t): [len(K.cone(q, e, x, t)[0]) for x in q] for t in (6, 7, 8)}
lf = os.path.join(OUT, "lattice.json")
json.dump(dict(qubits=q, edges=[list(x) for x in e], thetas=[0.4, 0.8, 1.0], ts=[6, 7, 8], max_qubits=33,
               cone_sizes=cone, check_K1=dict(theta=0.8, t=5, z=K.answers(q, e, 0.8, 5)["z"]),
               check_K3={str(t): K.answers(q, e, P2, t)["z"] for t in (6, 7)}), open(lf, "w"))
log = dict(stages=STAGES, ts=TS, dry_clifford_sentinel=DRY, fetch=f, registry=REG,
           registry_sha256=R.sha256_file(REG) if REG != "none" else None, now=now.isoformat(sep=" "),
           avoided=[a["path"] for a in avoid], masked_couplers=[list(x) for x in masked],
           failed_couplers=[list(x) for x in dev.failed_couplers], failed_qubits=list(dev.failed_qubits),
           lattice=dict(qubits=len(q), edges=len(e)), answered_at={t: sum(1 for k in cone[t] if k <= 33) for t in cone},
           sentinel_ring=ring, circuits=len(man["pubs"]), qpu_seconds_model=man["qpu_seconds_model"],
           circuits_sha256=man["circuits_sha256"], answers_cpu_sha256=sha(af), lattice_sha256=sha(lf))
json.dump(log, open(os.path.join(OUT, "build.json"), "w"), indent=1)
print(f"{dev.name}: {log['circuits']} circuits, {log['qpu_seconds_model']} s; suspect lattice {log['lattice']}; failed "
      f"{log['failed_couplers']} {log['failed_qubits']}; masked {log['masked_couplers']}; answered at t = 6, 7, 8: "
      f"{log['answered_at']}; answers_cpu {log['answers_cpu_sha256'][:16]}, lattice {log['lattice_sha256'][:16]}")
