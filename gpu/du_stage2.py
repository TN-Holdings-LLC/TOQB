"""P4 stage 2b (prereg/drafts-2026-11-03/du_stage2_note.md): the same chain circuit, N = 33, t = 0..16, away from the
dual-unitary point, answers from a GPU computation sealed before the run. Builds one job folder (V: the chain is
positions 0..32 of the n = 40 ring placed around the registry) from one fetch and the registry. CPU only.

  Records (one per (h, b), t = 0..16): (0, pi/4) Clifford control; (0.15, pi/4) dual-unitary control (closed form);
  (0.15, pi/4 - 0.1) and (0.15, pi/4 - 0.2) (answers from gpu/du_answers.py). Then the sentinel (echo D = 24 on the
  same ring). 4000 shots, "stay".

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/du_stage2.py FETCH_DIR REGISTRY.json OUT_DIR [--dry-clifford-sentinel]
"""
import datetime as dt
import json
import os
import pickle
import sys
from zoneinfo import ZoneInfo

import numpy as np

from psf_os import allocate as A
from psf_os import circuits as C
from psf_os import device as Dv
from psf_os import dual as DU
from psf_os import job as J
from psf_os import registry as R
from psf_os import sentinel
from psf_os.compile import RuleCompiler, measured_qubits

FETCH, REG, OUT = sys.argv[1:4]
DRY = "--dry-clifford-sentinel" in sys.argv
SPEC = dict(kind="echo_clifford", D=24) if DRY else None
N, TMAX, SHOTS, RING, MAX_S = 33, 16, 4000, 40, 90
SETTINGS = ((0.0, np.pi / 4), (0.15, np.pi / 4), (0.15, np.pi / 4 - 0.1), (0.15, np.pi / 4 - 0.2))  # (h, b)
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
mq = measured_qubits(rc.compile(C.model_circuit(list(np.zeros(C.n_model_angles(RING, 1))), RING, 1)))
ring = [int(mq[j]) for j in range(RING)]
runs = os.path.join(OUT, "V", "runs")
for h, b in SETTINGS:
    rec = DU.build(dev_v, dict(N=N, h=h, kick=b, t_max=TMAX, shots=SHOTS), runs, ring, compiler=rc)
    if not rec["valid"]:
        raise SystemExit(f"STOP: (h {h}, b {b}) not accepted: {rec['echo']['q2_circuits']}")
sentinel.build(dev_v, runs, ring, SHOTS, rc, spec=SPEC)
man = J.assemble(dev_v, runs, os.path.join(OUT, "V", "job"), max_seconds=MAX_S)
assert man.get("stay") is True
chain = ring[:N]
log = dict(dry_clifford_sentinel=DRY, fetch=f, registry=REG, registry_sha256=R.sha256_file(REG), now=now.isoformat(sep=" "),
           avoided=[a["path"] for a in avoid], masked_couplers=[list(e) for e in masked], N=N, t_max=TMAX,
           settings=[dict(h=h, b=b) for h, b in SETTINGS], shots=SHOTS, ring=ring, chain=chain,
           listed_paths_on_chain=[a["path"] for a in avoid if all(q in chain for q in a["path"])],
           circuits=len(man["pubs"]), qpu_seconds_model=man["qpu_seconds_model"], circuits_sha256=man["circuits_sha256"])
json.dump(log, open(os.path.join(OUT, "build.json"), "w"), indent=1)
print(f"job V: {log['circuits']} circuits, {log['qpu_seconds_model']} s by the time model, chain {chain}, "
      f"listed paths on the chain {log['listed_paths_on_chain']}, masked {log['masked_couplers']}")
