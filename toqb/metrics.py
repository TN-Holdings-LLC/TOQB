"""Structural check and metrics of a compiled circuit on a device."""
from __future__ import annotations

ALWAYS_ALLOWED = {"barrier", "measure", "delay", "reset"}
SYMMETRIC = {"cz", "rzz", "swap"}  # two-qubit gates whose direction does not matter


def structural_check(out, device):
    """None if every instruction is in the device's basis and every two-qubit gate sits on an accepted pair;
    otherwise a short description of the first violation."""
    allowed = set(device.basis) | ALWAYS_ALLOWED
    edges = set(device.edges)
    for ins in out.data:
        name = ins.operation.name
        if name not in allowed:
            return f"operation {name} not in the basis"
        q = tuple(out.find_bit(b).index for b in ins.qubits)
        if any(i >= device.num_qubits for i in q):
            return f"qubit {max(q)} outside the device"
        if len(q) == 2 and name not in ALWAYS_ALLOWED and q not in edges and not (name in SYMMETRIC and q[::-1] in edges):
            return f"{name} on {q}, not a coupled pair"
        if len(q) > 2 and name not in ALWAYS_ALLOWED:
            return f"{name} on {len(q)} qubits"
    return None


def metrics(out, device):
    """Two-qubit count and depth, gates on failed elements, and the duration when the device has a Target."""
    g2 = device.two_qubit_gate
    two = [ins for ins in out.data if len(ins.qubits) == 2 and ins.operation.name not in ALWAYS_ALLOWED]
    on_failed = 0
    for ins in two:
        q = tuple(out.find_bit(b).index for b in ins.qubits)
        if q in device.failed_edges or q[::-1] in device.failed_edges or set(q) & device.failed_qubits:
            on_failed += 1
    m = dict(q2=len(two), d2=out.depth(filter_function=lambda x: len(x.qubits) == 2
                                       and x.operation.name not in ALWAYS_ALLOWED),
             on_failed=on_failed, two_qubit_gate=g2, qubits_used=len({out.find_bit(b).index for i in out.data
                                                                     for b in i.qubits}))
    if device.target is not None:
        try:
            m["duration_s"] = float(out.estimate_duration(device.target, unit="s"))
        except Exception as exc:  # noqa: BLE001 - recorded, not fatal
            m["duration_s"] = f"n/a: {type(exc).__name__}"
    return m


EQUIV_MAX_QUBITS = 12   # the check simulates state vectors on the qubits the output touches
EQUIV_TRIALS = 3        # random product input states, besides |0...0>
EQUIV_TOL = 1e-6        # state infidelity above this is "not equivalent"


def placements(out, n):
    """(initial, final): the device qubit holding each of the n input qubits before and after the circuit.
    From `metadata` (TKET adapter), else from Qiskit's layout, else the identity."""
    md = getattr(out, "metadata", None) or {}
    if "toqb_initial" in md:
        return list(md["toqb_initial"]), list(md["toqb_final"])
    lay = getattr(out, "layout", None)
    if lay is not None:
        return (list(lay.initial_index_layout(filter_ancillas=True))[:n],
                list(lay.final_index_layout(filter_ancillas=True))[:n])
    return list(range(n)), list(range(n))


def equivalence(logical, out):
    """{"checked": True, "infidelity": x, "equivalent": bool} or {"checked": False, "why": ...}.

    The input (final measurements removed) and the output are run from |0...0> and from EQUIV_TRIALS random
    product states; input qubit i is prepared at its initial device qubit in the output and read at its final one,
    every other touched qubit starts in |0> and must end in |0>. The largest state infidelity is reported."""
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    bare = logical.copy()
    bare.remove_final_measurements(inplace=True)
    if any(i.operation.name in ("measure", "reset") for i in bare.data):
        return dict(checked=False, why="the input measures or resets mid-circuit")
    if any(i.operation.name == "reset" for i in out.data):
        return dict(checked=False, why="the output resets a qubit")
    n = bare.num_qubits
    initial, final = placements(out, n)
    gates = [i for i in out.data if i.operation.name not in ("barrier", "measure", "delay")]
    active = sorted({out.find_bit(b).index for i in gates for b in i.qubits} | set(initial) | set(final))
    if len(active) > EQUIV_MAX_QUBITS:
        return dict(checked=False, why=f"{len(active)} qubits touched (limit {EQUIV_MAX_QUBITS})")
    idx = {p: k for k, p in enumerate(active)}
    red = QuantumCircuit(len(active), global_phase=out.global_phase)
    for i in gates:
        red.append(i.operation, [idx[out.find_bit(b).index] for b in i.qubits])
    rng = np.random.default_rng(0)
    worst = 0.0
    for trial in range(EQUIV_TRIALS + 1):
        angles = rng.uniform(0, 2 * np.pi, (n, 3)) if trial else None
        comp = QuantumCircuit(len(active))
        ref = QuantumCircuit(len(active))
        for q in range(n):
            if angles is not None:
                comp.u(*angles[q], idx[initial[q]])
                ref.u(*angles[q], idx[final[q]])
        comp.compose(red, inplace=True)
        ref.compose(bare, qubits=[idx[final[q]] for q in range(n)], inplace=True)
        fid = abs(Statevector(ref).inner(Statevector(comp))) ** 2
        worst = max(worst, float(1 - fid))
    return dict(checked=True, infidelity=worst, equivalent=bool(worst <= EQUIV_TOL))
