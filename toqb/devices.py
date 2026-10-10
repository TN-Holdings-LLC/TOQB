"""Devices: IBM fake backends (with their Target) and abstract coupling maps (no Target, no noise).

Spec strings:
    fake:FakeTorino        a qiskit_ibm_runtime fake backend
    linear:N               a line of N qubits
    grid:RxC               an R x C square grid
    heavyhex:D             Qiskit's heavy-hex map of distance D
    full:N                 all-to-all on N qubits
    bp:<test id>           the backend Benchpress builds for that test (toqb.benchpress_source): its FlexibleBackend's
                           map and basis (no Target: abstract maps carry no calibration), or the fake device with its
                           Target
Abstract maps use the basis cz, rz, sx, x (as Benchpress's FlexibleBackend does, which also allows id).
"""
from __future__ import annotations

from dataclasses import dataclass, field

FAILED_ERROR = 0.5  # an element reported with error >= 0.5 counts as failed
ABSTRACT_BASIS = ("cz", "rz", "sx", "x")


@dataclass
class Device:
    spec: str
    num_qubits: int
    edges: list            # directed (a, b) pairs the device accepts for two-qubit gates
    basis: list            # operation names the device accepts
    target: object = None  # Qiskit Target, only for fake backends
    failed_edges: set = field(default_factory=set)
    failed_qubits: set = field(default_factory=set)

    @property
    def two_qubit_gate(self):
        return next((g for g in ("cz", "ecr", "cx") if g in self.basis), None)


def _failed(target):
    edges, qubits = set(), set()
    for name in ("cz", "ecr", "cx"):
        if name in target.operation_names:
            for qargs, props in target[name].items():
                if qargs is not None and props is not None and props.error is not None and props.error >= FAILED_ERROR:
                    edges.add(tuple(qargs))
    if "sx" in target.operation_names:
        for qargs, props in target["sx"].items():
            if qargs is not None and props is not None and props.error is not None and props.error >= FAILED_ERROR:
                qubits.add(qargs[0])
    if "measure" in target.operation_names:  # v14: a qubit whose measurement fails is a failed qubit too
        for qargs, props in target["measure"].items():
            if qargs is not None and props is not None and props.error is not None and props.error >= FAILED_ERROR:
                qubits.add(qargs[0])
    return edges, qubits


def from_target(spec, target, with_target):
    cm = target.build_coupling_map()
    basis = [g for g in target.operation_names if g in ("cx", "cz", "ecr", "rz", "sx", "x", "id")]
    fe, fq = _failed(target) if with_target else (set(), set())
    edges = sorted({tuple(e) for e in cm.get_edges()})
    return Device(spec, target.num_qubits, edges, basis, target if with_target else None, fe, fq)


def get_device(spec: str) -> Device:
    kind, _, arg = spec.partition(":")
    if kind == "bp":
        from toqb.benchpress_source import build
        _, backend, _ = build(arg)
        return from_target(spec, backend.target, type(backend).__name__ != "FlexibleBackend")
    if kind == "fake":
        from qiskit_ibm_runtime import fake_provider
        target = getattr(fake_provider, arg)().target
        cm = target.build_coupling_map()
        basis = [g for g in target.operation_names if g in ("cx", "cz", "ecr", "rz", "sx", "x", "id")]
        fe, fq = _failed(target)
        return Device(spec, target.num_qubits, [tuple(e) for e in cm.get_edges()], basis, target, fe, fq)
    from qiskit.transpiler import CouplingMap
    if kind == "linear":
        cm = CouplingMap.from_line(int(arg))
    elif kind == "grid":
        r, c = (int(x) for x in arg.lower().split("x"))
        cm = CouplingMap.from_grid(r, c)
    elif kind == "heavyhex":
        cm = CouplingMap.from_heavy_hex(int(arg))
    elif kind == "full":
        cm = CouplingMap.from_full(int(arg))
    else:
        raise ValueError(f"unknown device spec {spec!r}")
    edges = sorted({tuple(e) for e in cm.get_edges()} | {(b, a) for a, b in cm.get_edges()})
    return Device(spec, cm.size(), edges, list(ABSTRACT_BASIS))
