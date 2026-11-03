"""P4: reproduction of the dual-unitary kicked Ising experiment (arXiv 2411.00765) with psf-os, no error mitigation
(prereg/drafts-2026-11-03/du_repro_note.md). Builds two job folders from one fetch and the registry. CPU only;
nothing is submitted here.

  Job S: the chain = positions 0..20 of the rule's n = 40 ring on the device record as fetched (holds the known
         defect path [28, 29, 38, 49]).
  Job V: the chain = positions 0..20 of the n = 40 ring placed around the registry (psf-os allocate.mask).
  Each: h = 0, 0.05, 0.1, 0.15 (one record each, t = 0..10, N = 21, X readout of every site), then the sentinel
  (the rule's echo, D = 24, on the same n = 40 ring). 4000 shots. Every manifest says "stay".

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/du_repro.py FETCH_DIR REGISTRY.json OUT_DIR [--dry-clifford-sentinel]
"""
import datetime as dt
import json
import os
import pickle
import sys
from zoneinfo import ZoneInfo

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
N, TMAX, HS, SHOTS, RING = 21, 10, (0.0, 0.05, 0.1, 0.15), 4000, 40
if os.path.exists(OUT):
    raise SystemExit(f"STOP: {OUT} exists")
f = json.load(open(os.path.join(FETCH, "fetch.json")))
target = pickle.load(open(os.path.join(FETCH, "target.pkl"), "rb"))
dev = Dv.from_target(target, f["backend"], source=dict(fetch=f.get("fetched"), target_sha256=f.get("target_sha256")))
reg = R.load(REG)
now = dt.datetime.now(ZoneInfo("Europe/Zurich")).replace(tzinfo=None, microsecond=0)
avoid = R.avoid_paths(reg, dev.name, now)  # LISTED entries (valid 7 days); no same-day scan is required by the note
log = dict(dry_clifford_sentinel=DRY, fetch=f, registry=REG, registry_sha256=R.sha256_file(REG),
           now=now.isoformat(sep=" "), avoided=[a["path"] for a in avoid], N=N, t_max=TMAX, h=list(HS), shots=SHOTS,
           jobs={})


def ring_of(d, rc):
    """The rule's n = 40 ring on the device record: ring site j -> physical qubit (a one-layer model circuit)."""
    import numpy as np
    ang = list(np.zeros(C.n_model_angles(RING, 1)))
    mq = measured_qubits(rc.compile(C.model_circuit(ang, RING, 1)))
    return [int(mq[j]) for j in range(RING)]


def make(d, tag):
    rc = RuleCompiler(d)
    ring = ring_of(d, rc)
    runs = os.path.join(OUT, tag, "runs")
    for h in HS:
        rec = DU.build(d, dict(N=N, h=h, t_max=TMAX, shots=SHOTS), runs, ring, compiler=rc)
        if not rec["valid"]:
            raise SystemExit(f"STOP: {tag} h = {h} not accepted: {rec['echo']['q2_circuits']}")
    sentinel.build(d, runs, ring, SHOTS, rc, spec=SPEC)
    man = J.assemble(d, runs, os.path.join(OUT, tag, "job"), max_seconds=60)
    assert man.get("stay") is True
    return ring, man


ring_s, man_s = make(dev, "S")
dev_v, masked = A.mask(dev, avoid, reason=f"registry at {now.isoformat(sep=' ')}")
ring_v, man_v = make(dev_v, "V")
for tag, ring, man in (("S", ring_s, man_s), ("V", ring_v, man_v)):
    chain = ring[:N]
    log["jobs"][tag] = dict(ring=ring, chain=chain, circuits=len(man["pubs"]), qpu_seconds_model=man["qpu_seconds_model"],
                            circuits_sha256=man["circuits_sha256"],
                            listed_paths_on_chain=[a["path"] for a in avoid if all(q in chain for q in a["path"])])
log["masked_couplers"] = [list(e) for e in masked]
json.dump(log, open(os.path.join(OUT, "build.json"), "w"), indent=1)
for tag in ("S", "V"):
    j = log["jobs"][tag]
    print(f"job {tag}: {j['circuits']} circuits, {j['qpu_seconds_model']} s by the time model, chain {j['chain']}, "
          f"listed paths on the chain {j['listed_paths_on_chain']}")
print("masked", log["masked_couplers"])
