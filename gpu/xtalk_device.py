"""Crosstalk test job (draft for prereg/drafts-2026-11-04/xtalk_note_DRAFT.md; not declared): P5's circuit on the
suspect-qubit lattice, standard arm (barrier per colour class) against split arm (each class split into mutually
non-adjacent sublayers, barrier per sublayer), interleaved in each record; readout-pattern controls; mirrors of both
arms; ring sentinel. 4000 shots, no mitigation, "stay".

  theta 0.4  at t = 1..5, arms S and D     (where the correlations were amplified, 1.08-1.17x)
  theta 0.8  at t = 1..5, arms S and D     (where the magnetisation error is larger)
  theta 0    at t = 1, 5, arms S and D     (floor; every gate diagonal, ideal <Z> = 1)
  mirror of theta 0.4 at t = 3, 5, arms S and D
  readout patterns all0, all1, A, B, M0, M1, M2
  ring sentinel

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/xtalk_device.py FETCH_DIR|fake:NAME REGISTRY.json|none OUT_DIR
       [--dry-clifford-sentinel]
"""
import collections
import datetime as dt
import json
import os
import pickle
import sys
from zoneinfo import ZoneInfo

import numpy as np

from psf_os import allocate as A
from psf_os import circuits as C
from psf_os import crosstalk2d as X
from psf_os import device as Dv
from psf_os import job as J
from psf_os import kim as K
from psf_os import registry as R
from psf_os import sentinel
from psf_os.compile import RuleCompiler, measured_qubits

FETCH, REG, OUT = sys.argv[1:4]
DRY = "--dry-clifford-sentinel" in sys.argv
SPEC = dict(kind="echo_clifford", D=24) if DRY else None
SHOTS, RING, MAX_S = 4000, 40, 70
CELLS = [(0.4, [1, 2, 3, 4, 5]), (0.8, [1, 2, 3, 4, 5]), (0.0, [1, 5])]
MIRROR = (0.4, [3, 5])

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
for k, (th, ts) in enumerate(CELLS):
    rec = X.build(dev_v, dict(theta=th, ts=ts, shots=SHOTS, suspect=True), runs, compiler=rc, tag=f"{k}")
    if not rec["valid"]:
        raise SystemExit(f"STOP: theta {th} not accepted: {[c for c in rec['echo']['checks'] if not c['ok']]}")
    recs.append(rec)
mrec = X.build(dev_v, dict(theta=MIRROR[0], ts=MIRROR[1], shots=SHOTS, suspect=True, mirror=True), runs, compiler=rc,
               tag="3")
if not mrec["valid"]:
    raise SystemExit(f"STOP: mirror not accepted: {[c for c in mrec['echo']['checks'] if not c['ok']]}")
prec = X.build_patterns(dev_v, dict(shots=SHOTS, suspect=True), runs, compiler=rc, name="pxtalk4_readout-lattice")
if not prec["valid"]:
    raise SystemExit("STOP: readout patterns not accepted")
mq = measured_qubits(rc.compile(C.model_circuit(list(np.zeros(C.n_model_angles(RING, 1))), RING, 1)))
ring = [int(mq[j]) for j in range(RING)]
sentinel.build(dev_v, runs, ring, SHOTS, rc, spec=SPEC)
man = J.assemble(dev_v, runs, os.path.join(OUT, "V", "job"), max_seconds=MAX_S)
assert man.get("stay") is True

qubits, edges = recs[0]["qubits"], [tuple(e) for e in recs[0]["edges"]]
gS, gD = recs[0]["groups_standard"], recs[0]["groups_split"]
cov = {d: X.coverage(qubits, edges, X.pairs_at(edges, d)) for d in (1, 2, 3)}
log = dict(fetch=f, registry=REG, now=now.isoformat(sep=" "), avoided=[a["path"] for a in avoid],
           masked_couplers=[list(x) for x in masked], failed_couplers=[list(x) for x in dev.failed_couplers],
           failed_qubits=list(dev.failed_qubits), lattice=dict(qubits=len(qubits), edges=len(edges)),
           layers_per_step=dict(standard=len(gS), split=len(gD), standard_sizes=[len(g) for g in gS],
                                split_sizes=[len(g) for g in gD]),
           cells=[[th, ts] for th, ts in CELLS], mirror=[MIRROR[0], MIRROR[1]],
           patterns={n: len(v) for n, v in prec["flipped"].items()},
           pattern_coverage={str(d): dict(pairs=len(c), all_four=sum(len(s) == 4 for s in c.values()))
                             for d, c in cov.items()},
           sentinel_ring=ring, sentinel_overlaps_lattice=sorted(set(qubits) & set(ring)), circuits=len(man["pubs"]),
           qpu_seconds_model=man["qpu_seconds_model"], circuits_sha256=man["circuits_sha256"])
json.dump(log, open(os.path.join(OUT, "build.json"), "w"), indent=1)
print(f"{dev.name}: lattice {len(qubits)} qubits, {len(edges)} edges; CZ layers per step {len(gS)} -> {len(gD)} "
      f"(sizes {[len(g) for g in gS]} -> {[len(g) for g in gD]}); {log['circuits']} circuits, "
      f"{log['qpu_seconds_model']} s by the model; pattern coverage (all four states) "
      + ", ".join(f"d{d} {v['all_four']}/{v['pairs']}" for d, v in log["pattern_coverage"].items()))
