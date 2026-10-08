"""Benchpress transpilation tests as TOQB cases and devices, built as Benchpress's Qiskit gym builds them
(Benchpress commit b695f30): the same input circuit (QASM file, or one PauliEvolutionGate for a HamLib instance) and
the same backend (FlexibleBackend on an abstract map, or the configured fake device, FakeTorino).

Case and device specs both take the form "bp:<test id>", e.g. "bp:test_QASMBench_small[adder_n4-linear]". The clone
is found from $TOQB_BENCHPRESS.

The standard set is a stratified sample of these tests, drawn by `sample` from a seed that is committed (its SHA-256)
before a run and published after it. The 152 tests that PSF-Zero's development used (data/psf_zero_dev_tests.txt;
the PSF-Zero record, Addenda 377-392) are excluded from the sample, so that its author's compiler was not tuned on it.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

TOPOS = ("all-to-all", "square", "heavy-hex", "linear")
SUMMIT = ("test_BV_100_transpile", "test_BVlike_simplification_transpile", "test_QAOA_100_transpile",
          "test_QFT_100_transpile", "test_QV_100_transpile", "test_circSU2_100_transpile", "test_circSU2_89_transpile",
          "test_clifford_100_transpile", "test_square_heisenberg_100_transpile")
STANDARD_K = {"QASMBench small": 8, "QASMBench medium": 6, "QASMBench large": 6, "HamLib": 7,
              "HamLib, FakeTorino": 10, "Feynman, FakeTorino": 8, "100-qubit, FakeTorino": 0}
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DEV_TESTS = os.path.join(DATA, "psf_zero_dev_tests.txt")
# the 1,032 tests with results published by the Benchpress authors (branch previous_results, commit f87a12a,
# Qiskit 2.5.0rc1 and TKET 2.18.0); the other 22 at b695f30 are tests Benchpress does not run, such as HamLib
# instances wider than FakeTorino
PUBLISHED = os.path.join(DATA, "benchpress_published_b695f30.txt")


def clone():
    bp = os.environ.get("TOQB_BENCHPRESS")
    if not bp:
        raise RuntimeError("set TOQB_BENCHPRESS to a Benchpress clone (commit b695f30)")
    return bp


def strata(bp):
    """{stratum: [(test id, kind, builder argument)]} for every Benchpress transpilation test (1,032 at b695f30).
    Reads files only; needs no quantum package."""
    root = os.path.join(bp, "benchpress")

    def qasm(sub):
        out = {}
        for r, _, files in os.walk(os.path.join(root, "qasm", sub)):
            for f in files:
                if f.endswith(".qasm") and "transpiled" not in f:
                    out[f.split(".")[0]] = os.path.join(r, f)
        return out

    S = {}
    for size in ("small", "medium", "large"):
        names = qasm("qasmbench-" + size)
        for t in TOPOS:
            S[f"QASMBench {size}, {t}"] = [(f"test_QASMBench_{size}[{n}-{t}]", "qasmbench", [p, t])
                                           for n, p in sorted(names.items())]
    with open(os.path.join(root, "hamiltonian", "hamlib", "100_representative.json"), encoding="utf-8") as fh:
        hams = json.load(fh)
    for t in TOPOS:
        S[f"HamLib, {t}"] = [(f"test_hamiltonians[ham_{h['ham_instance'][1:-1]}-{t}]", "ham_abstract",
                              [h["ham_instance"], t]) for h in hams]
    S["HamLib, FakeTorino"] = [(f"test_hamlib_hamiltonians_transpile[ham_{h['ham_instance'][1:-1]}]", "ham_device",
                                h["ham_instance"]) for h in hams]
    S["Feynman, FakeTorino"] = [(f"test_feynman_transpile[{f}]", "feynman", f)
                                for f in sorted(os.listdir(os.path.join(root, "qasm", "feynman"))) if f.endswith(".qasm")]
    S["100-qubit, FakeTorino"] = [(i, "summit", i) for i in SUMMIT]
    return S


def index(bp):
    return {tid: (s, kind, arg) for s, tests in strata(bp).items() for tid, kind, arg in tests}


def _ids(path):
    with open(path, encoding="utf-8") as fh:
        return {ln.strip() for ln in fh if ln.strip()}


def dev_tests():
    return _ids(DEV_TESTS)


def published():
    return _ids(PUBLISHED)


def seed_commitment(seed: str) -> str:
    return hashlib.sha256(("TOQB-seed|" + seed.strip()).encode("utf-8")).hexdigest()


def sample(bp, seed: str, k=None):
    """[(stratum, test id)]: in each stratum, the published tests not in PSF-Zero's development set, ordered by
    SHA-256("TOQB-standard|" + seed + "|" + id), the first k[stratum] (k from STANDARD_K by stratum family)."""
    k = k or STANDARD_K
    excluded, pub = dev_tests(), published()
    out = []
    for name, tests in strata(bp).items():
        n = k.get(name, k.get(name.split(",")[0], 0))
        keep = sorted((t for t in tests if t[0] in pub and t[0] not in excluded),
                      key=lambda t: hashlib.sha256(f"TOQB-standard|{seed.strip()}|{t[0]}".encode()).hexdigest())
        out += [(name, t[0]) for t in keep[:n]]
    return out


def _setup(bp):
    if bp not in sys.path:
        sys.path.insert(0, bp)
    from benchpress.config import Configuration
    Configuration.gym_name = "qiskit"
    return Configuration


def build(test_id):
    """(circuit, backend, stratum) for a test id, as Benchpress's Qiskit gym builds them."""
    bp = clone()
    stratum, kind, arg = index(bp)[test_id]
    cfg = _setup(bp)
    from qiskit import QuantumCircuit
    from benchpress.utilities.backends import FlexibleBackend
    if kind == "qasmbench":
        qc = QuantumCircuit.from_qasm_file(arg[0])
        return qc, FlexibleBackend(qc.num_qubits, arg[1], control_flow=True), stratum
    if kind in ("ham_abstract", "ham_device"):
        from qiskit.circuit.library import PauliEvolutionGate
        from qiskit.quantum_info import SparsePauliOp
        inst = arg[0] if kind == "ham_abstract" else arg
        with open(cfg.get_hamiltonian_dir("hamlib") + "100_representative.json", encoding="utf-8") as fh:
            h = next(x for x in json.load(fh) if x["ham_instance"] == inst)
        op = SparsePauliOp(h["ham_hamlib_hamiltonian_terms"], h["ham_hamlib_hamiltonian_coefficients"])
        qc = QuantumCircuit(op.num_qubits)
        qc.append(PauliEvolutionGate(op, time=1), range(op.num_qubits))
        if kind == "ham_abstract":
            return qc, FlexibleBackend(qc.num_qubits, arg[1], control_flow=True), stratum
        return qc, cfg.backend(), stratum
    if kind == "feynman":
        return QuantumCircuit.from_qasm_file(cfg.get_qasm_dir("feynman") + arg), cfg.backend(), stratum
    if kind == "summit":
        from qiskit.circuit.library import EfficientSU2, QuantumVolume
        from benchpress.qiskit_gym.circuits import bv_all_ones, trivial_bvlike_circuit
        q = cfg.get_qasm_dir
        qc = {"test_BV_100_transpile": lambda: bv_all_ones(100),
              "test_BVlike_simplification_transpile": lambda: trivial_bvlike_circuit(100),
              "test_QAOA_100_transpile": lambda: QuantumCircuit.from_qasm_file(
                  q("qaoa") + "qaoa_barabasi_albert_N100_3reps.qasm"),
              "test_QFT_100_transpile": lambda: QuantumCircuit.from_qasm_file(q("qft") + "qft_N100.qasm"),
              "test_QV_100_transpile": lambda: QuantumVolume(100, 100, seed=12345),
              "test_circSU2_100_transpile": lambda: EfficientSU2(100, reps=3, entanglement="circular"),
              "test_circSU2_89_transpile": lambda: EfficientSU2(89, reps=3, entanglement="circular"),
              "test_clifford_100_transpile": lambda: QuantumCircuit.from_qasm_file(
                  q("clifford") + "clifford_100_12345.qasm"),
              "test_square_heisenberg_100_transpile": lambda: QuantumCircuit.from_qasm_file(
                  q("square-heisenberg") + "square_heisenberg_N100.qasm")}[arg]()
        return qc, cfg.backend(), stratum
    raise ValueError(kind)
