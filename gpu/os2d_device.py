"""OS2D test job (draft for prereg/drafts-2026-11-04/os2d_note_DRAFT.md; not declared): the P6 patch placed by
psf_os.lattice2d (through ising2d.place), with the user's own circuit mirrored as a sentinel (psf_os.mirror2d).

  theta_x 0.53 at t = 1..5     (P6's problem, CPU answers sealed in results/p6-answers-2026-11-04)
  theta_x 0    at t = 1, 5     (readout floor; every gate diagonal, ideal <Z> = 1)
  mirror of the theta_x 0.53 circuit at t = 3, 5 (U, barrier, U^dagger; ideal <Z> = 1; CZ exactly doubled)
  then the ring sentinel (echo D = 24 on the rule's n = 40 ring). 4000 shots, no mitigation, "stay".

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/os2d_device.py FETCH_DIR|fake:NAME REGISTRY.json|none OUT_DIR
       [--dry-clifford-sentinel]
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
from psf_os import ising2d as I
from psf_os import job as J
from psf_os import mirror2d as M
from psf_os import registry as R
from psf_os import sentinel
from psf_os.compile import RuleCompiler, measured_qubits

FETCH, REG, OUT = sys.argv[1:4]
DRY = "--dry-clifford-sentinel" in sys.argv
SPEC = dict(kind="echo_clifford", D=24) if DRY else None
SHOTS, RING, MAX_S = 4000, 40, 70
CELLS = [(0.53, [1, 2, 3, 4, 5]), (0.0, [1, 5])]
MIRROR_TS = [3, 5]

if os.path.exists(OUT):
    raise SystemExit(f"STOP: {OUT} exists")
if FETCH.startswith("fake:"):
    dev = Dv.fetch_fake(FETCH[5:])
    f = dict(backend=dev.name, fake=True)
else:
    f = json.load(open(os.path.join(FETCH, "fetch.json")))
    target = pickle.load(open(os.path.join(FETCH, "target.pkl"), "rb"))
    dev = Dv.from_target(target, f["backend"], source=dict(fetch=f.get("fetched"), target_sha256=f.get("target_sha256")))
now = dt.datetime.now(ZoneInfo("Europe/Zurich")).replace(tzinfo=None, microsecond=0)
avoid = R.avoid_paths(R.load(REG), dev.name, now) if REG != "none" else []
dev_v, masked = A.mask(dev, avoid, reason=f"registry at {now.isoformat(sep=' ')}") if avoid else (dev, [])
rc = RuleCompiler(dev_v)
runs = os.path.join(OUT, "V", "runs")
recs = []
for tx, ts in CELLS:
    rec = I.build(dev_v, dict(theta_x=tx, ts=ts, shots=SHOTS), runs, compiler=rc)
    if not rec["valid"]:
        raise SystemExit(f"STOP: theta_x {tx} not accepted: {rec['echo']['q2_circuits']} against {rec['echo']['q2_expected']}")
    recs.append(rec)
mrec = M.build(dev_v, dict(ts=MIRROR_TS, theta_x=0.53, shots=SHOTS), runs, compiler=rc)
if not mrec["valid"]:
    raise SystemExit(f"STOP: mirror not accepted: {mrec['echo']['q2_circuits']} against {mrec['echo']['q2_expected']}")
if mrec["mapping"] != recs[0]["mapping"]:
    raise SystemExit("STOP: the mirror landed on another copy")
mq = measured_qubits(rc.compile(C.model_circuit(list(np.zeros(C.n_model_angles(RING, 1))), RING, 1)))
ring = [int(mq[j]) for j in range(RING)]
sentinel.build(dev_v, runs, ring, SHOTS, rc, spec=SPEC)
man = J.assemble(dev_v, runs, os.path.join(OUT, "V", "job"), max_seconds=MAX_S)
assert man.get("stay") is True
patch = set(recs[0]["mapping"].values())
log = dict(fetch=f, registry=REG, now=now.isoformat(sep=" "), avoided=[a["path"] for a in avoid],
           masked_couplers=[list(x) for x in masked], failed_couplers=[list(x) for x in dev.failed_couplers],
           failed_qubits=list(dev.failed_qubits), copy=recs[0]["copy"], cells=[[tx, ts] for tx, ts in CELLS],
           q2_per_circuit={f"{tx:g}": r["echo"]["q2_circuits"] for (tx, _), r in zip(CELLS, recs)},
           mirror_ts=MIRROR_TS, mirror_q2=mrec["echo"]["q2_circuits"],
           sentinel_ring=ring, sentinel_overlaps_patch=sorted(patch & set(ring)), circuits=len(man["pubs"]),
           qpu_seconds_model=man["qpu_seconds_model"], circuits_sha256=man["circuits_sha256"])
json.dump(log, open(os.path.join(OUT, "build.json"), "w"), indent=1)
print(f"{dev.name}: copy (drow {log['copy']['drow']}, dcol {log['copy']['dcol']}), passed over "
      f"{len(log['copy']['passed_over'])}; {log['circuits']} circuits, {log['qpu_seconds_model']} s by the model; "
      f"sentinel ring overlaps the patch on {len(log['sentinel_overlaps_patch'])} qubits")
