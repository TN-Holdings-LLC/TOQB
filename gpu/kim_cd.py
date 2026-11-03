"""P5 stages C, D and the suspect-qubit rule (prereg/drafts-2026-11-03/kim_cd_note.md): one job on ibm_kingston.

  tag b: the lattice as in stage B (registry mask), theta 0.4, 0.8, 1.0, t = 1..5            (answers: CPU cones)
  tag s: the lattice without the ends of failed or masked couplers (kim.region suspect=True), the same circuits
                                                                                             (answers: CPU cones)
  tag c: the stage-B lattice, theta 0, 0.4, 0.8, 1.0, pi/2, t = 6, 7, 8, 20
         (answers: theta 0 trivial, pi/2 stabilizer on CPU; 0.4-1.0 at t = 6-8 from the pod for qubits whose cone has
         at most 33 qubits, gpu/kim_answers_pod.sh; t = 20: none)
  then the sentinel (echo D = 24 on the n = 40 ring). 4000 shots, "stay".

Writes OUT/V/job, OUT/answers_cpu.json, OUT/lattice.json (input of the pod) and OUT/build.json. Nothing is submitted.

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/kim_cd.py FETCH_DIR REGISTRY.json OUT_DIR [--dry-clifford-sentinel]
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
DRY = "--dry-clifford-sentinel" in sys.argv
SPEC = dict(kind="echo_clifford", D=24) if DRY else None
P2 = float(np.pi / 2)
B_THETAS, B_TS = (0.4, 0.8, 1.0), [1, 2, 3, 4, 5]
C_THETAS, C_TS = (0.0, 0.4, 0.8, 1.0, P2), [6, 7, 8, 20]
SHOTS, RING, MAX_S = 4000, 40, 70


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


if os.path.exists(OUT):
    raise SystemExit(f"STOP: {OUT} exists")
f = json.load(open(os.path.join(FETCH, "fetch.json")))
target = pickle.load(open(os.path.join(FETCH, "target.pkl"), "rb"))
dev = Dv.from_target(target, f["backend"], source=dict(fetch=f.get("fetched"), target_sha256=f.get("target_sha256")))
reg = R.load(REG)
now = dt.datetime.now(ZoneInfo("Europe/Zurich")).replace(tzinfo=None, microsecond=0)
avoid = R.avoid_paths(reg, dev.name, now)
dev_v, masked = A.mask(dev, avoid, reason=f"registry at {now.isoformat(sep=' ')}")
rc = RuleCompiler(dev_v)
runs = os.path.join(OUT, "V", "runs")
for tag, suspect, thetas, ts in (("b", False, B_THETAS, B_TS), ("s", True, B_THETAS, B_TS), ("c", False, C_THETAS, C_TS)):
    for th in thetas:
        rec = K.build(dev_v, dict(theta=th, ts=ts, shots=SHOTS, tag=tag, suspect=suspect), runs, compiler=rc)
        if not rec["valid"]:
            raise SystemExit(f"STOP: {tag} theta {th} not accepted: {rec['echo']['q2_circuits']}")
mq = measured_qubits(rc.compile(C.model_circuit(list(np.zeros(C.n_model_angles(RING, 1))), RING, 1)))
ring = [int(mq[j]) for j in range(RING)]
sentinel.build(dev_v, runs, ring, SHOTS, rc, spec=SPEC)
man = J.assemble(dev_v, runs, os.path.join(OUT, "V", "job"), max_seconds=MAX_S)
assert man.get("stay") is True

lat = {"b": K.region(dev_v), "s": K.region(dev_v, suspect=True)}
ans = {}
for tag in ("b", "s"):
    q, e = lat[tag]
    ans[tag] = {f"{th:.6f}": {str(t): K.answers(q, e, th, t) for t in B_TS} for th in B_THETAS}
q, e = lat["b"]
ans["c"] = {f"{0.0:.6f}": {str(t): K.answers(q, e, 0.0, t) for t in C_TS},
            f"{P2:.6f}": {str(t): K.answers(q, e, P2, t) for t in C_TS}}
af = os.path.join(OUT, "answers_cpu.json")
json.dump(dict(lattices={k: dict(qubits=v[0], edges=[list(x) for x in v[1]]) for k, v in lat.items()}, answers=ans),
          open(af, "w"))
cone = {str(t): [len(K.cone(q, e, x, t)[0]) for x in q] for t in (6, 7, 8)}
lf = os.path.join(OUT, "lattice.json")
json.dump(dict(qubits=q, edges=[list(x) for x in e], thetas=[0.4, 0.8, 1.0], ts=[6, 7, 8], max_qubits=33, cone_sizes=cone,
               check_K1=dict(theta=0.8, t=5, z=ans["b"][f"{0.8:.6f}"]["5"]["z"]),
               check_K3={str(t): ans["c"][f"{P2:.6f}"][str(t)]["z"] for t in (6, 7)}), open(lf, "w"))
log = dict(dry_clifford_sentinel=DRY, fetch=f, registry=REG, registry_sha256=R.sha256_file(REG), now=now.isoformat(sep=" "),
           avoided=[a["path"] for a in avoid], masked_couplers=[list(x) for x in masked],
           lattice_b=dict(qubits=len(lat["b"][0]), edges=len(lat["b"][1])),
           lattice_s=dict(qubits=len(lat["s"][0]), edges=len(lat["s"][1]),
                          dropped=sorted(set(lat["b"][0]) - set(lat["s"][0]))),
           answered_at={t: sum(1 for k in cone[t] if k <= 33) for t in cone}, sentinel_ring=ring,
           circuits=len(man["pubs"]), qpu_seconds_model=man["qpu_seconds_model"], circuits_sha256=man["circuits_sha256"],
           answers_cpu_sha256=sha(af), lattice_sha256=sha(lf))
json.dump(log, open(os.path.join(OUT, "build.json"), "w"), indent=1)
print(f"job V: {log['circuits']} circuits, {log['qpu_seconds_model']} s by the time model; lattice b {log['lattice_b']}, "
      f"s {log['lattice_s']['qubits']} qubits {log['lattice_s']['edges']} edges (dropped {log['lattice_s']['dropped']}); "
      f"answered by the pod at t = 6, 7, 8: {log['answered_at']}; answers_cpu {log['answers_cpu_sha256'][:16]}, "
      f"lattice {log['lattice_sha256'][:16]}")
