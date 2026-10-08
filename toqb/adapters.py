"""Compiler adapters. An adapter has `name`, `version()` and `compile(circuit, device)`; it must return a circuit on
the device's qubits that uses only the device's basis.

Spec strings:
    qiskit:L             Qiskit preset pass manager, level L, with coupling map and basis only
    qiskit:L:target      the same with the device's Target (fake devices; falls back to map and basis otherwise)
    tket:L               pytket (needs pytket and pytket-qiskit), see TketAdapter
    psf:default          PSF-Zero's default call (path from $PSF_ZERO_REPO)
    psf:recommended      PSF-Zero's recommended call with the device's Target (the default call on a device without one,
                         as qiskit:L:target falls back to map and basis)
    ext:pkg.module:fn    an external adapter: fn(arg) -> adapter, with arg the rest of the spec after a second ':'

The reference compiler of TOQB is "qiskit:2:target" (Benchpress's call passes the backend, and so its Target).
"""
from __future__ import annotations

import contextlib
import importlib
import importlib.util
import io
import os
import sys


class QiskitAdapter:
    def __init__(self, level: int, use_target: bool):
        self.level, self.use_target = level, use_target
        self.name = f"qiskit:{level}" + (":target" if use_target else "")

    def version(self):
        import qiskit
        return qiskit.__version__

    def compile(self, circuit, device):
        from qiskit.transpiler import CouplingMap
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
        if self.use_target and device.target is not None:
            pm = generate_preset_pass_manager(self.level, target=device.target, seed_transpiler=0)
        else:
            pm = generate_preset_pass_manager(self.level, coupling_map=CouplingMap(device.edges),
                                              basis_gates=device.basis, seed_transpiler=0)
        return pm.run(circuit)


class TketAdapter:
    """TKET as its own IBM backend compiles: the default compilation pass of pytket-qiskit's IBMQBackend at the given
    optimisation level (`IBMQBackend.pass_from_info`), built offline from the device's architecture and gate set, so
    no IBM account is needed. At level 2 that is DecomposeBoxes, FullPeepholeOptimise, a rebase, LightSABRE routing,
    KAKDecomposition, CliffordSimp, SynthesiseTket, a rebase, a squash and RemoveRedundancies. The output is rebuilt
    in Qiskit on the device's qubit indices (`_to_qiskit`), with the initial and final placement of each input qubit
    in `metadata` (for the equivalence check)."""

    def __init__(self, level: int):
        self.level = level
        self.name = f"tket:{level}"

    def version(self):
        import pytket
        import pytket.extensions.qiskit as pq
        return f"pytket {pytket.__version__}, pytket-qiskit {getattr(pq, '__extension_version__', '?')}"

    def compile(self, circuit, device):
        from pytket import OpType
        from pytket.architecture import Architecture
        from pytket.backends.backendinfo import BackendInfo
        from pytket.extensions.qiskit import IBMQBackend, qiskit_to_tk
        from pytket.predicates import CompilationUnit
        ops = {"cz": OpType.CZ, "cx": OpType.CX, "ecr": OpType.ECR, "rz": OpType.Rz, "sx": OpType.SX,
               "x": OpType.X}
        gateset = {ops[g] for g in device.basis if g in ops} | {OpType.Measure, OpType.Barrier, OpType.Reset}
        info = BackendInfo("toqb", device.spec, "0", Architecture(list(device.edges)), gateset)
        tk = qiskit_to_tk(circuit)
        inputs = list(tk.qubits)  # q[0], q[1], ... in the input's order
        cu = CompilationUnit(tk)
        IBMQBackend.pass_from_info(info, optimisation_level=self.level).apply(cu)
        out = self._to_qiskit(cu.circuit, device)
        out.metadata = dict(toqb_initial=[cu.initial_map[q].index[0] for q in inputs],
                            toqb_final=[cu.final_map[q].index[0] for q in inputs])
        return out

    @staticmethod
    def _to_qiskit(tk, device):
        """Rebuild the circuit gate by gate on the device's qubit indices (TKET's node index), so that the output's
        qubit i is the device's qubit i. Angles in TKET are in half-turns."""
        import math
        from pytket import OpType
        from qiskit import QuantumCircuit
        qc = QuantumCircuit(device.num_qubits, len(tk.bits))
        bit = {b: i for i, b in enumerate(tk.bits)}
        names = {OpType.CZ: "cz", OpType.CX: "cx", OpType.ECR: "ecr", OpType.SX: "sx", OpType.X: "x"}
        for cmd in tk.get_commands():
            t = cmd.op.type
            qs = [a.index[0] for a in cmd.args if a in tk.qubits]
            if t == OpType.Rz:
                qc.rz(float(cmd.op.params[0]) * math.pi, qs[0])
            elif t in names:
                getattr(qc, names[t])(*qs)
            elif t == OpType.Measure:
                qc.measure(qs[0], bit[cmd.args[1]])
            elif t == OpType.Barrier:
                qc.barrier(*qs)
            elif t == OpType.Reset:
                qc.reset(qs[0])
            else:
                raise ValueError(f"TKET returned {t}, outside the device's basis")
        qc.global_phase = float(tk.phase) * math.pi
        return qc


class PSFZeroAdapter:
    """PSF-Zero's calls as its README gives them. The compiler file is loaded from $PSF_ZERO_REPO."""

    RECOMMENDED = dict(placement_refine=True, final_resynthesis="select", compare_level3=True, compare_floor=True,
                       candidate_score="hybrid")

    def __init__(self, call: str):
        if call not in ("default", "recommended"):
            raise ValueError(f"PSF-Zero call {call!r}")
        self.call, self.name = call, f"psf:{call}"
        repo = os.environ.get("PSF_ZERO_REPO")
        if not repo:
            raise RuntimeError("set PSF_ZERO_REPO to a PSF-Zero checkout")
        sys.path[:0] = [os.path.join(repo, "benchmarks"), repo]
        spec = importlib.util.spec_from_file_location("psf_compile", os.path.join(repo, "psf_compile.py"))
        self.mod = importlib.util.module_from_spec(spec)
        sys.modules["psf_compile"] = self.mod
        spec.loader.exec_module(self.mod)

    def version(self):
        return self.mod.VERSION

    def compile(self, circuit, device):
        from qiskit.transpiler import CouplingMap
        kw = dict(coupling_map=CouplingMap(device.edges), basis_gates=device.basis, entangling_basis="cx",
                  layout_search=True, seed_transpiler=0)
        if self.call == "recommended" and device.target is not None:
            kw.update(target=device.target, **self.RECOMMENDED)  # without a Target: the default call, as Qiskit's
        with contextlib.redirect_stdout(io.StringIO()):
            return self.mod.compile_for_hardware(circuit, **kw)


def make_adapter(spec: str):
    kind, _, rest = spec.partition(":")
    if kind == "qiskit":
        level, _, opt = rest.partition(":")
        return QiskitAdapter(int(level), opt == "target")
    if kind == "tket":
        return TketAdapter(int(rest or 2))
    if kind == "psf":
        return PSFZeroAdapter(rest)
    if kind == "ext":
        module, _, tail = rest.partition(":")
        fn, _, arg = tail.partition(":")
        return getattr(importlib.import_module(module), fn)(arg)
    raise ValueError(f"unknown adapter spec {spec!r}")
