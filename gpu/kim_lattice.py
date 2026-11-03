"""P5 stage B (prereg/drafts-2026-11-03/kim_lattice_note.md): the kicked Ising model on ibm_kingston's own lattice
(the form of IBM's 2023 utility experiment), t = 0..5, without error mitigation. Builds one job folder from one fetch
and the registry, and computes the exact answers on CPU (causal cones of at most 19 qubits; stabilizer at pi/2).
Nothing is submitted here.

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/kim_lattice.py FETCH_DIR REGISTRY.json OUT_DIR [--dry-clifford-sentinel]
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
THETAS, TMAX, SHOTS, RING, MAX_S = (0.0, 0.4, 0.8, 1.0, float(np.pi / 2)), 5, 4000, 40, 60
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
for th in THETAS:
    rec = K.build(dev_v, dict(theta=th, t_max=TMAX, shots=SHOTS), runs, compiler=rc)
    if not rec["valid"]:
        raise SystemExit(f"STOP: theta {th} not accepted: {rec['echo']['q2_circuits']}")
qubits, edges = K.region(dev_v)
mq = measured_qubits(rc.compile(C.model_circuit(list(np.zeros(C.n_model_angles(RING, 1))), RING, 1)))
ring = [int(mq[j]) for j in range(RING)]
sentinel.build(dev_v, runs, ring, SHOTS, rc, spec=SPEC)
man = J.assemble(dev_v, runs, os.path.join(OUT, "V", "job"), max_seconds=MAX_S)
assert man.get("stay") is True
ans = {}
for th in THETAS:
    ans[f"{th:.6f}"] = [K.answers(qubits, edges, th, t) for t in range(TMAX + 1)]
af = os.path.join(OUT, "answers.json")
json.dump(dict(qubits=qubits, edges=[list(e) for e in edges], answers=ans), open(af, "w"))
log = dict(dry_clifford_sentinel=DRY, fetch=f, registry=REG, registry_sha256=R.sha256_file(REG), now=now.isoformat(sep=" "),
           avoided=[a["path"] for a in avoid], masked_couplers=[list(e) for e in masked], thetas=list(THETAS),
           t_max=TMAX, shots=SHOTS, lattice_qubits=len(qubits), lattice_edges=len(edges),
           colours=len(K.colour(edges)), sentinel_ring=ring, circuits=len(man["pubs"]),
           qpu_seconds_model=man["qpu_seconds_model"], circuits_sha256=man["circuits_sha256"],
           answers_sha256=hashlib.sha256(open(af, "rb").read()).hexdigest(),
           cone_max={f"{th:.6f}": [a["cone_max"] for a in ans[f"{th:.6f}"]] for th in THETAS})
json.dump(log, open(os.path.join(OUT, "build.json"), "w"), indent=1)
print(f"job V: {log['circuits']} circuits, {log['qpu_seconds_model']} s by the time model; lattice {len(qubits)} qubits, "
      f"{len(edges)} edges, {log['colours']} colours; masked {log['masked_couplers']}; answers {log['answers_sha256'][:16]}")
for th in THETAS:
    print(f"theta {th:.4f}: M_exact(t) {[round(float(np.mean(a['z'])), 4) for a in ans[f'{th:.6f}']]}")
