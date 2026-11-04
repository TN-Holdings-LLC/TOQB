"""SPD for P6 (the Qedma tutorial patch, theta_x 0.53, theta_z 0.1, theta_zz 1.0) against the sealed exact answers
(results/p6-answers-2026-11-04: CPU t <= 5, pod t = 6..9). Not declared; a workplace check of rust/spd's layered mode.

usage: PYTHONPATH=<psf-os> python spd_p6_check.py OUT_JSONL --deltas 1e-3,3e-4,1e-4 [--ts 1,...,9] [--threads 2]
"""
import argparse
import json
import os
import subprocess
import tempfile
import time

from psf_os import ising2d as I

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RES = os.path.join(ROOT, "results", "p6-answers-2026-11-04")
BIN = os.path.join(ROOT, "rust", "spd", "target", "release", "spd_layers")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--deltas", required=True)
    ap.add_argument("--ts", default="1,2,3,4,5,6,7,8,9")
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--cap", type=int, default=12_000_000)
    a = ap.parse_args()
    cpu = json.load(open(os.path.join(RES, "answers_cpu.json")))
    gpu = json.load(open(os.path.join(RES, "gpu", "answers_gpu.json")))
    qs = I.QUBITS
    fd, spec = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w") as f:
        f.write(f"rx {I.THETA_X!r} " + " ".join(map(str, qs)) + "\n")
        f.write(f"rz {I.THETA_Z!r} " + " ".join(map(str, qs)) + "\n")
        for L in I.LAYERS:
            f.write(f"rzz {I.THETA_ZZ!r} " + " ".join(f"{x}-{y}" for x, y in L) + "\n")
    for t in [int(x) for x in a.ts.split(",")]:
        if cpu["qubits"] != qs:
            raise RuntimeError("answers on another qubit order")
        ex = cpu["answers"][str(t)] if str(t) in cpu["answers"] else gpu[str(t)]["z"]
        for delta in [float(x) for x in a.deltas.split(",")]:
            t0 = time.time()
            out = subprocess.run([BIN, spec, str(t), repr(delta), ",".join(map(str, qs)), str(a.threads), str(a.cap)],
                                 capture_output=True, text=True, check=True).stdout
            v = {}
            for line in out.split("\n"):
                if line.strip():
                    q, z, peak, sec, cap = line.split()
                    v[int(q)] = (float(z), int(peak), float(sec), cap == "1")
            rec = dict(t=t, delta=delta, wall=round(time.time() - t0, 1), qubits=qs, z=[v[q][0] for q in qs],
                       peak=[v[q][1] for q in qs], capped=[v[q][3] for q in qs], exact=ex)
            with open(a.out, "a") as f:
                f.write(json.dumps(rec) + "\n")
            ok = [i for i, e in enumerate(ex) if e is not None and not rec["capped"][i]]
            err = [abs(rec["z"][i] - ex[i]) for i in ok]
            ms, me = sum(rec["z"][i] for i in ok) / len(ok), sum(ex[i] for i in ok) / len(ok)
            print(f"P6 t {t} delta {delta:g}: {len(ok)} qubits, M spd {ms:.5f} exact {me:.5f} (|dM| {abs(ms - me):.5f}), "
                  f"max err {max(err):.4f}, peak {max(rec['peak'])}, wall {rec['wall']:.0f} s", flush=True)
    os.remove(spec)


if __name__ == "__main__":
    main()
