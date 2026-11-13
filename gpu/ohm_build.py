"""Ohm's-law device job, raw (workplace, 2026-11-12; home's instruction of 02:05 CET; not declared): the circuits of
gpu/ohm_answers.py (arms A0 / A1 / A2, cycles, K bit strings and their complements) on one N-qubit chain.

Placement and form as gpu/hub_build.py: the chain by the dual-unitary rule (daily/du91 shapes first, psf-os rule C if
none qualifies), logical qubit k on chain label k; psf-os's user entrance (user2d.build_batch) places each circuit by
translation, compiles it, adds its floor and mirror (the mirror from the compiled circuit, as hub_build), one ring
sentinel per job. Refuses unless A1 and A2 have the same compiled CZ count and CZ depth for every cycle count and
string (RZ is virtual). Answers: per-qubit <Z> read from ANS_IN (gpu/ohm_answers.py output, sealed) and written by
tag and chain label to ANS_OUT; the strings are regenerated from ANS_IN's seed and must equal the ones stored there.
usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/ohm_build.py DEV_DIR OUT ANS_IN ANS_OUT [--shots 1000]
       [--max-seconds 160]
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import hub_build as HB  # noqa: E402
import ohm_answers as OA  # noqa: E402


def cz_depth(c):
    return c.depth(filter_function=lambda i: i.operation.name == "cz")


def main():
    from qiskit import qpy
    from psf_os import device as Dv
    from psf_os import user2d as U
    ap = argparse.ArgumentParser()
    ap.add_argument("dev")
    ap.add_argument("out")
    ap.add_argument("ans_in")
    ap.add_argument("ans_out")
    ap.add_argument("--shots", type=int, default=1000)
    ap.add_argument("--max-seconds", type=float, default=160)
    ap.add_argument("--sentinel-fallback", default=None, choices=[None, "same_qubits"],
                    help="psf-os sentinel fallback (2026-11-13); default: none, as before")
    a = ap.parse_args()
    for p in (a.out, a.ans_out):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    dev = Dv.Device.load(a.dev)
    A = json.load(open(a.ans_in))
    meta, vals = A["meta"], A["z"]
    N, K = meta["N"], meta["K"]
    strs = OA.strings(N, K, meta["m"], meta["seed"])
    if {n: "".join(map(str, b)) for n, b in strs} != meta["strings"]:
        raise SystemExit("REFUSED: the strings regenerated from the seed differ from the answers file's")
    labels, how = HB.chain_of(dev, N)
    items, answers = [], {}
    for arm in OA.ARMS:
        for t in meta["cycles"]:
            for name, bits in strs:
                tg = OA.tag(arm, t, name)
                items.append((tg, HB.on_chain(OA.circuit(N, t, arm, bits), labels, dev.num_qubits)))
                answers[tg] = {str(q): v for q, v in zip(labels, vals[tg])}
    HB._mirror_from_compiled(dev, U)
    rep = U.build_batch(dev, items, a.out, shots=a.shots, max_seconds=a.max_seconds,
                        sentinel_spec=HB.sentinel_spec_of(a.sentinel_fallback))
    cz = {t: r["cz"] for t, r in rep["items"].items()}
    runs = os.path.join(a.out, "runs")
    depth = {t: cz_depth(qpy.load(open(os.path.join(runs, f"p2d_{t}.qpy"), "rb"))[0]) for t in cz}
    for t in meta["cycles"]:
        for name, _ in strs:
            t1, t2 = OA.tag("A1", t, name), OA.tag("A2", t, name)
            if (cz[t1], depth[t1]) != (cz[t2], depth[t2]):
                raise SystemExit(f"REFUSED: A1 and A2 differ at t {t} {name}: CZ {cz[t1]} / {cz[t2]}, "
                                 f"depth {depth[t1]} / {depth[t2]}")
    with open(a.ans_out, "w") as f:
        json.dump(dict(meta=meta, z=answers), f, indent=1, sort_keys=True)
    json.dump(dict(device=dev.name, chain=dict(labels=labels, **how), cz=cz, cz_depth=depth, shots=a.shots,
                   strings=meta["strings"], N=N, K=K, m=meta["m"], cycles=meta["cycles"], seed=meta["seed"],
                   circuits=rep["circuits"], qpu_seconds_model=rep["qpu_seconds_model"],
                   **HB.sentinel_fallback_report(a.out, a.sentinel_fallback)),
              open(os.path.join(a.out, "build.json"), "w"), indent=1)
    print(f"chain by rule {how['rule']} ({how.get('shape', how.get('start'))}), {labels[:3]}..{labels[-2:]}")
    for arm in OA.ARMS:
        for t in meta["cycles"]:
            tg = [OA.tag(arm, t, n) for n, _ in strs]
            print(f"{arm} t {t}: CZ {min(cz[x] for x in tg)}-{max(cz[x] for x in tg)}, CZ depth "
                  f"{min(depth[x] for x in tg)}-{max(depth[x] for x in tg)}")
    print(f"circuits {rep['circuits']}  model {rep['qpu_seconds_model']} s  ({a.shots} shots)")
    print("answers by chain label sha256", hashlib.sha256(open(a.ans_out, "rb").read()).hexdigest())


if __name__ == "__main__":
    main()
