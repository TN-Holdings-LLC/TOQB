"""Self-repair test, job 2 (draft for prereg/drafts-2026-11-04/repair_note_DRAFT.md; not declared): runs the chain
(psf_os.repair2d, rule and release as declared) on the ledger that includes job 1, then builds in one job the P6
problem on A's copy (no chain) and on B's copy (with the chain), interleaved, each with its floor (theta_x 0 at t = 1, 5),
and the ring sentinel. Refuses to build if the chain's status is not TESTABLE (the test is then NOT TESTED or NO COPY,
and the log says which). 4000 shots, no mitigation, "stay".

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/repair_job2.py FETCH_DIR|fake:NAME REGISTRY.json|none LEDGER.json RULE
       RELEASE OUT_DIR [--now ISO] [--dry-clifford-sentinel]
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
from psf_os import ledger as Lg
from psf_os import registry as R
from psf_os import repair2d as Rp
from psf_os import sentinel
from psf_os.compile import RuleCompiler, measured_qubits

FETCH, REG, LED, RULE, REL, OUT = sys.argv[1:7]
DRY = "--dry-clifford-sentinel" in sys.argv
SPEC = dict(kind="echo_clifford", D=24) if DRY else None
SHOTS, RING, MAX_S = 4000, 40, 70
if os.path.exists(OUT):
    raise SystemExit(f"STOP: {OUT} exists")
if FETCH.startswith("fake:"):
    dev = Dv.fetch_fake(FETCH[5:])
    f = dict(backend=dev.name, fake=True)
else:
    f = json.load(open(os.path.join(FETCH, "fetch.json")))
    target = pickle.load(open(os.path.join(FETCH, "target.pkl"), "rb"))
    dev = Dv.from_target(target, f["backend"], source=dict(fetch=f.get("fetched"), target_sha256=f.get("target_sha256")))
now = (dt.datetime.fromisoformat(sys.argv[sys.argv.index("--now") + 1]) if "--now" in sys.argv else
       dt.datetime.now(ZoneInfo("Europe/Zurich")).replace(tzinfo=None, microsecond=0))
avoid = R.avoid_paths(R.load(REG), dev.name, now) if REG != "none" else []
dev_v, masked = A.mask(dev, avoid, reason=f"registry at {now.isoformat(sep=' ')}") if avoid else (dev, [])
led = Lg.load(LED)
if not any(r["device"] == dev.name for r in led["records"]):
    raise SystemExit(f"STOP: the ledger has no readings for {dev.name} (job 2 must run on job 1's device)")
late = [r["job"] for r in led["records"] if dt.datetime.fromisoformat(r["when"]) > now]
if late:
    # a reading dated after `now` is never used by the chain (no look-ahead); here it means a clock or WHEN mistake
    raise SystemExit(f"STOP: the ledger has readings after now ({now}): jobs {sorted(set(late))}")
log = Rp.chain(dev_v, led, now, I.EDGES, I.QUBITS, rule=RULE, release=REL, offsets=I.OFFSETS)
log.update(ledger_sha256=R.sha256_file(LED), registry=REG, fetch=f)
os.makedirs(OUT)
Rp.save_log(log, os.path.join(OUT, "chain.json"))
print(f"chain ({RULE}, {REL}): excluded {sorted(log['excluded'])}; status {log['status']}")
if log["status"] != "TESTABLE":
    raise SystemExit(0)
rc = RuleCompiler(dev_v)
runs = os.path.join(OUT, "V", "runs")
for tx, ts, nm in ((0.53, [1, 2, 3, 4, 5], "prep2d_a_tx0.53"), (0.0, [1, 5], "prep2d_b_tx0_floor")):
    rec = Rp.build(dev_v, log, dict(ts=ts, theta_x=tx, shots=SHOTS), runs, compiler=rc, name=nm)
    if not rec["valid"]:
        raise SystemExit(f"STOP: theta_x {tx} not accepted")
mq = measured_qubits(rc.compile(C.model_circuit(list(np.zeros(C.n_model_angles(RING, 1))), RING, 1)))
ring = [int(mq[j]) for j in range(RING)]
sentinel.build(dev_v, runs, ring, SHOTS, rc, spec=SPEC)
man = J.assemble(dev_v, runs, os.path.join(OUT, "V", "job"), max_seconds=MAX_S)
assert man.get("stay") is True
b = dict(now=now.isoformat(sep=" "), A=log["A"]["copy"], B=log["B"]["copy"], price=log["price"],
         circuits=len(man["pubs"]), qpu_seconds_model=man["qpu_seconds_model"], circuits_sha256=man["circuits_sha256"],
         sentinel_ring=ring)
json.dump(b, open(os.path.join(OUT, "build.json"), "w"), indent=1)
print(f"{dev.name}: A copy {log['A']['copy']}, B copy {log['B']['copy']}; {b['circuits']} circuits, "
      f"{b['qpu_seconds_model']} s by the model")
