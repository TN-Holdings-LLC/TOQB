"""Prepare one night of the daily record (prereg/daily/standing_rules.md): copy the night's circuits and write the
answers file {tag: {label: exact <Z>}} from the sealed and released sources.

  FX-A: results/bank-2026-11-04/pod/du_bank/answers.json (sealed 11-04), x at t 12 on the chain of the practice test
  D02, D03, ...: results/daily-pool-2026-11-05/released/<ID>.json (hashes committed in 12164be, released in 50e412e)

usage: python gpu/daily_night.py OUT_DIR ID [ID ...]
"""
import json
import os
import shutil
import sys

POOL = "results/daily-pool-2026-11-05"
CHAIN = list(range(0, 16)) + [19] + list(range(35, 19, -1))


def answers_for(pid):
    if pid == "FX-A":
        x = json.load(open("results/bank-2026-11-04/pod/du_bank/answers.json"))["h0.15_b0.485398"]["x"][12]
        return {str(CHAIN[k]): float(x[k]) for k in range(len(CHAIN))}
    v = json.load(open(f"{POOL}/released/{pid}.json"))
    if v.get("failed"):
        raise SystemExit(f"{pid}: answer marked failed")
    return {str(k): float(z) for k, z in v["values"].items()}


def main(out, ids):
    if os.path.exists(out):
        raise SystemExit(f"STOP: {out} exists")
    os.makedirs(os.path.join(out, "circuits"))
    for pid in ids:
        shutil.copy(f"{POOL}/circuits/{pid}.qpy", os.path.join(out, "circuits", f"{pid}.qpy"))
    json.dump({pid: answers_for(pid) for pid in ids}, open(os.path.join(out, "answers.json"), "w"))
    print(f"{len(ids)} circuits and answers.json written to {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
