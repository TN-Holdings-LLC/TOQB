"""Drive rust/spd (sparse Pauli dynamics) for P5's lattice b and compare with the sealed exact answers.

Not declared; a workplace check (2026-11-04). Phases:
  t5    t = 5, every qubit, against results/kim-cd-2026-11-03/answers_cpu.json (lattice b)
  t678  t = 6, 7, 8, the answered qubits, against answers_pod/answers_C.json
  t20   t = 20, every qubit (or every k-th with --stride), no exact answer
Each (phase, theta, t, delta) appends one JSON line to OUT_JSONL with per-qubit values, peaks, seconds.

Usage: python spd_check.py PHASE OUT_JSONL --deltas 1e-3,3e-4,1e-4 [--thetas 0.4,0.8,1.0] [--stride 1]
       [--threads 2] [--cap 60000000]
"""
import argparse
import json
import os
import subprocess
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RES = os.path.join(ROOT, "results", "kim-cd-2026-11-03")
BIN = os.path.join(ROOT, "rust", "spd", "target", "release", "spd")


def run(edges_file, theta, t, delta, qubits, threads, cap):
    t0 = time.time()
    out = subprocess.run([BIN, edges_file, repr(theta), str(t), repr(delta), ",".join(map(str, qubits)), str(threads),
                          str(cap)], capture_output=True, text=True, check=True).stdout
    vals = {}
    for line in out.split("\n"):
        if line.strip():
            q, v, peak, sec, capped = line.split()
            vals[int(q)] = dict(z=float(v), peak=int(peak), s=float(sec), capped=bool(int(capped)))
    return vals, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["t5", "t678", "t20"])
    ap.add_argument("out")
    ap.add_argument("--deltas", required=True)
    ap.add_argument("--thetas", default="0.4,0.8,1.0")
    ap.add_argument("--ts", default=None)
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--cap", type=int, default=60_000_000)
    a = ap.parse_args()
    lat = json.load(open(os.path.join(RES, "lattice.json")))
    qubits, edges = lat["qubits"], lat["edges"]
    fd, ef = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w") as f:
        f.write("".join(f"{x} {y}\n" for x, y in edges))
    cpu = json.load(open(os.path.join(RES, "answers_cpu.json")))["answers"]["b"]
    pod = json.load(open(os.path.join(RES, "answers_pod", "answers_C.json")))
    ts = [int(x) for x in a.ts.split(",")] if a.ts else {"t5": [5], "t678": [6, 7, 8], "t20": [20]}[a.phase]
    for theta in [float(x) for x in a.thetas.split(",")]:
        key = f"{theta:.6f}"
        for t in ts:
            if a.phase == "t5":
                exact = cpu[key][str(t)]["z"]
            elif a.phase == "t678":
                exact = pod[key][str(t)]["z"]
            else:
                exact = [None] * len(qubits)
            sel = [j for j, q in enumerate(qubits) if (exact[j] is not None or a.phase == "t20")][::a.stride]
            for delta in [float(x) for x in a.deltas.split(",")]:
                vals, wall = run(ef, theta, t, delta, [qubits[j] for j in sel], a.threads, a.cap)
                rec = dict(phase=a.phase, theta=theta, t=t, delta=delta, wall=round(wall, 1), qubits=[qubits[j] for j in sel],
                           z=[vals[qubits[j]]["z"] for j in sel], peak=[vals[qubits[j]]["peak"] for j in sel],
                           sec=[vals[qubits[j]]["s"] for j in sel], capped=[vals[qubits[j]]["capped"] for j in sel],
                           exact=[exact[j] for j in sel])
                with open(a.out, "a") as f:
                    f.write(json.dumps(rec) + "\n")
                ok = [i for i, e in enumerate(rec["exact"]) if e is not None and not rec["capped"][i]]
                msg = f"{a.phase} theta {theta} t {t} delta {delta:g}: {len(sel)} qubits, wall {wall:.0f} s, peak {max(rec['peak'])}"
                if ok:
                    err = [abs(rec["z"][i] - rec["exact"][i]) for i in ok]
                    m_spd = sum(rec["z"][i] for i in ok) / len(ok)
                    m_ex = sum(rec["exact"][i] for i in ok) / len(ok)
                    msg += f", max err {max(err):.4f}, M spd {m_spd:.4f} exact {m_ex:.4f}"
                else:
                    good = [z for z, c in zip(rec["z"], rec["capped"]) if not c]
                    msg += f", M {sum(good) / max(1, len(good)):.4f} ({sum(rec['capped'])} capped)"
                print(msg, flush=True)
    os.remove(ef)


if __name__ == "__main__":
    main()
