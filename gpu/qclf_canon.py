"""Placement-free hash of a classifier build (home, 2026-11-11): every user circuit, floor and mirror of OUT/runs
re-labelled from physical qubits to classical-bit order (the measured map), gate names and parameters (rounded to
1e-12) and the relabelled qubits serialised in order, then sha256. Two builds with the same canonical hash run the
same gates on the same logical qubits in the same order, so qclf_check.py's noiseless result (which reduces each
circuit to its active qubits and reads the bits by the measured map) is the same for both. Used tonight as: a build
whose canonical hash equals that of a build whose check PASSED carries that PASS; otherwise the full check runs.
Refuses (exit 2) a circuit with an active qubit that is not measured.
usage: python gpu/qclf_canon.py OUT [OUT2 ...]
"""
import gzip
import hashlib
import os
import sys


def circuits(path):
    from qiskit import qpy
    if os.path.exists(path):
        return qpy.load(open(path, "rb"))
    return qpy.load(gzip.open(path + ".gz", "rb"))


def canon(out):
    from qiskit.circuit import Parameter  # noqa: F401
    h = hashlib.sha256()
    n = 0
    for stem in ("q_a_rule", "q_a_rule_floor", "q_a_rule_mirror"):
        for c in circuits(os.path.join(out, "runs", stem + ".qpy")):
            mm = {c.find_bit(i.qubits[0]).index: c.find_bit(i.clbits[0]).index
                  for i in c.data if i.operation.name == "measure"}           # physical -> clbit
            for ins in c.data:
                if ins.operation.name in ("barrier", "delay"):
                    continue
                qs = []
                for q in ins.qubits:
                    p = c.find_bit(q).index
                    if p not in mm:
                        raise SystemExit(f"REFUSED: {stem}: active qubit {p} is not measured")
                    qs.append(mm[p])
                ps = [f"{float(x):.12f}" for x in ins.operation.params]
                h.update(f"{ins.operation.name}|{','.join(ps)}|{','.join(map(str, qs))};".encode())
            h.update(b"#")
            n += 1
    return h.hexdigest(), n


if __name__ == "__main__":
    for o in sys.argv[1:]:
        d, n = canon(o)
        print(f"{o}: {n} circuits, canonical sha256 {d}")
