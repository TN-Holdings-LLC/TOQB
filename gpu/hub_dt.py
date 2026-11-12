"""Hubbard 1D, one time with two step sizes (home, 2026-11-12; task C follow-up, owner 11:02 JST "進めて").
Arms at J t = T: `T{T}_s{steps}` = the hub_cost circuit (U 4) with dt = T / steps. Two answer sets, per qubit <Z>:
  circuit   the circuit's exact value (quimb MPS, as gpu/hub_answers.py)   -> READS verdict, as before;
  continuum the continuum value by Richardson from dt 0.25/4 and 0.25/8    -> which arm is closer to the physics.
Subcommands:
  answers OUT_DIR --L 20 --arms 1.0:2,1.0:4,0.5:1,0.5:2     writes circuit.json and continuum.json (sealed; checks only)
  build   DEV OUT ANS_DIR ANS_OUT_PREFIX --L 20 --arms ...   chain, user2d batch (mirror from the compiled circuit),
                                                            writes ANS_OUT_PREFIX_circuit.json / _continuum.json by tag
                                                            and chain label
"""
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "notes", "hubbard_2026-11-11"))
import hub_cost as HC  # noqa: E402


def arms_of(s):
    return [(float(a), int(b)) for a, b in (x.split(":") for x in s.split(","))]


def tag(L, T, steps):
    return f"L{L}_T{T}_s{steps}"


def circ(L, T, steps):
    old = HC.DT
    HC.DT = T / steps
    try:
        return HC.circuit(L, steps)
    finally:
        HC.DT = old


def zq(qc):
    z, bond, err = HC.run_quimb(HC.blocks(qc), 1024)
    return np.asarray(z), bond, err


def answers(a):
    os.makedirs(a.out, exist_ok=True)
    circuit, cont = {}, {}
    for T in sorted({T for T, _ in arms_of(a.arms)}):
        t0 = time.time()
        z8, b8, e8 = zq(circ(a.L, T, int(round(T / (0.25 / 8)))))
        z4, b4, e4 = zq(circ(a.L, T, int(round(T / (0.25 / 4)))))
        z0 = 2 * z8 - z4
        cont[f"T{T}"] = z0.tolist()
        print(f"continuum J t {T}: bond {b8} / {b4}, error estimate {e8:.1e} / {e4:.1e}, "
              f"Richardson step |z(dt/8) - z0| max {np.abs(z8 - z0).max():.1e}, sum Z {z0.sum():.1e}, {time.time() - t0:.0f} s",
              flush=True)
    for T, s in arms_of(a.arms):
        z, b, e = zq(circ(a.L, T, s))
        circuit[tag(a.L, T, s)] = z.tolist()
        print(f"{tag(a.L, T, s)} (dt {T / s}): bond {b}, error estimate {e:.1e}, sum Z {z.sum():.1e}; MSE circuit against "
              f"continuum {np.mean((z - np.array(cont[f'T{T}'])) ** 2):.2e}", flush=True)
    json.dump(circuit, open(os.path.join(a.out, "circuit.json"), "w"), sort_keys=True)
    json.dump(cont, open(os.path.join(a.out, "continuum.json"), "w"), sort_keys=True)
    for f in ("circuit.json", "continuum.json"):
        print(f, hashlib.sha256(open(os.path.join(a.out, f), "rb").read()).hexdigest())


def build(a):
    from psf_os import device as Dv
    from psf_os import user2d as U
    import hub_build as HB
    for p in (a.out, a.ans_prefix + "_circuit.json"):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    dev = Dv.Device.load(a.dev)
    circuit = json.load(open(os.path.join(a.ans_dir, "circuit.json")))
    cont = json.load(open(os.path.join(a.ans_dir, "continuum.json")))
    labels, how = HB.chain_of(dev, 2 * a.L)
    items, ac, ak = [], {}, {}
    for T, s in arms_of(a.arms):
        t = tag(a.L, T, s)
        items.append((t, HB.on_chain(circ(a.L, T, s), labels, dev.num_qubits)))
        ac[t] = {str(q): v for q, v in zip(labels, circuit[t])}
        ak[t] = {str(q): v for q, v in zip(labels, cont[f"T{T}"])}
    HB._mirror_from_compiled(dev, U)
    rep = U.build_batch(dev, items, a.out, shots=4000, max_seconds=a.max_seconds)
    cz = {t: r["cz"] for t, r in rep["items"].items()}
    json.dump(ac, open(a.ans_prefix + "_circuit.json", "w"), indent=1, sort_keys=True)
    json.dump(ak, open(a.ans_prefix + "_continuum.json", "w"), indent=1, sort_keys=True)
    json.dump(dict(device=dev.name, chains={str(a.L): dict(labels=labels, **how)}, cz=cz, circuits=rep["circuits"],
                   qpu_seconds_model=rep["qpu_seconds_model"]), open(os.path.join(a.out, "build.json"), "w"), indent=1)
    for t in sorted(cz):
        print(f"{t}: CZ {cz[t]}, copy {rep['items'][t]['copy']}")
    print(f"chain by rule {how['rule']}; circuits {rep['circuits']}  model {rep['qpu_seconds_model']} s")
    for k in ("circuit", "continuum"):
        print(k, "answers sha256", hashlib.sha256(open(f"{a.ans_prefix}_{k}.json", "rb").read()).hexdigest())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("answers")
    p1.add_argument("out")
    p1.add_argument("--L", type=int, default=20)
    p1.add_argument("--arms", default="1.0:2,1.0:4,0.5:1,0.5:2")
    p2 = sub.add_parser("build")
    for x in ("dev", "out", "ans_dir", "ans_prefix"):
        p2.add_argument(x)
    p2.add_argument("--L", type=int, default=20)
    p2.add_argument("--arms", default="1.0:2,1.0:4,0.5:1,0.5:2")
    p2.add_argument("--max-seconds", type=float, default=60)
    a = ap.parse_args()
    answers(a) if a.cmd == "answers" else build(a)
