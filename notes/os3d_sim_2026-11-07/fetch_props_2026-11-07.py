"""Save the calibration (BackendProperties) of ibm_fez at the time this morning's job ran, for the device-like
simulator only (it is not used by any placement, build or verdict). Home, VPN OFF. Reads, submits nothing.

usage: python fetch_props_2026-11-07.py OUT.json
"""
import json
import os
import sys

from qiskit_ibm_runtime import QiskitRuntimeService

out = sys.argv[1]
if os.path.exists(out):
    raise SystemExit(f"STOP: {out} exists")
svc = QiskitRuntimeService()
props = svc.job("dbn5m0lt7fqc73aivqa0").properties()
if props is None:
    raise SystemExit("STOP: the job has no properties")
json.dump(props.to_dict(), open(out, "w"), default=str)
print("saved", out, "calibrated", props.last_update_date, "qubits", len(props.qubits))
