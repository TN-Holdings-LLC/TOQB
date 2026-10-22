"""Which noise source sets the shrink lam? (report only, declared 2026-10-22 in
prereg/drafts-2026-10-22/lam_ablate_note.md)

    python -m toqb.lam_ablate RUNS_DIR OUT_DIR

The lam swap (results/lam-swap-2026-10-22) is repeated with the twin's noise taken apart. The twin (toqb.fast_noise) has
four sources, each read from the calibration: two-qubit depolarizing (the CZ error), one-qubit depolarizing (sx, x),
thermal relaxation (T1, T2 over every gate and idle), and the readout error. Five twins are built from
`snapshot:marrakesh`: the full one, and one with each source switched off (error 0, failed elements kept failed;
T1 = T2 = 1,000 s). They are
written as targets (OUT_DIR/target_<variant>.pkl) and used as `file:` devices, so nothing else changes.

For L 8 and 16, each model (the parameters trained through item 31 and through the zipper in
results/zip-compare-2026-10-22/runs) on each circuit, on each twin: (lam, delta, fit rms) from toqb.undamp.estimate
(the 64 training inputs, 1,024 trajectories, seed predict.seed + 5), as toqb.lam_swap.

Checks that stop the run: the compiled circuit of the first training input is the same gate for gate (names, qubits,
angles) on every twin (the switches change the noise, not the compile); and the full twin's lam equals the lam swap's
(within 1e-9).
"""
from __future__ import annotations

import json
import os
import pickle
import sys

import numpy as np

from toqb import s2r2 as S2
from toqb import task_loop as TL
from toqb import undamp as U
from toqb.devices import FAILED_ERROR

ARMS = {"t": "psfai:template", "z": "psfai:template_zip"}
VARIANTS = ("full", "no_cz", "no_1q", "no_relax", "no_readout")
OFF_T = 1000.0


class Stop(Exception):
    pass


def variant_target(target, variant):
    """A copy of the target with one noise source switched off (the twin reads only these fields)."""
    from qiskit.transpiler import InstructionProperties
    t = pickle.loads(pickle.dumps(target))
    if variant == "full":
        return t
    if variant == "no_relax":
        qps = list(t.qubit_properties)  # the target hands out copies: change them, then set the list back
        for qp in qps:
            if qp is not None:
                qp.t1, qp.t2 = OFF_T, OFF_T
        t.qubit_properties = qps
        return t
    names = {"no_cz": [g for g in ("cz", "ecr", "cx") if g in t.operation_names], "no_1q": ["sx", "x"],
             "no_readout": ["measure"]}[variant]
    for name in names:
        for qargs, p in list(t[name].items()):
            # a failed element stays failed (toqb.devices.FAILED_ERROR), so the placement cannot change
            if p is not None and p.error is not None and p.error < FAILED_ERROR:
                t.update_instruction_properties(name, qargs, InstructionProperties(duration=p.duration, error=0.0))
    return t


def signature(c):
    return [(i.operation.name, tuple(c.find_bit(q).index for q in i.qubits),
             tuple(round(float(p), 12) for p in i.operation.params)) for i in c.data]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    runs, out = argv[0], argv[1]
    if os.path.exists(out):
        raise Stop(f"{out} exists; a run never overwrites another")
    os.makedirs(out)
    from toqb.devices import get_device
    base = get_device("snapshot:marrakesh").target
    dev = {}
    for v in VARIANTS:
        path = os.path.join(out, f"target_{v}.pkl")
        with open(path, "wb") as f:
            pickle.dump(variant_target(base, v), f)
        dev[v] = "file:" + os.path.abspath(path)
    swap = {}
    sf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "lam-swap-2026-10-22", "lam_swap.txt")
    for line in open(sf):
        if line.startswith("{"):
            r = json.loads(line)
            swap[(r["L"], r["model"], r["circuit"])] = r["lam"]
    rows = []
    for L in (8, 16):
        for model in ("t", "z"):
            rec = json.load(open(f"{runs}/L{L}_s301-{ARMS[model].replace(':', '_')}.json"))
            theta = np.array(rec["final_mean"])
            task = rec["task"]
            Xtr = S2.teacher_data2(task)[0]
            qc = TL.model_circuit(TL.angle_list(theta, Xtr[0], task["n"], L, task["enc"]), task["n"], L)
            for circ in ("t", "z"):
                ref = None
                for v in VARIANTS:
                    plan = dict(name=rec["plan"], device=dev[v], task=task, train=rec["train"],
                                predict=rec["predict"], standin=rec["standin"])
                    R = S2.Runner(plan, ARMS[circ])
                    sig = signature(R.arm.compile(qc))
                    if ref is None:
                        ref = sig
                    elif sig != ref:
                        raise Stop(f"L{L} model {model} circuit {circ}: the circuit differs on twin {v}")
                    lam, delta, rms = U.estimate(R, theta, Xtr, task, 1024, rec["predict"]["seed"] + 5)
                    if v == "full" and abs(lam - swap[(L, model, circ)]) > 1e-9:
                        raise Stop(f"L{L} {model}/{circ}: full twin lam {lam} != the lam swap's {swap[(L, model, circ)]}")
                    row = dict(L=L, model=model, circuit=circ, twin=v, lam=float(lam), delta=float(delta),
                               fit_rms=float(rms))
                    rows.append(row)
                    print(json.dumps(row), flush=True)
    json.dump(rows, open(os.path.join(out, "lam_ablate.json"), "w"), indent=1)
    print("| L | model / circuit | " + " | ".join(VARIANTS) + " |")
    print("|---|---|" + "---|" * len(VARIANTS))
    for L in (8, 16):
        for model in ("t", "z"):
            for circ in ("t", "z"):
                rs = {r["twin"]: r for r in rows if (r["L"], r["model"], r["circuit"]) == (L, model, circ)}
                print(f"| {L} | {model} / {circ} | " + " | ".join(
                    f"{rs[v]['lam']:.3f} ({rs[v]['delta']:+.3f}, {rs[v]['fit_rms']:.3f})" for v in VARIANTS) + " |")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Stop as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        sys.exit(2)
