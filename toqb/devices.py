"""Devices: IBM fake backends (with their Target) and abstract coupling maps (no Target, no noise).

Spec strings:
    fake:FakeTorino        a qiskit_ibm_runtime fake backend
    linear:N               a line of N qubits
    grid:RxC               an R x C square grid
    heavyhex:D             Qiskit's heavy-hex map of distance D
    full:N                 all-to-all on N qubits
    psfos:FOLDER           a psf-os device record (FOLDER/device.json): geometry and failed marks only
    file:PATH              a Target saved with pickle (`toqb.s2rc_device fetch`: a device's Target on one day)
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


def failmark_target(dev_json):
    """A Qiskit Target from a psf-os device record (device.json: couplers, failed couplers, failed qubits): every
    coupler and qubit of the geometry, with error 1.0 on the failed ones and no other number anywhere (no error, no
    duration). It carries exactly the information TOQB's arms read from a full Target through the failed mark
    (`toqb.fold` bad / `_all_pairs`, `toqb.task_loop.blind_device`), and nothing else. (2026-11-10, classifier.)"""
    from qiskit.circuit import Delay, Measure, Parameter
    from qiskit.circuit.library import CZGate, RZGate, SXGate, XGate
    from qiskit.transpiler import InstructionProperties, Target
    n = int(dev_json["num_qubits"])
    fq = {int(q) for q in dev_json.get("failed_qubits", [])}
    fc = {tuple(sorted(map(int, e))) for e in dev_json.get("failed_couplers", [])}

    def props(bad):
        return InstructionProperties(error=1.0) if bad else InstructionProperties()
    t = Target(num_qubits=n)
    for gate in (SXGate(), XGate(), RZGate(Parameter("theta")), Measure(), Delay(Parameter("t"))):
        t.add_instruction(gate, {(q,): props(q in fq) for q in range(n)})
    cz = {}
    for a, b in dev_json["couplers"]:
        a, b = int(a), int(b)
        bad = tuple(sorted((a, b))) in fc
        cz[(a, b)] = props(bad)
        cz[(b, a)] = props(bad)
    t.add_instruction(CZGate(), cz)
    return t


def get_device(spec: str) -> Device:
    kind, _, arg = spec.partition(":")
    if kind == "psfos":  # a psf-os device record folder (device.json): failed marks only
        import json
        import os
        d = json.load(open(os.path.join(arg, "device.json")))
        return from_target(spec, failmark_target(d), True)
    if kind == "bp":
        from toqb.benchpress_source import build
        _, backend, _ = build(arg)
        return from_target(spec, backend.target, type(backend).__name__ != "FlexibleBackend")
    if kind == "file":
        import pickle
        with open(arg, "rb") as f:
            target = pickle.load(f)
        return from_target(spec, target, True)
    if kind == "snapshot" and arg == "marrakesh":
        # The stand-in's own calibration as published (toqb.s2r.SNAPSHOT, ibm_marrakesh, 2026-10-13) without the
        # stand-in's deliberate deviations (T1 / T2 scaling, over-rotation, ZZ): the twin a user would build from the
        # device's published calibration (design C's rehearsal).
        from toqb.s2r import standin_target
        return from_target(spec, standin_target(0.0, 0, 4e-9), True)
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
