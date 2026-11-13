"""Answers of the Clifford twins in a job built with user2d.build_batch(..., twin=True) (home, 2026-11-13).
For each user tag, the twin run p2d_<tag>_twin.qpy is read back and its per-qubit <Z> computed exactly by stabilizer
simulation (psf_os.twin.z_exact), keyed by chain label like the user answers. Written to its own file; hash printed."""
import ast
import hashlib
import json
import os


def twin_answers(out, tags, ans_path):
    from qiskit import qpy
    from psf_os import twin as TW
    runs = os.path.join(out, "runs")
    res = {}
    for tag in tags:
        rec = json.load(open(os.path.join(runs, f"p2d_{tag}_twin.json")))
        m = rec["mapping"] if isinstance(rec["mapping"], dict) else ast.literal_eval(rec["mapping"])
        labels = rec["labels"]
        ct = qpy.load(open(os.path.join(runs, f"p2d_{tag}_twin.qpy"), "rb"))[0]
        z = TW.z_exact(ct, [int(m[str(q)]) for q in labels])
        res[tag] = {str(q): float(v) for q, v in zip(labels, z)}
    if os.path.exists(ans_path):
        raise SystemExit(f"STOP: {ans_path} exists")
    json.dump(res, open(ans_path, "w"), indent=1, sort_keys=True)
    print("twin answers sha256", hashlib.sha256(open(ans_path, "rb").read()).hexdigest())
    return res
