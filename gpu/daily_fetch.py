"""Daily record, step 1 at home (VPN OFF): read the queue (pending jobs only) of ibm_marrakesh, ibm_fez, ibm_kingston,
choose the night's devices by the standing rule (every device with at most 10 pending jobs; if none, the one with
the fewest; ties in that order), then `psf-os fetch` each into OUT_BASE/<device>/dev.

Uses the saved IBM account only; reads no key and no quality number. Run from ~/toqb_push_2026-10-15.
usage: python daily_fetch_2026-11-05.py OUT_BASE
"""
import datetime as dt
import json
import os
import subprocess
import sys

from qiskit_ibm_runtime import QiskitRuntimeService

ORDER = ["ibm_marrakesh", "ibm_fez", "ibm_kingston"]
LIMIT = 10
base = sys.argv[1]
if os.path.exists(base):
    raise SystemExit(f"STOP: {base} exists")
svc = QiskitRuntimeService()
q = {n: svc.backend(n).status().pending_jobs for n in ORDER}
chosen = [n for n in ORDER if q[n] <= LIMIT] or [min(ORDER, key=lambda n: (q[n], ORDER.index(n)))]
os.makedirs(base)
json.dump(dict(pending=q, read=dt.datetime.now(dt.timezone.utc).isoformat(), limit=LIMIT, chosen=chosen),
          open(os.path.join(base, "queue.json"), "w"), indent=1)
print("queue", q, "-> chosen", chosen)
for n in chosen:
    subprocess.run([sys.executable, "-m", "psf_os", "fetch", "--backend", n, "--out", os.path.join(base, n, "dev")],
                   check=True)
print("fetched:", ", ".join(chosen))
