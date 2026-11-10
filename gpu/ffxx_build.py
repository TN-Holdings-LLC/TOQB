"""Try-build of the XX-chain ruler (gpu/ff_xx.py) through psf-os's user entrance (home, 2026-11-10; prototype, not
declared). The chain: the shape rule of daily/du91 first, else rule C (psf_os.chain.place), as du91; the user circuit
is gpu/ff_xx's brickwork written on the chain's labels (site i on label chain[i]), no measurement (the entrance
measures every touched qubit in label order); one job, each circuit with its floor and mirror, one ring sentinel.
Answers: the free-fermion <Z> of each site on its label.

usage: PYTHONPATH=<psf-os>:<TOQB>:<TOQB>/gpu python gpu/ffxx_build.py DEV_DIR OUT ANSWERS_OUT [--n 91]
       [--thetas 1.5707963267948966,0.25] [--steps 4,8,12] [--max-seconds 120]
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ff_xx as F  # noqa: E402
from daily import du91 as X  # noqa: E402


def chain_for(dev, n):
    pl = X.place(dev, n)
    if pl["shape"] is not None:
        sh = next(s for s in X.SHAPES if s[0] == pl["shape"])
        return dict(rule="shape " + pl["shape"], chain=list(X.snake(n, sh)))
    from psf_os import chain as CH
    c = CH.place(dev, n)
    return dict(rule="C", chain=list(c["chain"]), start=c["start"], steps=c["steps"])


def circuit_on(labels, width, steps, theta):
    from qiskit import QuantumCircuit
    logical = F.circuit(len(labels), steps, theta, measure=False)
    qc = QuantumCircuit(width)
    qc.compose(logical, qubits=list(labels), inplace=True)
    return qc


def tag(theta, steps):
    return f"xx_th{int(round(theta * 1000)):04d}_s{steps:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dev_dir")
    ap.add_argument("out")
    ap.add_argument("answers_out")
    ap.add_argument("--n", type=int, default=91)
    ap.add_argument("--thetas", default="1.5707963267948966,0.25")
    ap.add_argument("--steps", default="4,8,12")
    ap.add_argument("--max-seconds", type=float, default=120)
    a = ap.parse_args()
    for p in (a.out, a.answers_out):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    from psf_os import device as Dv
    from psf_os import user2d as U
    dev = Dv.Device.load(a.dev_dir)
    ch = chain_for(dev, a.n)
    labels = ch["chain"]
    items, answers = [], {}
    for th in [float(v) for v in a.thetas.split(",")]:
        for s in [int(v) for v in a.steps.split(",")]:
            items.append((tag(th, s), circuit_on(labels, dev.num_qubits, s, th)))
            answers[tag(th, s)] = {str(q): float(z) for q, z in zip(labels, F.z_exact(a.n, s, th))}
    rep = U.build_batch(dev, items, os.path.join(a.out, "job_build"), shots=4000, max_seconds=a.max_seconds)
    with open(a.answers_out, "w") as f:
        json.dump(answers, f, indent=1, sort_keys=True)
    sha = hashlib.sha256(open(a.answers_out, "rb").read()).hexdigest()
    log = dict(device=dev.name, n=a.n, chain=ch, cz={t: r["cz"] for t, r in rep["items"].items()},
               circuits=rep["circuits"], qpu_seconds_model=rep["qpu_seconds_model"], answers_sha256=sha)
    json.dump(log, open(os.path.join(a.out, "build.json"), "w"), indent=1)
    print(f"{dev.name}: {ch['rule']} chain {labels[:3]}..{labels[-2:]}")
    for t, r in rep["items"].items():
        print(f"{t:16} CZ {r['cz']}")
    print(f"circuits {rep['circuits']}  model {rep['qpu_seconds_model']} s  answers sha256 {sha}")


if __name__ == "__main__":
    main()
