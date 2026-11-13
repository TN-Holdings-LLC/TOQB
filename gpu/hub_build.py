"""1D Fermi-Hubbard device job, raw (home, 2026-11-11; owner 19:44 JST): the Trotter circuit of
notes/hubbard_2026-11-11/hub_cost.py (interleaved Jordan-Wigner, fermionic swaps, Neel start, J 1, dt 0.25) at U = 4
and, in the same job, the U = 0 ruler (free fermions, exact at any size) in which every onsite RZZ is replaced by two
CZ on the same pair separated by a barrier (CZ CZ = identity), so that both arms carry the same CZ count and the same
CZ layers (owner: "U=0 の位置にも打ち消し合う CZ を2つ置き、CZ の数と層をそろえる").

Placement: the 2L-qubit chain by the dual-unitary rule (daily/du91: shape rule first; if no shape qualifies, psf-os
rule C), the logical qubit k on chain label k; psf-os's user entrance (user2d.build_batch) places each circuit by
translation, compiles it, adds its floor and mirror, and one ring sentinel serves the job. 4000 shots.
Answers: per-qubit <Z>, read from ANS_IN (gpu/hub_answers.py output, sealed) and written by tag and chain label to
ANS_OUT. Refuses unless the two arms of every step have the same compiled CZ count.
usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/hub_build.py DEV_DIR OUT ANS_IN ANS_OUT --L 20 --steps 2 4 6
       [--max-seconds 60]
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from daily import du91 as X  # noqa: E402
import hub_answers as HA  # noqa: E402


def logical(L, steps, arm):
    """2L-qubit circuit: arm 'U4' is hub_cost's circuit at U = 4; arm 'U0' the U = 0 circuit with each onsite RZZ(0)
    written as CZ, barrier, CZ (and the onsite RZ(0) dropped)."""
    from qiskit import QuantumCircuit
    if arm == "U4":
        return HA.circuit(L, steps, 4.0)
    src = HA.circuit(L, steps, 0.0)
    out = QuantumCircuit(src.num_qubits)
    for ins in src.data:
        qs = [src.find_bit(q).index for q in ins.qubits]
        if ins.operation.name == "rzz":
            out.cz(*qs)
            out.barrier(*qs)
            out.cz(*qs)
        elif ins.operation.name == "rz" and abs(float(ins.operation.params[0])) < 1e-15:
            continue
        else:
            out.append(ins.operation, qs)
    return out


def on_chain(qc, labels, width):
    from qiskit import QuantumCircuit
    out = QuantumCircuit(width)
    for ins in qc.data:
        out.append(ins.operation, [labels[qc.find_bit(q).index] for q in ins.qubits])
    return out


def _mirror_from_compiled(dev, U):
    """The mirror as psf-os's grid3d.mirror_of_compiled builds it: the compiled U, a barrier, its inverse, Z readout.
    user2d's mirror recompiles the logical U U^dagger at level 1, and for this circuit the reversed half loses a few
    CZ (try-build 2026-11-11: the mirror_cz acceptance failed), as grid3d's docstring records for the folded layout.
    Overridden here for this job only; psf-os itself is not changed. The acceptance (mirror CZ = 2 x user CZ) still
    runs and refuses on any mismatch."""
    from qiskit import QuantumCircuit
    from psf_os.compile import RuleCompiler
    rc = RuleCompiler(dev)

    def mirror(u, phys):
        body = rc.pm.run(u)
        out = QuantumCircuit(body.num_qubits, len(phys))
        out.compose(body, qubits=list(range(body.num_qubits)), inplace=True)
        out.barrier()
        out.compose(body.inverse(), qubits=list(range(body.num_qubits)), inplace=True)
        for k, q in enumerate(phys):
            out.measure(q, k)
        return out
    U.M.mirror = mirror


def chain_of(dev, n):
    pl = X.place(dev, n)
    if pl["shape"] is not None:
        shape = next(s for s in X.SHAPES if s[0] == pl["shape"])
        return list(X.snake(n, shape)), dict(rule="shape", shape=pl["shape"], passed_over=pl["passed_over"])
    from psf_os import chain as CH
    rc = CH.place(dev, n)
    return list(rc["chain"]), dict(rule="C", start=rc["start"], passed_over=pl["passed_over"])


def main():
    from psf_os import device as Dv
    from psf_os import user2d as U
    ap = argparse.ArgumentParser()
    ap.add_argument("dev")
    ap.add_argument("out")
    ap.add_argument("ans_in")
    ap.add_argument("ans_out")
    ap.add_argument("--L", type=int, nargs="+", default=[20])
    ap.add_argument("--steps", type=int, nargs="+", default=[2, 4, 6])
    ap.add_argument("--max-seconds", type=float, default=60)
    ap.add_argument("--arms", default="U4,U0", help="arms to build (default both)")
    ap.add_argument("--twin", action="store_true", help="add each circuit's Clifford twin (psf_os.twin); answers to ANS_twin.json")
    a = ap.parse_args()
    for p in (a.out, a.ans_out):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    dev = Dv.Device.load(a.dev)
    vals = json.load(open(a.ans_in))
    items, answers, chains = [], {}, {}
    for L in a.L:
        labels, how = chain_of(dev, 2 * L)
        chains[L] = dict(labels=labels, **how)
        for s in a.steps:
            for arm in a.arms.split(","):
                tag = f"L{L}_s{s}_{arm}"
                items.append((tag, on_chain(logical(L, s, arm), labels, dev.num_qubits)))
                answers[tag] = {str(q): v for q, v in zip(labels, vals[tag])}
    _mirror_from_compiled(dev, U)
    rep = U.build_batch(dev, items, a.out, shots=4000, max_seconds=a.max_seconds, **(dict(twin=True) if a.twin else {}))
    cz = {t: r["cz"] for t, r in rep["items"].items()}
    for L in a.L:
        for s in a.steps:
            if f"L{L}_s{s}_U0" in cz and cz[f"L{L}_s{s}_U4"] != cz[f"L{L}_s{s}_U0"]:
                raise SystemExit(f"REFUSED: CZ differ between the arms at L {L} steps {s}: "
                                 f"{cz[f'L{L}_s{s}_U4']} and {cz[f'L{L}_s{s}_U0']}")
    with open(a.ans_out, "w") as f:
        json.dump(answers, f, indent=1, sort_keys=True)
    json.dump(dict(device=dev.name, chains={str(k): v for k, v in chains.items()}, cz=cz,
                   circuits=rep["circuits"], qpu_seconds_model=rep["qpu_seconds_model"]),
              open(os.path.join(a.out, "build.json"), "w"), indent=1)
    for L, c in chains.items():
        print(f"L {L}: chain by rule {c['rule']} ({c.get('shape', c.get('start'))}), {c['labels'][:3]}..{c['labels'][-2:]}")
    for t in sorted(cz):
        print(f"{t}: CZ {cz[t]}, copy {rep['items'][t]['copy']}")
    print(f"circuits {rep['circuits']}  model {rep['qpu_seconds_model']} s")
    print("answers sha256", hashlib.sha256(open(a.ans_out, "rb").read()).hexdigest())
    if a.twin:
        from twin_util import twin_answers
        twin_answers(a.out, sorted(cz), a.ans_out[:-5] + "_twin.json")


if __name__ == "__main__":
    main()
