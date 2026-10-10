"""Structural check and metrics of a compiled circuit on a device."""
from __future__ import annotations

ALWAYS_ALLOWED = {"barrier", "measure", "delay", "reset"}
SYMMETRIC = {"cz", "rzz", "swap"}  # two-qubit gates whose direction does not matter


CONTROL_FLOW = {"if_else", "while_loop", "for_loop", "switch_case", "box"}


def structural_check(out, device):
    """None if every instruction is in the device's basis and every two-qubit gate sits on an accepted pair;
    otherwise a short description of the first violation. v13: control flow (`if_else` and the like) is accepted,
    and its bodies are checked in the same way, on the qubits the instruction acts on."""
    allowed = set(device.basis) | ALWAYS_ALLOWED
    edges = set(device.edges)
    return _check(out, list(range(out.num_qubits)), device, allowed, edges)


def _check(circ, where, device, allowed, edges):
    for ins in circ.data:
        name = ins.operation.name
        q = tuple(where[circ.find_bit(b).index] for b in ins.qubits)
        if any(i >= device.num_qubits for i in q):
            return f"qubit {max(q)} outside the device"
        if name in CONTROL_FLOW:
            for block in ins.operation.blocks:  # a body's qubits are the instruction's, in order
                problem = _check(block, list(q), device, allowed, edges)
                if problem:
                    return f"in {name}: {problem}"
            continue
        if name not in allowed:
            return f"operation {name} not in the basis"
        if len(q) == 2 and name not in ALWAYS_ALLOWED and q not in edges and not (name in SYMMETRIC and q[::-1] in edges):
            return f"{name} on {q}, not a coupled pair"
        if len(q) > 2 and name not in ALWAYS_ALLOWED:
            return f"{name} on {len(q)} qubits"
    return None


def _two_qubit_gates(circ, where):
    """(qubits) of every two-qubit gate, in control flow's bodies too (each body counted once, as written). v13."""
    out = []
    for ins in circ.data:
        q = tuple(where[circ.find_bit(b).index] for b in ins.qubits)
        if ins.operation.name in CONTROL_FLOW:
            for block in ins.operation.blocks:
                out += _two_qubit_gates(block, list(q))
        elif len(q) == 2 and ins.operation.name not in ALWAYS_ALLOWED:
            out.append(q)
    return out


def _operations(circ, where):
    """(name, qubits) of every operation but barriers and delays, in control flow's bodies too. v14."""
    out = []
    for ins in circ.data:
        q = tuple(where[circ.find_bit(b).index] for b in ins.qubits)
        if ins.operation.name in CONTROL_FLOW:
            for block in ins.operation.blocks:
                out += _operations(block, list(q))
        elif ins.operation.name not in ("barrier", "delay"):
            out.append((ins.operation.name, q))
    return out


def failed_operations(out, device):
    """v14: the operations (gates and measurements) on a failed qubit, and the two-qubit gates on a failed coupler.
    One of them makes the output unusable on the device: its result is noise, and nothing in the output says so."""
    n = 0
    for name, q in _operations(out, list(range(out.num_qubits))):
        if set(q) & device.failed_qubits or (len(q) == 2 and (q in device.failed_edges or q[::-1] in device.failed_edges)):
            n += 1
    return n


def metrics(out, device):
    """Two-qubit count and depth, gates on failed elements, and the duration when the device has a Target."""
    g2 = device.two_qubit_gate
    two = _two_qubit_gates(out, list(range(out.num_qubits)))
    on_failed = 0
    for q in two:
        if q in device.failed_edges or q[::-1] in device.failed_edges or set(q) & device.failed_qubits:
            on_failed += 1
    m = dict(q2=len(two), d2=out.depth(filter_function=lambda x: len(x.qubits) == 2
                                       and x.operation.name not in ALWAYS_ALLOWED),
             on_failed=on_failed, on_failed_ops=failed_operations(out, device), two_qubit_gate=g2, qubits_used=len({out.find_bit(b).index for i in out.data
                                                                     for b in i.qubits}))
    if device.target is not None:
        try:
            m["duration_s"] = float(out.estimate_duration(device.target, unit="s"))
        except Exception as exc:  # noqa: BLE001 - recorded, not fatal
            m["duration_s"] = f"n/a: {type(exc).__name__}"
    return m


EQUIV_MAX_QUBITS = 12   # the check simulates state vectors on the qubits the output touches
EQUIV_TRIALS = 3        # random product input states, besides |0...0>
EQUIV_TOL = 1e-6        # a distance above this is "not equivalent"
CLASSICAL_CONTROL = {"if_else", "while_loop", "for_loop", "switch_case", "box"}


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


def _final_measures(qc):
    """({clbit index: qubit index}, keep, None) when every measurement in qc is final, else (None, None, why).

    A measurement is final when nothing that is measured later depends on its qubit. A gate on a qubit already
    measured is "trailing": every qubit it touches must stay unmeasured from then on, so it cannot change any measured
    bit, and it is left out of the simulation (`keep` is False for it). TKET, for one, can put a swap after the
    measurements when it turns an implicit qubit permutation back into gates. The last measurement into a clbit
    counts."""
    measured, dead, cmap, keep = set(), set(), {}, []
    for ins in qc.data:
        name = ins.operation.name
        if name in CLASSICAL_CONTROL:
            return None, None, "has classical control"
        qs = set(qc.find_bit(b).index for b in ins.qubits)
        if name == "reset":
            return None, None, "resets a qubit"
        if name == "measure":
            if qs & dead:
                return None, None, "measures a qubit after a gate that follows a measurement"
            measured |= qs
            cmap[qc.find_bit(ins.clbits[0]).index] = next(iter(qs))
            keep.append(True)
        elif name in ("barrier", "delay"):
            keep.append(True)
        elif qs & (measured | dead):
            dead |= qs
            keep.append(False)
        else:
            keep.append(True)
    return cmap, keep, None


def _gates(qc, keep):
    """qc's kept gates, without its measurements, barriers and delays (a circuit of gates only, no clbits)."""
    from qiskit import QuantumCircuit
    g = QuantumCircuit(qc.num_qubits, global_phase=qc.global_phase)
    for ins, k in zip(qc.data, keep):
        if k and ins.operation.name not in ("measure", "barrier", "delay"):
            g.append(ins.operation, [qc.find_bit(b).index for b in ins.qubits])
    return g


def _clbit_distribution(probs, cmap):
    """{outcome: probability} over the clbits in cmap ({clbit: qubit position in the simulated register}), from the
    register's basis-state probabilities (Qiskit's order: position 0 is the least significant bit)."""
    import numpy as np
    b = np.arange(len(probs))
    keys = np.zeros(len(probs), dtype=np.int64)
    for j, c in enumerate(sorted(cmap)):
        keys |= ((b >> cmap[c]) & 1) << j
    u, inv = np.unique(keys, return_inverse=True)
    return dict(zip(u.tolist(), np.bincount(inv, weights=probs).tolist()))


def equivalence(logical, out, reference=None):
    """{"checked": True, "method": ..., "against": ..., "distance": x, "equivalent": bool} or
    {"checked": False, "why": ...}.

    The input is expanded through its definitions. When the compiler reads a high-level operation its own way (TKET
    builds its own product formula for a PauliEvolutionGate), the adapter passes that reading as `reference`, and the
    output is checked against it ("against": "the compiler's reading").

    The input and the output are run from |0...0> and from EQUIV_TRIALS random product states; input qubit i is
    prepared at its initial device qubit in the output, and every other qubit the output touches starts in |0>.
      - "state" (an input without measurements): input qubit i is read at its final device qubit, every other touched
        qubit must end in |0>; the distance is the largest state infidelity.
      - "distribution" (an input whose measurements are all final, `_final_measures`): the probabilities of the
        measured clbits are compared, each clbit read from the qubit the output measures into it; the distance is
        the largest total variation distance. Passes that act only on what is measured (removing diagonal gates or
        swaps before a measurement) change the state but not these probabilities. Gates after the measurements that
        nothing measures afterwards are left out, and their number is reported as "trailing" (they still count in
        the output's metrics).
    """
    import numpy as np
    from qiskit import QuantumCircuit, transpile
    from qiskit.quantum_info import Statevector
    src = logical if reference is None else reference
    against = "the input" if reference is None else "the compiler's reading of the input"
    if src.num_qubits != logical.num_qubits:
        return dict(checked=False, why="the compiler's reading has a different number of qubits")
    meas_in, keep_in, why = _final_measures(src)
    if why:
        return dict(checked=False, why=f"the input {why}")
    if src.num_qubits > EQUIV_MAX_QUBITS:
        return dict(checked=False, why=f"{src.num_qubits} input qubits (limit {EQUIV_MAX_QUBITS})")
    # instructions expanded through their definitions: a PauliEvolutionGate becomes Qiskit's product formula
    bare = transpile(_gates(src, keep_in), basis_gates=["u", "cx"], optimization_level=0)
    meas_out, keep_out, why = _final_measures(out)
    if why:
        return dict(checked=False, why=f"the output {why}")
    trailing = keep_out.count(False)
    n = bare.num_qubits
    initial, final = placements(out, n)
    gates = [i for i, k in zip(out.data, keep_out) if k and i.operation.name not in ("barrier", "measure", "delay")]
    touched = {out.find_bit(b).index for i in gates for b in i.qubits} | set(initial)
    touched |= set(meas_out.values()) if meas_in else set(final)
    active = sorted(touched)
    if len(active) > EQUIV_MAX_QUBITS:
        return dict(checked=False, why=f"{len(active)} qubits touched (limit {EQUIV_MAX_QUBITS})")
    method = "distribution" if meas_in else "state"
    if meas_in and set(meas_in) != set(meas_out):
        return dict(checked=True, method=method, against=against, distance=1.0, equivalent=False, trailing=trailing,
                    why=f"the output measures into clbits {sorted(meas_out)}, the input into {sorted(meas_in)}")
    idx = {p: k for k, p in enumerate(active)}
    red = QuantumCircuit(len(active), global_phase=out.global_phase)
    for i in gates:
        red.append(i.operation, [idx[out.find_bit(b).index] for b in i.qubits])
    rng = np.random.default_rng(0)
    worst = 0.0
    for trial in range(EQUIV_TRIALS + 1):
        angles = rng.uniform(0, 2 * np.pi, (n, 3)) if trial else None
        comp = QuantumCircuit(len(active))
        if angles is not None:
            for q in range(n):
                comp.u(*angles[q], idx[initial[q]])
        comp.compose(red, inplace=True)
        if meas_in:
            ref = QuantumCircuit(n)
            if angles is not None:
                for q in range(n):
                    ref.u(*angles[q], q)
            ref.compose(bare, inplace=True)
            p = _clbit_distribution(Statevector(ref).probabilities(), meas_in)
            r = _clbit_distribution(Statevector(comp).probabilities(), {c: idx[q] for c, q in meas_out.items()})
            d = 0.5 * sum(abs(p.get(k, 0.0) - r.get(k, 0.0)) for k in set(p) | set(r))
        else:
            ref = QuantumCircuit(len(active))
            if angles is not None:
                for q in range(n):
                    ref.u(*angles[q], idx[final[q]])
            ref.compose(bare, qubits=[idx[final[q]] for q in range(n)], inplace=True)
            d = 1 - abs(Statevector(ref).inner(Statevector(comp))) ** 2
        worst = max(worst, float(d))
    return dict(checked=True, method=method, against=against, distance=worst, equivalent=bool(worst <= EQUIV_TOL),
                trailing=trailing)
