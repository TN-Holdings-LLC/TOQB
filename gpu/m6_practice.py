"""OS plan M6 and practice problems on a device (prereg/drafts-2026-11-02/m6_practice_note.md): builds three job folders
with psf-os's own functions, from one fetch and the day's registry. CPU only; nothing is submitted here.

  Job S (standard n = 40 ring): sh6 (D = 12) and cluster_parity, then the sentinel on the same ring.
  Job V (n = 40 ring placed around the registry): the same two user records, then the sentinel.
  Job P (standard n = 20 ring): kising_forward (hz 0, h 0.3) at L = 4 and L = 8.

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/m6_practice.py FETCH_DIR REGISTRY.json OUT_DIR [--dry-clifford-sentinel]
(--dry-clifford-sentinel: dry runs only; the sentinel at the echo's Clifford point, so that a laptop can simulate it)
Every manifest says "stay": true (TOQB s2rc_device submit never moves these jobs)."""
import datetime as dt
import json
import os
import pickle
import sys
from zoneinfo import ZoneInfo

from psf_os import allocate as A
from psf_os import device as Dv
from psf_os import job as J
from psf_os import registry as R
from psf_os import sentinel
from psf_os.compile import RuleCompiler

FETCH, REG, OUT = sys.argv[1:4]
DRY = "--dry-clifford-sentinel" in sys.argv
SPEC = dict(kind="echo_clifford", D=24) if DRY else None
if os.path.exists(OUT):
    raise SystemExit(f"STOP: {OUT} exists")
f = json.load(open(os.path.join(FETCH, "fetch.json")))
target = pickle.load(open(os.path.join(FETCH, "target.pkl"), "rb"))
dev = Dv.from_target(target, f["backend"], source=dict(fetch=f.get("fetched"), target_sha256=f.get("target_sha256")))
reg = R.load(REG)
# the registry is read at build time, in CET (records are in CET), as gpu/defect_days.sh does
now = dt.datetime.now(ZoneInfo("Europe/Zurich")).replace(tzinfo=None, microsecond=0)
if R.is_stale(reg, dev.name, now):
    raise SystemExit(f"STOP: the registry holds no scan of {dev.name} on {now.date()}")
avoid = R.avoid_paths(reg, dev.name, now)
SHOTS = 1000
log = dict(dry_clifford_sentinel=DRY, fetch=f, registry=REG, registry_sha256=R.sha256_file(REG), now=now.isoformat(sep=" "),
           avoided=[a["path"] for a in avoid], jobs={})


def user_and_sentinel(d, tag):
    rc = RuleCompiler(d)
    runs = os.path.join(OUT, tag, "runs")
    rings = []
    for job in (dict(kind="sh6", n=40, D=12, shots=SHOTS), dict(kind="cluster_parity", n=40, shots=SHOTS)):
        rec = J.build(d, job, runs, compiler=rc)
        if not rec["echo"]["accepted"]:
            raise SystemExit(f"STOP: {tag} {job['kind']} not accepted")
        mq = rec["echo"]["measured_qubits"]
        rings.append([int(mq[str(j)]) for j in range(40)])
    if rings[0] != rings[1]:
        raise SystemExit(f"STOP: {tag}: the two user records are on different rings")
    sentinel.build(d, runs, rings[0], SHOTS, rc, spec=SPEC)
    man = J.assemble(d, runs, os.path.join(OUT, tag, "job"), max_seconds=30)
    return rings[0], man


ring_s, man_s = user_and_sentinel(dev, "S")
dev_v, masked = A.mask(dev, avoid, reason=f"registry at {now.isoformat(sep=' ')}")
ring_v, man_v = user_and_sentinel(dev_v, "V")
rc = RuleCompiler(dev)
runs_p = os.path.join(OUT, "P", "runs")
ring_p = None
for L in (4, 8):
    rec = J.build(dev, dict(kind="kising_forward", n=20, L=L, h=0.3, shots=SHOTS), runs_p, compiler=rc)
    if not rec["echo"]["accepted"]:
        raise SystemExit(f"STOP: P L = {L} not accepted")
    mq = rec["echo"]["measured_qubits"]
    r = [int(mq[str(j)]) for j in range(20)]
    if ring_p not in (None, r):
        raise SystemExit("STOP: P's two records are on different rings")
    ring_p = r
man_p = J.assemble(dev, runs_p, os.path.join(OUT, "P", "job"), max_seconds=30)
for tag, ring, man in (("S", ring_s, man_s), ("V", ring_v, man_v), ("P", ring_p, man_p)):
    assert man.get("stay") is True
    log["jobs"][tag] = dict(ring=ring, circuits=len(man["pubs"]), qpu_seconds_model=man["qpu_seconds_model"],
                            circuits_sha256=man["circuits_sha256"])
log["masked_couplers"] = [list(e) for e in masked]
log["listed_path_on_S"] = [a["path"] for a in avoid if all(q in ring_s for q in a["path"])]
log["listed_path_on_V"] = [a["path"] for a in avoid if all(q in ring_v for q in a["path"])]
json.dump(log, open(os.path.join(OUT, "build.json"), "w"), indent=1)
for tag in ("S", "V", "P"):
    j = log["jobs"][tag]
    print(f"job {tag}: {j['circuits']} circuits, {j['qpu_seconds_model']} s by the time model, ring {j['ring'][:6]}...")
print("masked", log["masked_couplers"], "| listed paths on S", log["listed_path_on_S"], "| on V", log["listed_path_on_V"])
