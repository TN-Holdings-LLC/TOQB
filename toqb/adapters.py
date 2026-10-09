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
    in `metadata` (for the equivalence check).

    The input is converted with qiskit_to_tk. Two things come first (`_tk_input`):
      - a gate defined in the input itself (QASMBench's ctu or add4, say) is expanded through its definition
        (`_expand_custom`), as pytket's own QASM reader does in Benchpress's TKET gym;
      - a PauliEvolutionGate becomes TKET's own first-order product formula (gen_term_sequence_circuit, which groups
        the terms into commuting sets and orders them; Benchpress's TKET gym builds its Hamiltonian circuits the same
        way), with Qiskit's conventions for the gate (U = exp(-i t H); character k of a Pauli label acts on the
        gate's qubit n-1-k). The formula differs from Qiskit's, which keeps the terms in order, so the output is
        checked against TKET's reading (`reference_input`).
    Classical control (conditions on measured bits) is not supported: such an input or output is recorded as a
    failure of this adapter, not of TKET."""

    def __init__(self, level: int):
        self.level = level
        self.name = f"tket:{level}"

    def version(self):
        import pytket
        import pytket.extensions.qiskit as pq
        return f"pytket {pytket.__version__}, pytket-qiskit {getattr(pq, '__extension_version__', '?')}"

    @staticmethod
    def _units(circuit):
        """The pytket Qubit and Bit for each Qiskit qubit and clbit, named (register, index) as qiskit_to_tk names
        them."""
        from pytket import Bit, Qubit

        def name(b):
            loc = circuit.find_bit(b)
            if not loc.registers:
                raise ValueError("a bit outside every register")
            reg, k = loc.registers[0]
            return reg.name, k
        return [Qubit(*name(b)) for b in circuit.qubits], [Bit(*name(b)) for b in circuit.clbits]

    @staticmethod
    def _peg_box(peg):
        """TKET's first-order product formula for a PauliEvolutionGate, as a CircBox on the gate's qubits in order."""
        import math
        from pytket import Circuit, Qubit
        from pytket.circuit import CircBox
        from pytket.pauli import Pauli, QubitPauliString
        from pytket.utils import QubitPauliOperator, gen_term_sequence_circuit
        from qiskit.quantum_info import SparsePauliOp
        syn = peg.synthesis
        if type(syn).__name__ != "LieTrotter" or getattr(syn, "reps", 1) != 1:
            raise ValueError(f"PauliEvolutionGate with {type(syn).__name__}, reps {getattr(syn, 'reps', '?')}")
        if not isinstance(peg.operator, SparsePauliOp):
            raise ValueError("PauliEvolutionGate on a list of operators")
        t, n = float(peg.params[0]), peg.num_qubits
        letters = {"X": Pauli.X, "Y": Pauli.Y, "Z": Pauli.Z}
        terms = {}
        for label, c in peg.operator.to_list():
            if abs(complex(c).imag) > 1e-12:
                raise ValueError(f"complex coefficient for {label}")
            qps = QubitPauliString({Qubit(n - 1 - k): letters[ch] for k, ch in enumerate(label) if ch != "I"})
            # gen_term_sequence_circuit approximates exp(-i pi/2 P): a coefficient 2 t c / pi gives exp(-i t c P)
            terms[qps] = terms.get(qps, 0.0) + 2 * t * float(complex(c).real) / math.pi
        return CircBox(gen_term_sequence_circuit(QubitPauliOperator(terms), Circuit(n)))

    # instructions qiskit_to_tk takes as they are; anything else (a gate defined in the input's QASM file, such as
    # QASMBench's ctu or add4) is expanded through its definition first, as pytket's own QASM reader does in
    # Benchpress's TKET gym
    PASS_THROUGH = {"measure", "barrier", "reset", "delay", "PauliEvolution", "unitary", "if_else", "while_loop",
                    "for_loop", "switch_case", "store", "initialize", "state_preparation"}

    @classmethod
    def _expand_custom(cls, circuit):
        from qiskit.circuit.library.standard_gates import get_standard_gate_name_mapping
        known = set(get_standard_gate_name_mapping()) | cls.PASS_THROUGH
        for _ in range(20):
            names = sorted({i.operation.name for i in circuit.data} - known)
            if not names:
                break
            circuit = circuit.decompose(gates_to_decompose=names)
        return circuit

    def _tk_input(self, circuit):
        from pytket.extensions.qiskit import qiskit_to_tk
        circuit = self._expand_custom(circuit)
        if not any(i.operation.name == "PauliEvolution" for i in circuit.data):
            return qiskit_to_tk(circuit)
        qs, _ = self._units(circuit)
        tk = qiskit_to_tk(circuit.copy_empty_like())
        run = None
        for ins in list(circuit.data) + [None]:
            if ins is not None and ins.operation.name != "PauliEvolution":
                if run is None:
                    run = circuit.copy_empty_like()
                    run.global_phase = 0
                run.append(ins)
                continue
            if run is not None:
                tk.append(qiskit_to_tk(run))
                run = None
            if ins is not None:
                tk.add_circbox(self._peg_box(ins.operation), [qs[circuit.find_bit(b).index] for b in ins.qubits])
        return tk

    def reference_input(self, circuit):
        """The input as TKET reads it, as a Qiskit circuit on the input's qubits and clbits, when that differs from
        Qiskit's reading (a PauliEvolutionGate); None otherwise."""
        if not any(i.operation.name == "PauliEvolution" for i in circuit.data):
            return None
        from pytket.extensions.qiskit import tk_to_qiskit
        from pytket.passes import DecomposeBoxes
        from qiskit import QuantumCircuit
        tk = self._tk_input(circuit)
        DecomposeBoxes().apply(tk)
        try:
            qc = tk_to_qiskit(tk, replace_implicit_swaps=True)
        except TypeError:
            tk.replace_implicit_wire_swaps()
            qc = tk_to_qiskit(tk)
        # back onto the input's own qubit and clbit order, matched by (register, index)
        qpos = {(r.name, k): circuit.find_bit(b).index for r in circuit.qregs for k, b in enumerate(r)}
        cpos = {(r.name, k): circuit.find_bit(b).index for r in circuit.cregs for k, b in enumerate(r)}

        def where(bit, pos):
            reg, k = qc.find_bit(bit).registers[0]
            return pos[(reg.name, k)]
        out = QuantumCircuit(circuit.num_qubits, circuit.num_clbits, global_phase=qc.global_phase)
        for ins in qc.data:
            out.append(ins.operation, [where(b, qpos) for b in ins.qubits], [where(b, cpos) for b in ins.clbits])
        return out

    def compile(self, circuit, device):
        from pytket import OpType
        from pytket.architecture import Architecture
        from pytket.backends.backendinfo import BackendInfo
        from pytket.extensions.qiskit import IBMQBackend
        from pytket.predicates import CompilationUnit
        ops = {"cz": OpType.CZ, "cx": OpType.CX, "ecr": OpType.ECR, "rz": OpType.Rz, "sx": OpType.SX,
               "x": OpType.X}
        gateset = {ops[g] for g in device.basis if g in ops} | {OpType.Measure, OpType.Barrier, OpType.Reset}
        info = BackendInfo("toqb", device.spec, "0", Architecture(list(device.edges)), gateset)
        inputs, bits = self._units(circuit)  # the pytket units of the input's qubits and clbits, in Qiskit's order
        cu = CompilationUnit(self._tk_input(circuit))
        IBMQBackend.pass_from_info(info, optimisation_level=self.level).apply(cu)
        out = self._to_qiskit(cu.circuit, device, circuit.num_clbits, {b: i for i, b in enumerate(bits)})
        out.metadata = dict(toqb_initial=[cu.initial_map[q].index[0] for q in inputs],
                            toqb_final=[cu.final_map[q].index[0] for q in inputs])
        return out

    @staticmethod
    def _to_qiskit(tk, device, num_clbits, bit):
        """Rebuild the circuit gate by gate on the device's qubit indices (TKET's node index), so that the output's
        qubit i is the device's qubit i, and clbit j is the input's clbit j. Angles in TKET are in half-turns."""
        import math
        from pytket import OpType
        from qiskit import QuantumCircuit
        qc = QuantumCircuit(device.num_qubits, num_clbits)
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
