"""Sealing of the daily pool (task T, addendum A) and the circuits for anyone to recompute (addendum C).

  seal      raw answer files of gpu/daily_answers.py (pod) -> SEALED/<ID>.json and SEALED/answers.json, each written as
            json.dumps(obj, sort_keys=True, separators=(",", ":")) and one newline; and RESULTS/sha256.txt (one line per
            file). The values are not committed: results/daily-pool-2026-11-05/sealed/ and answers.json are in
            .gitignore; only sha256.txt goes into git.
  redact    a pod log without the lines that carry answer values (M, |<.>|), for the commit; the full log stays sealed.
  circuits  every problem's circuit with its measurements as RESULTS/circuits/<ID>.qpy and <ID>.qasm (OpenQASM 3).

usage: python daily/seal.py seal SEALED_DIR RESULTS_DIR RAW.json [RAW.json ...]
       python daily/seal.py seal-add SEALED_DIR RESULTS_DIR NAME RAW.json [RAW.json ...]   (a later day's problems)
       python daily/seal.py redact IN.txt OUT.txt
       python daily/seal.py circuits RESULTS_DIR
       python daily/seal.py leakcheck SEALED_DIR [FILE ...]   (no files: the files staged for the next commit)

  leakcheck  before every commit: no sealed value (every <Z>/<X> and M, as 4 decimals, rounded and cut) may appear in
            a text file to be committed; exit 1 and the hits if one does.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from daily import pool as P  # noqa: E402

REQUIRED_IDS = [e[0] for e in P.POOL] + ["FX-B"]
SEALED_IDS = REQUIRED_IDS + [e[0] for e in P.SCALE + P.HARD]  # S01-S06, H01-H03 when computed (sealed on their own day otherwise)
CIRCUIT_IDS = [e[0] for e in P.POOL + P.FIXED + P.SCALE + P.HARD]
VALUE_LINE = re.compile(r"(\bM [+-]|M over them|\|<\.>\||^(D\d\d|FX-[AB]|S\d\d|H\d\d): )")


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n"


def record(pid, raw):
    _, fam, pa, par, t, layers, g = P.entry(pid)
    vals = {str(q): v for q, v in raw["values"].items()}
    labels = [str(q) for q in P.patch(pa)[0]]
    if sorted(vals) != sorted(labels):
        raise RuntimeError(f"{pid}: the values are not the patch's labels")
    done = [v for v in vals.values() if v is not None]
    rec = dict(id=pid, family=fam, patch=pa, labels=[int(x) for x in labels], params=par,
               params_text=P.params_text(par), t=t, cz_layers=layers, grade=g, readout=P.READOUT[fam],
               method=raw["method"], failed=bool(raw["failed"]), values=vals,
               M=float(np.mean(done)) if done else None)
    if "cone" in raw:
        rec["cone"] = {str(q): c for q, c in raw["cone"].items()}
    return rec


def seal(sealed, results, raws):
    merged = {}
    for f in raws:
        for pid, r in json.load(open(f)).items():
            if pid in merged:
                raise RuntimeError(f"{pid} in two raw files")
            merged[pid] = r
    missing = [p for p in REQUIRED_IDS if p not in merged]
    if missing:
        raise RuntimeError(f"no answer for {missing}")
    os.makedirs(sealed, exist_ok=True)
    lines, allrec = [], {}
    for pid in [p for p in SEALED_IDS if p in merged]:
        rec = record(pid, merged[pid])
        allrec[pid] = rec
        text = canonical(rec)
        open(os.path.join(sealed, f"{pid}.json"), "w", newline="\n").write(text)
        lines.append(f"{hashlib.sha256(text.encode()).hexdigest()}  sealed/{pid}.json")
    text = canonical(allrec)
    open(os.path.join(sealed, "answers.json"), "w", newline="\n").write(text)
    lines.append(f"{hashlib.sha256(text.encode()).hexdigest()}  answers.json")
    open(os.path.join(results, "sha256.txt"), "w", newline="\n").write("\n".join(lines) + "\n")
    return lines


def seal_add(sealed, results, name, raws):
    """Problems sealed on a later day (S01-S06, H01-H03): SEALED/<ID>.json for each, SEALED/answers_<name>.json for
    them together, and their lines appended to RESULTS/sha256.txt. The lines already there (the 11-05 seal and its
    answers.json) are left as they are; a problem already in sha256.txt is refused."""
    merged = {}
    for f in raws:
        for pid, r in json.load(open(f)).items():
            if pid in merged:
                raise RuntimeError(f"{pid} in two raw files")
            merged[pid] = r
    path = os.path.join(results, "sha256.txt")
    old = open(path).read()
    for pid in merged:
        if pid not in SEALED_IDS or pid in REQUIRED_IDS:
            raise RuntimeError(f"{pid}: not a problem sealed on a later day")
        if f"  sealed/{pid}.json\n" in old:
            raise RuntimeError(f"{pid} is sealed already")
    os.makedirs(sealed, exist_ok=True)
    lines, allrec = [], {}
    for pid in [p for p in SEALED_IDS if p in merged]:
        rec = record(pid, merged[pid])
        allrec[pid] = rec
        text = canonical(rec)
        open(os.path.join(sealed, f"{pid}.json"), "w", newline="\n").write(text)
        lines.append(f"{hashlib.sha256(text.encode()).hexdigest()}  sealed/{pid}.json")
    text = canonical(allrec)
    open(os.path.join(sealed, f"answers_{name}.json"), "w", newline="\n").write(text)
    lines.append(f"{hashlib.sha256(text.encode()).hexdigest()}  sealed/answers_{name}.json")
    open(path, "w", newline="\n").write(old + "\n".join(lines) + "\n")
    return lines


def redact(src, dst):
    keep = [ln for ln in open(src).read().splitlines() if not VALUE_LINE.search(ln)]
    open(dst, "w", newline="\n").write("\n".join(keep) + "\n")


def circuits(results):
    from qiskit import qasm3, qpy
    d = os.path.join(results, "circuits")
    os.makedirs(d, exist_ok=True)
    for pid in CIRCUIT_IDS:
        qc = P.problem_circuit(pid)
        qc.name = pid
        with open(os.path.join(d, pid + ".qpy"), "wb") as f:
            qpy.dump(qc, f)
        open(os.path.join(d, pid + ".qasm"), "w", newline="\n").write(qasm3.dumps(qc))
    return len(CIRCUIT_IDS)


def leakcheck(sealed, files):
    """[(file, value string)] of the sealed values (4 decimals, rounded or cut, sign ignored) found in the files."""
    import math
    vals = set()
    for rec in json.load(open(os.path.join(sealed, "answers.json"))).values():
        for v in list(rec["values"].values()) + [rec.get("M")]:
            if v is None:
                continue
            a = abs(v)
            vals.add(f"{a:.4f}")
            vals.add(f"{math.floor(a * 1e4) / 1e4:.4f}")
    pat = re.compile(r"(?<![0-9.])(" + "|".join(re.escape(x) for x in sorted(vals)) + r")")
    hits = []
    for f in files:
        try:
            text = open(f, encoding="utf-8").read()
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue  # binary (QPY) or removed
        hits += [(f, m.group(1)) for m in pat.finditer(text)]
    return hits


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "seal":
        print("\n".join(seal(sys.argv[2], sys.argv[3], sys.argv[4:])))
    elif cmd == "seal-add":
        print("\n".join(seal_add(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])))
    elif cmd == "redact":
        redact(sys.argv[2], sys.argv[3])
    elif cmd == "leakcheck":
        import subprocess
        fs = sys.argv[3:] or subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=d"],
                                            capture_output=True, text=True).stdout.split()
        h = leakcheck(sys.argv[2], fs)
        for f, v in h:
            print(f"LEAK {f}: {v}")
        print(f"leakcheck: {len(fs)} files, {len(h)} hits")
        sys.exit(1 if h else 0)
    elif cmd == "circuits":
        print(circuits(sys.argv[2]), "circuits written")
    else:
        raise SystemExit(__doc__)
