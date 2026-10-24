"""Does PSF-Zero a24 build the same circuits as TOQB's arms on a22? Analysis for the a24 switch (2026-10-24):

    python -m toqb.zip_a24_check OUT.json [--item31] [--n 10 12 14 16] [--L 8 16 24 32]

Default: a24's zipper (PSF_RING_ZIP=1, Rust ring r2) against TOQB's report-only `psfai:template_zip` (a22 with
toqb.ring_zip, Python). With --item31: a24's default template (Rust ring r2, no zipper) against `psfai:template` on
a22 / c61 (Python).

Runs itself twice in subprocesses (the two front ends cannot share one process: both register module names) and
compares, per (n, L), the compiled circuit of one random model instruction by instruction (name, physical qubits,
parameters to 1e-9), plus CZ count and duration. Needs $PSF_ZERO_REPO.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import numpy as np


def build(side, ns, Ls):
    from toqb import s2r as S
    from toqb import task_loop as TL
    from toqb.devices import get_device
    device = get_device("snapshot:marrakesh")
    zip_mode = os.environ.get("TOQB_ZIPCHECK_ITEM31") != "1"
    arm = S.Arm("psfai:template_zip" if (side == "toqb" and zip_mode) else "psfai:template", device)
    rng = np.random.default_rng(20261024)
    out = {}
    for n in ns:
        for L in Ls:
            theta = rng.uniform(-1, 1, TL.n_params(n, L))
            x = rng.uniform(-1, 1, n)
            qc = TL.model_circuit(TL.angle_list(theta, x, n, L, np.pi / 2), n, L)
            try:
                c = arm.compile(qc)
                d, q2 = arm.duration(c, (n, L))
                ops = [[i.operation.name, [c.find_bit(q).index for q in i.qubits],
                        [float(p) for p in i.operation.params]] for i in c.data]
                out[f"{n},{L}"] = dict(q2=int(q2), duration_us=round(d * 1e6, 4), ops=ops)
            except Exception as exc:
                out[f"{n},{L}"] = dict(error=f"{type(exc).__name__}: {exc}"[:300])
    return out


def same(a, b):
    if "error" in a or "error" in b:
        return False, "error"
    if len(a["ops"]) != len(b["ops"]):
        return False, f"{len(a['ops'])} against {len(b['ops'])} instructions"
    for k, (x, y) in enumerate(zip(a["ops"], b["ops"])):
        if x[0] != y[0] or x[1] != y[1] or len(x[2]) != len(y[2]) or any(abs(p - q) > 1e-9 for p, q in zip(x[2], y[2])):
            return False, f"first difference at instruction {k}: {x} against {y}"
    return True, ""


def main(argv):
    argv = list(argv)
    if len(argv) >= 2 and argv[0] == "--side":
        side, path, ns, Ls = argv[1], argv[2], json.loads(argv[3]), json.loads(argv[4])
        json.dump(build(side, ns, Ls), open(path, "w"))
        return 0
    if not argv:
        print(__doc__)
        return 1
    out = argv.pop(0)
    item31 = "--item31" in argv
    if item31:
        argv.remove("--item31")
    ns = [10, 12, 14, 16]
    Ls = [8, 16, 24, 32]
    if "--n" in argv:
        i = argv.index("--n"); j = argv.index("--L") if "--L" in argv and argv.index("--L") > i else len(argv)
        ns = [int(v) for v in argv[i + 1:j]]
    if "--L" in argv:
        i = argv.index("--L"); j = argv.index("--n") if "--n" in argv and argv.index("--n") > i else len(argv)
        Ls = [int(v) for v in argv[i + 1:j]]
    repo = os.environ["PSF_ZERO_REPO"]
    env_t = dict(os.environ, PSF_COMPILE_FILE=os.path.join(repo, "patches/psf_compile_c61_2026-10-15/psf_compile.py"),
                 PSF_AI_FILE=os.path.join(repo, "patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"))
    env_t.pop("TOQB_RUST_TEMPLATE", None)
    env_a = dict(os.environ, PSF_COMPILE_FILE=os.path.join(repo, "psf_compile.py"),
                 PSF_AI_FILE=os.path.join(repo, "patches/psf_ai_compile_a24_2026-10-22/psf_ai_compile.py"),
                 PSF_BIND_LIB=os.path.join(repo, "rust/psfbind/target/release/libpsfbind.so"))
    env_a.pop("TOQB_RUST_TEMPLATE", None)
    if item31:
        env_t["TOQB_ZIPCHECK_ITEM31"] = env_a["TOQB_ZIPCHECK_ITEM31"] = "1"
        env_a.pop("PSF_RING_ZIP", None)
    else:
        env_a["PSF_RING_ZIP"] = "1"
    res = {}
    for side, env in (("toqb", env_t), ("a24", env_a)):
        path = out + f".{side}.json"
        subprocess.run([sys.executable, "-m", "toqb.zip_a24_check", "--side", side, path, json.dumps(ns),
                        json.dumps(Ls)], env=env, check=True)
        res[side] = json.load(open(path))
        os.remove(path)
    rows = []
    for key in res["toqb"]:
        ok, why = same(res["toqb"][key], res["a24"][key])
        t, a = res["toqb"][key], res["a24"][key]
        rows.append(dict(nL=key, identical=ok, why=why, toqb=[t.get("q2"), t.get("duration_us"), t.get("error")],
                         a24=[a.get("q2"), a.get("duration_us"), a.get("error")]))
        print(json.dumps(rows[-1]))
    json.dump(rows, open(out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
