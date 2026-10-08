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
