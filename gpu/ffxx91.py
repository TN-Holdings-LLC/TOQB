"""XX chain (free fermions) at 91 qubits, depth scan, raw (home, 2026-11-12; owner 10:42 JST: worth doing; draft).
The circuit of gpu/ff_xx.py (brickwork of XX+YY rotations by theta, Neel start; exact at any size by free fermions),
built through the same path as the Hubbard jobs so that gpu/hub_check.py and gpu/hub_score.py apply unchanged:
chain by daily/du91 (shapes, else psf-os rule C), user2d batch, mirror from the compiled circuit (hub_build), one ring
sentinel, 4000 shots. Tags N{n}_th{1000 theta}_s{steps}; build.json carries chains[str(n)] and the CZ per tag.
usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/ffxx91.py DEV OUT ANS_OUT [--n 91] [--thetas 0.7853981633974483,1.5707963267948966]
       [--steps 2,4,6,8,10,12] [--max-seconds 160]
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import ff_xx as F  # noqa: E402
import hub_build as HB  # noqa: E402


def tag(n, th, s):
    return f"N{n}_th{int(round(th * 1000)):04d}_s{s:02d}"


def main():
    from psf_os import device as Dv
    from psf_os import user2d as U
    ap = argparse.ArgumentParser()
    ap.add_argument("dev")
    ap.add_argument("out")
    ap.add_argument("ans_out")
    ap.add_argument("--n", type=int, default=91)
    ap.add_argument("--thetas", default="0.7853981633974483,1.5707963267948966")
    ap.add_argument("--steps", default="2,4,6,8,10,12")
    ap.add_argument("--max-seconds", type=float, default=160)
    a = ap.parse_args()
    for p in (a.out, a.ans_out):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    dev = Dv.Device.load(a.dev)
    labels, how = HB.chain_of(dev, a.n)
    items, answers = [], {}
    for th in map(float, a.thetas.split(",")):
        for s in map(int, a.steps.split(",")):
            t = tag(a.n, th, s)
            items.append((t, HB.on_chain(F.circuit(a.n, s, th, measure=False), labels, dev.num_qubits)))
            answers[t] = {str(q): float(z) for q, z in zip(labels, F.z_exact(a.n, s, th))}
    HB._mirror_from_compiled(dev, U)
    rep = U.build_batch(dev, items, a.out, shots=4000, max_seconds=a.max_seconds)
    cz = {t: r["cz"] for t, r in rep["items"].items()}
    json.dump(answers, open(a.ans_out, "w"), indent=1, sort_keys=True)
    json.dump(dict(device=dev.name, chains={str(a.n): dict(labels=labels, **how)}, cz=cz, circuits=rep["circuits"],
                   qpu_seconds_model=rep["qpu_seconds_model"]), open(os.path.join(a.out, "build.json"), "w"), indent=1)
    for t in sorted(cz):
        print(f"{t}: CZ {cz[t]}, copy {rep['items'][t]['copy']}")
    print(f"chain by rule {how['rule']}; circuits {rep['circuits']}  model {rep['qpu_seconds_model']} s")
    print("answers sha256", hashlib.sha256(open(a.ans_out, "rb").read()).hexdigest())


if __name__ == "__main__":
    main()
