"""TOQB's PennyLane device: a QNode's circuits compiled by the compiler under test and run on TOQB noise, with what each
execution would cost on IBM hardware.

    import pennylane as qml
    from toqb.pennylane_device import CompiledDevice

    dev = CompiledDevice(wires=4, compiler="psfai:template", backend="fake:FakeFez", seed=1)

    @qml.set_shots(400)
    @qml.qnode(dev)
    def model(x, w):
        ...
        return qml.expval(qml.PauliZ(0))

    with qml.Tracker(dev) as tracker:
        model(x, w)
    tracker.totals  # executions, shots, compile_s, qpu_s (batch mode), usd (batch mode)

`compiler` is a TOQB loop arm (`toqb.task_loop.make_loop_arm`): "qiskit:L:target:template",
"qiskit:L:target:recompile", "psfai:template" or "psfai:recompile". Every execution measures all wires (as hardware
samples every qubit) and returns what PennyLane asked for from those counts, through PennyLane's own
`diagonalize_measurements` and `measurements_from_counts`. Shots are required. Gradients are not computed by the
device: use a gradient-free optimiser (qml.SPSAOptimizer) or a shot-based rule such as parameter shift.
"""
from __future__ import annotations

import time

import pennylane as qml
from pennylane.devices import Device
from pennylane.devices.preprocess import (decompose, diagonalize_measurements, measurements_from_counts,
                                          validate_device_wires, validate_measurements)

# PennyLane operation -> (Qiskit gate method, number of parameters)
GATES = {"RX": ("rx", 1), "RY": ("ry", 1), "RZ": ("rz", 1), "PhaseShift": ("p", 1), "IsingZZ": ("rzz", 1),
         "CZ": ("cz", 0), "CNOT": ("cx", 0), "SWAP": ("swap", 0), "Hadamard": ("h", 0), "PauliX": ("x", 0),
         "PauliY": ("y", 0), "PauliZ": ("z", 0), "S": ("s", 0), "T": ("t", 0), "SX": ("sx", 0),
         "Identity": ("id", 0)}


def tape_to_qiskit(tape, wire_order):
    """The tape's operations as a Qiskit circuit on qubits in `wire_order`, every qubit measured at the end
    (`measure_all`, clbit k = qubit k), as TOQB's Qiskit front end builds its circuits."""
    from qiskit import QuantumCircuit
    index = {w: k for k, w in enumerate(wire_order)}
    qc = QuantumCircuit(len(wire_order))
    for op in tape.operations:
        name, npar = GATES[op.name]
        params = [float(p) for p in op.parameters[:npar]]
        getattr(qc, name)(*params, *[index[w] for w in op.wires])
    qc.measure_all()
    return qc


def _counts_for(qiskit_counts, wire_order, wires):
    """Qiskit counts (clbit 0 rightmost) marginalised to `wires`, keyed as PennyLane keys them (first wire first)."""
    pos = [wire_order.index(w) for w in wires]
    out = {}
    for key, v in qiskit_counts.items():
        bits = key.replace(" ", "")[::-1]  # bits[k] = clbit k = wire_order[k]
        k = "".join(bits[p] for p in pos)
        out[k] = out.get(k, 0) + v
    return out


class CompiledDevice(Device):
    """See the module's description."""

    name = "toqb.compiled"

    def __init__(self, wires, compiler="psfai:template", backend="fake:FakeFez", shots=None, seed=0, executor=None,
                 qpu_cost=None):
        super().__init__(wires=wires, shots=shots)
        from toqb.task_loop import DEFAULT_COST, Executor, make_loop_arm
        if executor is None:
            from toqb.devices import get_device
            device = get_device(backend)
            arm = make_loop_arm(compiler)
            arm.setup(device.target)
            executor = Executor(arm, device)
        self.executor = executor
        self.cost = dict(DEFAULT_COST, **(qpu_cost or {}))
        self.seed = seed
        self._count = 0
        self.next_seeds = None  # set by TOQB's loop to fix each circuit's shot seed
        self.check_first = False

    def preprocess_transforms(self, execution_config=None):
        program = qml.CompilePipeline() if hasattr(qml, "CompilePipeline") else qml.transforms.core.TransformProgram()
        program.add_transform(validate_device_wires, self.wires, name=self.name)
        program.add_transform(validate_measurements, name=self.name)
        program.add_transform(diagonalize_measurements)
        program.add_transform(measurements_from_counts)
        program.add_transform(decompose, stopping_condition=lambda op: op.name in GATES, name=self.name)
        return program

    def execute(self, circuits, execution_config=None):
        wire_order = list(self.wires)
        qcs, shots = [], None
        for tape in circuits:
            if not tape.shots:
                raise qml.DeviceError("toqb.compiled needs shots (qml.set_shots or the device's shots)")
            s = tape.shots.total_shots
            if shots is not None and s != shots:
                raise qml.DeviceError("one batch of circuits must share its number of shots")
            shots = s
            qcs.append(tape_to_qiskit(tape, wire_order))
        seeds = self.next_seeds or [self.seed * 1_000_003 + self._count + j for j in range(len(qcs))]
        self.next_seeds = None
        self._count += len(qcs)
        ex = self.executor
        c0 = ex.compile_s
        counts = ex.run(qcs, shots, seeds, check_first=self.check_first)
        results = tuple(_counts_for(c, wire_order, tape.measurements[0].wires or wire_order)
                        for c, tape in zip(counts, circuits))
        if self.tracker.active:
            from toqb.task_loop import qpu_seconds
            qpu = qpu_seconds(ex.last_durations, shots, self.cost)
            self.tracker.update(executions=len(qcs), shots=shots * len(qcs), compile_s=ex.compile_s - c0, qpu_s=qpu,
                                usd=qpu * self.cost["usd_per_s"], time=time.time())
            self.tracker.record()
        return results
