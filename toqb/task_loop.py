"""TOQB layer 3, the variational-loop scenario (v15): for the same money, which compiler returns the best model?

A classifier is trained by SPSA on a noisy device model, and every circuit of every iteration is compiled by the
compiler under test. Each iteration is one job of 2 x B circuits (the SPSA pair over a batch of B training points).
A compiler's output noise enters every gradient, so better circuits can give a better model for the same number of
jobs; and in session mode its compile time is paid in QPU time too. Both are priced in QPU seconds and dollars.

The task (identical for every arm; nothing depends on the compiler but the circuits):
  - model: data re-uploading on a ring (DEPTH1's / RING1's classifier). Per layer: RY(enc x_q) on every qubit, then
    RY(a_q) RZ(b_q) on every qubit, then a CZ ring (0,1) ... (n-1,0); after the last layer RY(c_q); measure all. The
    prediction is sign(<Z_0>).
  - data: a teacher-student task. A teacher of the same model with angles drawn from `teacher_seed` labels uniform
    points x in [-1, 1]^n by the sign of its <Z_0>; points with |<Z_0>| < `teacher_gap` are dropped. So the task is
    learnable by the model, and what an arm reaches depends on the optimisation and the noise, not on luck in the
    data. Drawn with numpy only (no scikit-learn).
  - loss: mean over the batch of (1 - y z) / 2. SPSA with gains a_k = a / (k + 1 + A)^0.602, c_k = c / (k + 1)^0.101;
    the batch, the perturbation and the initial angles come from `loop_seed` and are the same for every arm.
  - the device model ("TOQB noise"): each compiled circuit is scheduled ALAP with the device's durations (idle time
    becomes delays), reduced to the qubits it uses, and run on Aer's density-matrix simulator with, per qubit and
    coupler of the device's Target: a depolarizing error of the reported gate error composed with thermal relaxation
    (T1, T2) over the gate's duration; thermal relaxation over every delay; the reported readout error. Shots are
    sampled with a seed fixed per (iteration, circuit), the same for every arm.

Front ends (`frontend` in the plan): "qiskit" builds each circuit as a Qiskit circuit; "pennylane" builds it as a
PennyLane tape returning qml.expval(qml.PauliZ(0)) and runs it through `toqb.pennylane_device.CompiledDevice`, the
PennyLane device a QML developer would use. Both hand the compilers the same Qiskit circuit.

Engines (`engine` in the plan, default "aer"): "aer" asks Aer for the counts of each circuit, as every scored run so
far. "fast" (`toqb.fast_noise`) evolves the same noisy circuit exactly with numpy, once scheduled per circuit
structure and batched, and draws the shots of clbit 0 from the exact probability: the same distribution, not the
same random stream. It measures only clbit 0 (the loop's <Z0>). `python -m toqb.check_fast_noise` checks it against
an exact reference and against Aer.

A hard QPU budget (`evaluation.stop_budget_usd`, batch mode): training stops before the job that would pass it, and
the model it bought is evaluated there (`rec["stop"]`). Without it, the budget of the report is the reference arm's
own spend plus a tolerance, which never binds.

Arms ("compiler:mode"):
  qiskit:L:target:template   Qiskit's loop practice: the circuit with every angle a Parameter, transpiled once at
                             level L with the device's Target (per circuit structure); each circuit is bound.
  qiskit:L:target:recompile  the concrete circuit transpiled every time.
  psfai:template             PSF-Zero's AI front end: its template built once per structure (`model_template`
                             from a22 on, else `ring_template`), `bind` each time (a structure without a template is
                             compiled by `compile_for_model_circuit`, and counted).
  psfai:recompile            `compile_for_model_circuit` every time.
The PSF-Zero files come from $PSF_ZERO_REPO: psf_compile.py ($PSF_COMPILE_FILE, default the release at its root) and
the front end ($PSF_AI_FILE, default patches/psf_ai_compile_a25_2026-10-25/psf_ai_compile.py since 2026-10-25, a24
from 2026-10-24, a22 before; a25 is a24 with the zipper also for odd n, results/zipper-odd-2026-10-25, and needs
psfbind ring r3). a24 builds the ring template in Rust (psfbind ring r2: $PSF_BIND_LIB or rust/psfbind/target/release)
and has the zipper as an option; TOQB runs `psfai:template` with the option off and `psfai:template_zip` with it on
(PSF_RING_ZIP set per call). On the marrakesh snapshot a24 builds both arms' circuits instruction for instruction as
a22 / c61 with toqb.ring_zip did (results/a24-identity-2026-10-24). Earlier runs set a22 and c61
(patches/psf_compile_c61_2026-10-15/psf_compile.py as $PSF_COMPILE_FILE) explicitly in their scripts.

Price (the plan's `qpu_cost`; defaults: IBM's measured rate in PSF-Zero's TIME1 and FRAC1 runs, 0.27 ms per shot and
0.036 s per circuit, and the Pay-As-You-Go price, $96 per minute):
  - batch mode (only time on the QPU is billed): per circuit, per_circuit_s + shots x (per_shot_s + the circuit's
    duration);
  - session mode (wall-clock time while the QPU is committed to the session is billed): the same, plus the classical
    time of each iteration between jobs -- compiling, binding, the front end, the optimiser -- which the arm pays and
    the QPU waits for. TOQB's own checks and the simulation (which stands in for the QPU) are not counted.
Only training jobs are priced; the evaluations on the test set are reported at the price spent so far.

Energy (the plan's `energy`, a reference, not a measurement): a quantum arm is charged the system's whole wall-plug
power for the seconds its run holds the QPU (batch: QPU time; session: the session's time), at `qpu_system_kw` (a range,
default 10-25 kW, superconducting systems' power as cited in arXiv 2605.09580), plus its classical seconds at `cpu_w`
(default 10-50 W, one CPU core, assumed). The classical reference models (`toqb.classical`: logistic regression, an
MLP, nearest neighbours, numpy only) are trained on the same points and charged their seconds at `cpu_w`. They are the
bar a quantum model is read against, not participants.

Measured per arm (one process each, one thread):
  - the result for the money: noisy test accuracy and margin at each evaluation with the dollars spent (both modes);
    the dollars to `target_accuracy`; the accuracy at the plan's `budget_usd`;
  - every output: the structural check, operations on failed elements, two-qubit count, duration; TOQB's equivalence
    check on the first circuit of the first, middle and last iteration (a failure there, or any structural failure or
    operation on a failed element, makes the arm invalid);
  - the cost of compiling (secondary): template builds plus binds, or every compile, against the reference arm's, in
    tiers 1x, 3x, 10x with the floor `budget_floor_s`.

    python -m toqb.task_loop run PLAN.json OUTDIR      every arm of the plan, one process each, then the report
    python -m toqb.task_loop arm PLAN.json OUTDIR SPEC one arm (what `run` starts)
    python -m toqb.task_loop classical PLAN.json OUTDIR the classical reference models (what `run` starts last)
    python -m toqb.score_loop OUTDIR                   the report again from the records
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import math
import os
import subprocess
import sys
import time

SINGLE_THREAD = {k: "1" for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "RAYON_NUM_THREADS",
                                  "QISKIT_NUM_PROCS", "NUMEXPR_NUM_THREADS")}
SINGLE_THREAD["QISKIT_PARALLEL"] = "FALSE"

DEFAULT_ENERGY = dict(qpu_system_kw=[10.0, 25.0], cpu_w=[10.0, 50.0],
                      attribution="time share: the system's whole power for the seconds a run holds the QPU",
                      source="10-25 kW: wall-plug power of superconducting systems (dilution refrigerators 10-25 kW "
                             "continuous) as cited in arXiv 2605.09580; 10-50 W: one CPU core, assumed")
DEFAULT_COST = dict(per_shot_s=0.00027, per_circuit_s=0.036, usd_per_s=96 / 60,
                    source="rate: PSF-Zero TIME1 / FRAC1 on ibm_fez (2026-10-14); price: IBM Pay-As-You-Go, "
                           "'starts at $96 USD / minute', billed per second (ibm.com/quantum/pricing, 2026-10-15)")


# ------------------------------------------------------------------------------------------------ task (numpy only)

def n_params(n, L):
    return 2 * n * L + n


def angle_list(theta, x, n, L, enc):
    """Every rotation angle of the model circuit, in the order its gates are appended (RY, RY, RZ, ..., RY)."""
    out, k = [], 0
    for _ in range(L):
        out += [enc * float(x[q]) for q in range(n)]
        for q in range(n):
            out += [float(theta[k]), float(theta[k + 1])]
            k += 2
    out += [float(theta[k + q]) for q in range(n)]
    return out


def gate_kinds(n, L):
    kinds = []
    for _ in range(L):
        kinds += ["ry"] * n + ["ry", "rz"] * n
    return kinds + ["ry"] * n


def model_circuit(angles, n, L):
    """The model as a Qiskit circuit; `angles` may be numbers or Parameters (from `angle_list`'s order)."""
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(n)
    it = iter(angles)
    for _ in range(L):
        for q in range(n):
            qc.ry(next(it), q)
        for q in range(n):
            qc.ry(next(it), q)
            qc.rz(next(it), q)
        for q in range(n):
            qc.cz(q, (q + 1) % n)
    for q in range(n):
        qc.ry(next(it), q)
    qc.measure_all()
    return qc


def model_ops(angles, n, L):
    """The model as PennyLane operations, in the same order as `model_circuit`."""
    import pennylane as qml
    ops, it = [], iter(angles)
    for _ in range(L):
        for q in range(n):
            ops.append(qml.RY(next(it), wires=q))
        for q in range(n):
            ops.append(qml.RY(next(it), wires=q))
            ops.append(qml.RZ(next(it), wires=q))
        for q in range(n):
            ops.append(qml.CZ(wires=[q, (q + 1) % n]))
    for q in range(n):
        ops.append(qml.RY(next(it), wires=q))
    return ops


def exact_z0(angles, n, L):
    """<Z_0> of the model without noise (numpy state vector)."""
    import numpy as np
    psi = np.zeros(2 ** n, dtype=complex)
    psi[0] = 1
    b = np.arange(2 ** n)
    ring = np.ones(2 ** n)
    for q in range(n):
        ring *= np.where(((b >> q) & 1) & ((b >> ((q + 1) % n)) & 1), -1, 1)

    def apply(psi, U, q):
        t = np.moveaxis(psi.reshape([2] * n), n - 1 - q, 0)
        s = t.shape
        t = (U @ t.reshape(2, -1)).reshape(s)
        return np.moveaxis(t, 0, n - 1 - q).reshape(-1)

    def ry(a):
        c, s = math.cos(a / 2), math.sin(a / 2)
        return np.array([[c, -s], [s, c]], dtype=complex)

    def rz(a):
        return np.diag([np.exp(-0.5j * a), np.exp(0.5j * a)])
    it = iter(angles)
    for _ in range(L):
        for q in range(n):
            psi = apply(psi, ry(next(it)), q)
        for q in range(n):
            psi = apply(psi, ry(next(it)), q)
            psi = apply(psi, rz(next(it)), q)
        psi = ring * psi
    for q in range(n):
        psi = apply(psi, ry(next(it)), q)
    p = np.abs(psi) ** 2
    return float(p[(b & 1) == 0].sum() - p[(b & 1) == 1].sum())


def teacher_data(task):
    """(X_train, y_train, X_test, y_test) of the teacher-student task (see the module's description)."""
    import numpy as np
    n, L, enc = task["n"], task["layers"], task["enc"]
    rng = np.random.default_rng(task["teacher_seed"])
    teacher = rng.uniform(-math.pi, math.pi, n_params(n, L))
    X, Y = [], []
    need = task["n_train"] + task["n_test"]
    while len(X) < need:
        x = rng.uniform(-1, 1, n)
        z = exact_z0(angle_list(teacher, x, n, L, enc), n, L)
        if abs(z) < task["teacher_gap"]:
            continue
        X.append(x)
        Y.append(1.0 if z > 0 else -1.0)
    X, Y = np.array(X), np.array(Y)
    ntr = task["n_train"]
    return X[:ntr], Y[:ntr], X[ntr:], Y[ntr:]


def spsa_schedule(task, opt):
    """(initial angles, [(batch indices, perturbation)] per iteration): drawn from `loop_seed` before any circuit runs,
    so every arm follows the same draws."""
    import numpy as np
    rng = np.random.default_rng(opt["loop_seed"])
    d = n_params(task["n"], task["layers"])
    theta0 = rng.uniform(-opt["init"], opt["init"], d)
    steps = []
    for _ in range(opt["iterations"]):
        idx = rng.choice(task["n_train"], opt["batch"], replace=False)
        steps.append((idx, rng.choice([-1, 1], d).astype(np.int8)))  # the same draws; compact for long runs
    return theta0, steps


def _cest_now():
    """The time in Central European time, as TOQB's records give it."""
    import datetime
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("Europe/Zurich")).strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:  # noqa: BLE001 - Windows without the tzdata package: central European summer time, fixed
        tz = datetime.timezone(datetime.timedelta(hours=2), "CEST")
        return datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z") + " (fixed +02:00)"


def gains(k, opt):
    return opt["a"] / (k + 1 + opt["A"]) ** 0.602, opt["c"] / (k + 1) ** 0.101


def qpu_seconds(durations_s, shots, cost):
    """Batch-mode QPU seconds of one job: per circuit, per_circuit_s + shots x (per_shot_s + its duration)."""
    return sum(cost["per_circuit_s"] + shots * (cost["per_shot_s"] + d) for d in durations_s)


def z_of_counts(counts, clbit=0):
    """<Z> of one clbit from Qiskit counts (keys: clbit 0 rightmost)."""
    shots = sum(counts.values())
    zero = sum(v for k, v in counts.items() if k.replace(" ", "")[-1 - clbit] == "0")
    return (2 * zero - shots) / shots


# ------------------------------------------------------------------------------------------------ the device model

class NoisyDevice:
    """TOQB noise on a fake backend's Target (see the module's description)."""

    def __init__(self, target):
        from qiskit.transpiler import PassManager
        from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDelay
        from qiskit_aer import AerSimulator
        self.target = target
        self.sched = PassManager([ALAPScheduleAnalysis(target=target), PadDelay(target=target)])
        self.sim = AerSimulator(method="density_matrix", max_parallel_threads=1, max_parallel_experiments=1)
        self._models = {}

    def _compact(self, c):
        from qiskit import QuantumCircuit
        act = sorted({c.find_bit(q).index for i in c.data if i.operation.name not in ("delay", "barrier")
                      for q in i.qubits})
        pos = {q: k for k, q in enumerate(act)}
        out = QuantumCircuit(len(act), c.num_clbits)
        for i in c.data:
            qs = [c.find_bit(q).index for q in i.qubits]
            if i.operation.name == "barrier" or any(q not in pos for q in qs):
                continue
            out.append(i.operation, [pos[q] for q in qs], [c.find_bit(b).index for b in i.clbits])
        return out, tuple(act)

    def _model(self, act):
        if act in self._models:
            return self._models[act]
        from qiskit.circuit import Delay
        from qiskit_aer.noise import (NoiseModel, ReadoutError, RelaxationNoisePass, depolarizing_error,
                                      thermal_relaxation_error)
        t = self.target
        nm = NoiseModel(basis_gates=[g for g in ("cz", "ecr", "cx", "rz", "sx", "x") if g in t.operation_names])
        T1 = [t.qubit_properties[q].t1 for q in act]
        T2 = [min(t.qubit_properties[q].t2, 2 * t.qubit_properties[q].t1) for q in act]
        for k, q in enumerate(act):
            for g in ("sx", "x"):
                p = t[g][(q,)]
                err = depolarizing_error(min(max(p.error or 0.0, 0.0), 0.5), 1)
                nm.add_quantum_error(err.compose(thermal_relaxation_error(T1[k], T2[k], p.duration)), g, [k])
            e = min(max(t["measure"][(q,)].error or 0.0, 0.0), 0.5)
            nm.add_readout_error(ReadoutError([[1 - e, e], [e, 1 - e]]), [k])
        g2 = next(g for g in ("cz", "ecr", "cx") if g in t.operation_names)
        for a in range(len(act)):
            for b in range(len(act)):
                p = t[g2][(act[a], act[b])] if (act[a], act[b]) in t[g2] else None
                if p is None:
                    continue
                th = thermal_relaxation_error(T1[a], T2[a], p.duration).expand(
                    thermal_relaxation_error(T1[b], T2[b], p.duration))
                err = depolarizing_error(min(max(p.error or 0.0, 0.0), 0.75), 2)
                nm.add_quantum_error(err.compose(th), g2, [a, b])
        rp = RelaxationNoisePass(T1, T2, dt=t.dt, op_types=[Delay])
        self._models[act] = (nm, rp)
        return nm, rp

    def counts(self, circuits, shots, seeds):
        """Qiskit counts of each circuit, from `shots` samples with the given seeds."""
        out = []
        for c, s in zip(circuits, seeds):
            sc, act = self._compact(self.sched.run(c))
            nm, rp = self._model(act)
            out.append(self.sim.run(rp(sc), noise_model=nm, shots=shots, seed_simulator=int(s)).result().get_counts())
        return out


# ------------------------------------------------------------------------------------------------ arms

def _qiskit_sig(qc):
    """A circuit's structure: names, qubits, clbits and the number of parameters of every instruction."""
    return tuple((i.operation.name, tuple(qc.find_bit(q).index for q in i.qubits),
                  tuple(qc.find_bit(c).index for c in i.clbits), len(i.operation.params)) for i in qc.data)


class QiskitLoop:
    def __init__(self, level, mode):
        self.level, self.mode = level, mode
        self.name = f"qiskit:{level}:target:{mode}"
        self.stats = dict(template_builds=0, template_unavailable=0)

    def version(self):
        import qiskit
        return qiskit.__version__

    def setup(self, target):
        from qiskit.transpiler import generate_preset_pass_manager
        self.pm = generate_preset_pass_manager(self.level, target=target, seed_transpiler=0)
        self._cache = {}

    def _template(self, qc):
        """Every numeric parameter of `qc` replaced by v[k] (in instruction order), transpiled once."""
        from qiskit.circuit import ParameterVector
        values = [float(p) for i in qc.data for p in i.operation.params]
        pv = ParameterVector("v", len(values))
        par = qc.copy_empty_like()
        k = 0
        for ins in qc.data:
            op = ins.operation
            if op.params:
                op = op.to_mutable()
                op.params = [pv[k + j] for j in range(len(op.params))]
                k += len(op.params)
            par.append(op, ins.qubits, ins.clbits)
        tq = self.pm.run(par)
        order = [pv[j] for j in range(len(values))]
        positional = list(tq.parameters) == order
        self.stats["template_builds"] += 1
        return tq, order, positional

    def compile_circuit(self, qc):
        if self.mode != "template":
            return self.pm.run(qc)
        sig = _qiskit_sig(qc)
        if sig not in self._cache:
            self._cache[sig] = self._template(qc)
        tq, order, positional = self._cache[sig]
        values = [float(p) for i in qc.data for p in i.operation.params]
        if positional:
            return tq.assign_parameters(values)
        present = set(tq.parameters)
        return tq.assign_parameters({p: v for p, v in zip(order, values) if p in present})


class PSFAILoop:
    def __init__(self, mode):
        self.mode = mode
        self.name = f"psfai:{mode}"
        self.stats = dict(template_builds=0, template_unavailable=0)
        repo = os.environ.get("PSF_ZERO_REPO")
        if not repo:
            raise RuntimeError("set PSF_ZERO_REPO to a PSF-Zero checkout")
        pc_file = os.environ.get("PSF_COMPILE_FILE", os.path.join(repo, "psf_compile.py"))
        ai_file = os.environ.get("PSF_AI_FILE", os.path.join(repo, "patches", "psf_ai_compile_a25_2026-10-25",
                                                             "psf_ai_compile.py"))
        sys.path[:0] = [os.path.join(repo, "benchmarks"), repo]
        here = os.getcwd()
        os.chdir(repo)  # the front end finds its a15 / a14 files from the repository root
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                spec = importlib.util.spec_from_file_location("psf_compile", pc_file)
                self.pc = importlib.util.module_from_spec(spec)
                sys.modules["psf_compile"] = self.pc
                spec.loader.exec_module(self.pc)
                self.pc.WARN_WITHOUT_TARGET = False
                spec = importlib.util.spec_from_file_location("psf_ai_compile_toqb", ai_file)
                self.ai = importlib.util.module_from_spec(spec)
                sys.modules["psf_ai_compile_toqb"] = self.ai
                spec.loader.exec_module(self.ai)
        finally:
            os.chdir(here)
        self.a24 = hasattr(self.ai, "A24_STATS")  # a24 on: the template in Rust, the zipper as PSF_RING_ZIP

    def version(self):
        v = f"psf_compile {self.pc.VERSION}, psf_ai_compile {self.ai.AI_COMPILE_VERSION}"
        rust = os.environ.get("TOQB_RUST_TEMPLATE", "")
        if self.mode == "template_zip":
            v += (", template with the zipper (a24, PSF_RING_ZIP=1)" if self.a24 else
                  ", template with the workplace's zipper candidate (toqb.ring_zip; report-only, Python)")
        if self.mode == "template" and self.a24:
            v += f", template built by a24 in Rust (PSF_RUST_TEMPLATE={os.environ.get('PSF_RUST_TEMPLATE', '')})"
        elif self.mode == "template" and rust in ("1", "check"):  # recorded: the template is built in Rust
            v += f", template built in Rust (toqb.ringport, TOQB_RUST_TEMPLATE={rust})"
        return v

    def setup(self, target):
        self.target = target
        self.basis = [g for g in ("cz", "rz", "sx", "x") if g in target.operation_names]
        self.cmap = target.build_coupling_map()
        self._cache = {}

    def _recompile(self, qc):
        with contextlib.redirect_stdout(io.StringIO()):
            return self.ai.compile_for_model_circuit(qc, self.cmap, self.basis, target=self.target)

    def _a24_template(self, qc, zipper):
        """a24's template for one structure, with its zipper option set for this call only."""
        old = os.environ.get("PSF_RING_ZIP")
        os.environ["PSF_RING_ZIP"] = "1" if zipper else ""
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                return self.ai.model_template(qc, self.target)
        finally:
            if old is None:
                os.environ.pop("PSF_RING_ZIP", None)
            else:
                os.environ["PSF_RING_ZIP"] = old

    def compile_circuit(self, qc):
        if self.a24 and self.mode in ("template", "template_zip"):
            sig = self.ai._structure_sig(qc)
            if sig not in self._cache:
                tpl = self._a24_template(qc, self.mode == "template_zip")
                self._cache[sig] = tpl
                self.stats["template_builds" if tpl is not None else "template_unavailable"] += 1
            tpl = self._cache[sig]
            if tpl is None:
                return self._recompile(qc)
            out = tpl.bind(qc)
            out.metadata = dict(toqb_initial=list(tpl.layout), toqb_final=list(tpl.layout))
            return out
        if self.mode == "template_zip":  # report-only (2026-10-22): a22's ring template with the zipper candidate
            return self._compile_zip(qc)
        if self.mode != "template":
            return self._recompile(qc)
        sig = self.ai._structure_sig(qc)
        if sig not in self._cache:
            make = getattr(self.ai, "model_template", None) or self.ai.ring_template  # a22 on: item 43
            rust = os.environ.get("TOQB_RUST_TEMPLATE", "")
            tpl = None
            if rust in ("1", "check"):  # toqb.ringport: the same template built in Rust (opt-in)
                from toqb import ringport as RP
                try:
                    tpl = RP.ring_template(qc, self.target, self.ai)
                    self.stats["rust_built"] = self.stats.get("rust_built", 0) + 1
                except RP.Refused as exc:  # a case not ported: the Python builds it
                    self.stats.setdefault("rust_refused", []).append(str(exc))
                    rust = "refused"
                if rust == "check":
                    with contextlib.redirect_stdout(io.StringIO()):
                        py = make(qc, self.target)
                    diffs = RP.compare(py, tpl) if (py is not None and tpl is not None) else (
                        [] if py is None and tpl is None else ["one of the two is None"])
                    if diffs:
                        raise RP.Mismatch(f"the Rust template differs from the Python's: {diffs[:5]}")
                    self.stats["rust_checked"] = self.stats.get("rust_checked", 0) + 1
            if rust not in ("1", "check"):
                with contextlib.redirect_stdout(io.StringIO()):
                    tpl = make(qc, self.target)
            self._cache[sig] = tpl
            self.stats["template_builds" if tpl is not None else "template_unavailable"] += 1
        tpl = self._cache[sig]
        if tpl is None:  # a structure the ring template does not read: compiled as the front end compiles it
            return self._recompile(qc)
        out = tpl.bind(qc)
        out.metadata = dict(toqb_initial=list(tpl.layout), toqb_final=list(tpl.layout))
        return out


def _psfai_compile_zip(self, qc):
    """psfai:template_zip: as psfai:template (one template per structure, then bound), with the template from
    toqb.ring_zip.model_template_z (a22's choice among N2, item 31 and the workplace's zipper, by item 84's rule).
    Python only (the Rust builder has no zipper); report-only, never a pre-registered arm."""
    from toqb import ring_zip as RZ
    sig = self.ai._structure_sig(qc)
    if sig not in self._cache:
        with contextlib.redirect_stdout(io.StringIO()):
            tpl = RZ.model_template_z(self.ai, self.pc, qc, self.target)
        self._cache[sig] = tpl
        self.stats["template_builds" if tpl is not None else "template_unavailable"] += 1
    tpl = self._cache[sig]
    if tpl is None:
        return self._recompile(qc)
    out = tpl.bind(qc)
    out.metadata = dict(toqb_initial=list(tpl.layout), toqb_final=list(tpl.layout))
    return out


PSFAILoop._compile_zip = _psfai_compile_zip


def make_loop_arm(spec):
    parts = spec.split(":")
    if parts[0] == "qiskit" and len(parts) == 4 and parts[2] == "target":
        return QiskitLoop(int(parts[1]), parts[3])
    if parts[0] == "psfai" and len(parts) == 2:
        return PSFAILoop(parts[1])
    if parts[0] == "fold" and len(parts) == 2:  # 2026-10-25: the hole schedule (toqb.fold), analysis arm
        from toqb.fold import FoldLoop
        return FoldLoop(parts[1])
    raise ValueError(f"unknown loop arm {spec!r}")


# ------------------------------------------------------------------------------------------------ compile and run

class Executor:
    """Compiles Qiskit circuits with one arm and runs them on TOQB noise, keeping every time and check. Shared by the
    Qiskit front end and the PennyLane device, so both measure the same thing."""

    def __init__(self, arm, device, engine="aer"):
        self.arm, self.device = arm, device
        if engine == "fast":  # toqb.fast_noise: the same noise model, exact <Z> of clbit 0, shots drawn from it
            from toqb.fast_noise import FastNoisyDevice
            self.noisy = FastNoisyDevice(device.target)
        elif engine == "aer":
            self.noisy = NoisyDevice(device.target)
        else:
            raise ValueError(f"unknown engine {engine!r}")
        self.engine = engine
        self._struct = {}
        self.compile_s = self.sim_s = self.check_s = 0.0
        self.circuits = 0
        self.q2, self.durations, self.equivalence = [], [], []
        self.structural_fail = self.on_failed_ops = 0
        self.last_durations = []

    def run(self, qcs, shots, seeds, check_first=False):
        from toqb.metrics import equivalence, failed_operations, metrics, structural_check
        outs, self.last_durations = [], []
        for j, qc in enumerate(qcs):
            s = time.perf_counter()
            out = self.arm.compile_circuit(qc)
            self.compile_s += time.perf_counter() - s
            self.circuits += 1
            s = time.perf_counter()
            key = cached = None
            if self.engine == "fast":
                # these checks read only the circuit's structure (gates and qubits, not angles): with the fast engine
                # they are computed for the first three circuits of a structure, required equal, then reused
                scan = self.noisy._scan(out)
                try:
                    out._toqb_scan = scan  # reused by the engine instead of scanning the circuit again
                except AttributeError:
                    pass
                key = scan[0]
                cached = self._struct.get(key)
            if cached is not None and cached[3] >= 3:
                sf, fo, m = cached[0], cached[1], cached[2]
                cached[3] += 1
            else:
                sf, fo, m = bool(structural_check(out, self.device)), failed_operations(out, self.device), \
                    metrics(out, self.device)
                if key is not None:
                    if cached is not None and (cached[0], cached[1], cached[2]["q2"], cached[2].get("duration_s")) \
                            != (sf, fo, m["q2"], m.get("duration_s")):
                        raise RuntimeError("structure-only checks differ between circuits of one structure")
                    self._struct[key] = [sf, fo, m, (cached[3] if cached else 0) + 1]
            if sf:
                self.structural_fail += 1
            self.on_failed_ops += fo
            self.q2.append(m["q2"])
            d = m.get("duration_s")
            d = d if isinstance(d, float) else 0.0
            self.durations.append(d)
            self.last_durations.append(d)
            if check_first and j == 0:
                e = equivalence(qc, out)
                self.equivalence.append(dict(checked=e.get("checked"), equivalent=e.get("equivalent"),
                                             distance=e.get("distance"), why=e.get("why")))
            self.check_s += time.perf_counter() - s
            outs.append(out)
        s = time.perf_counter()
        counts = self.noisy.counts(outs, shots, seeds)
        self.sim_s += time.perf_counter() - s
        return counts


class QiskitFrontEnd:
    """Circuits built in Qiskit; <Z_0> read from clbit 0."""

    def __init__(self, executor, n, L):
        self.ex, self.n, self.L = executor, n, L

    def z0(self, angle_sets, shots, seeds, check_first=False):
        qcs = [model_circuit(a, self.n, self.L) for a in angle_sets]
        return [z_of_counts(c) for c in self.ex.run(qcs, shots, seeds, check_first)]


class PennyLaneFrontEnd:
    """Circuits built as PennyLane tapes returning qml.expval(qml.PauliZ(0)), run through CompiledDevice."""

    def __init__(self, executor, n, L):
        from toqb.pennylane_device import CompiledDevice
        self.n, self.L = n, L
        self.dev = CompiledDevice(wires=n, executor=executor)

    def z0(self, angle_sets, shots, seeds, check_first=False):
        import pennylane as qml
        tapes = [qml.tape.QuantumScript(model_ops(a, self.n, self.L), [qml.expval(qml.PauliZ(0))], shots=shots)
                 for a in angle_sets]
        self.dev.next_seeds = list(seeds)
        self.dev.check_first = check_first
        return [float(r) for r in qml.execute(tapes, self.dev, diff_method=None)]


# ------------------------------------------------------------------------------------------------ one arm

def run_arm(plan, spec, partial_path=None):
    import numpy as np
    from toqb.devices import get_device
    task, opt, ev = plan["task"], plan["optimizer"], plan["evaluation"]
    cost = dict(DEFAULT_COST, **plan.get("qpu_cost", {}))
    frontend = plan.get("frontend", "qiskit")
    n, L, enc = task["n"], task["layers"], task["enc"]
    device = get_device(plan["device"])
    rec = dict(arm=spec, plan=plan["name"], device=plan["device"], frontend=frontend, qpu_cost=cost,
               engine=plan.get("engine", "aer"), started=_cest_now())
    try:
        arm = make_loop_arm(spec)
        rec["version"] = arm.version()
        if frontend == "pennylane":
            import pennylane as qml
            rec["version"] += f"; PennyLane {qml.__version__}"
    except Exception as exc:  # noqa: BLE001 - recorded: the arm could not be loaded
        rec["error"] = f"load: {type(exc).__name__}: {exc}"
        return rec
    Xtr, ytr, Xte, yte = teacher_data(task)
    theta, steps = spsa_schedule(task, opt)
    shots, seed_base = ev["shots"], ev["shot_seed"]
    t0 = time.perf_counter()
    s = time.perf_counter()
    try:
        arm.setup(device.target)
        ex = Executor(arm, device, engine=plan.get("engine", "aer"))
        fe = (PennyLaneFrontEnd if frontend == "pennylane" else QiskitFrontEnd)(ex, n, L)
    except Exception as exc:  # noqa: BLE001
        rec["error"] = f"setup: {type(exc).__name__}: {exc}"
        return rec
    t_setup = time.perf_counter() - s
    ex.compile_s += t_setup
    spent = dict(batch_qpu_s=0.0, session_s=t_setup, classical_s=t_setup)  # the setup happens inside the session
    curve, evals = [], []
    check_at = {0, opt["iterations"] // 2, opt["iterations"] - 1}
    eval_at = set(ev.get("at", []))  # extra evaluation points (long runs)
    curve_every = int(ev.get("curve_every", 1))

    def evaluate(k, theta):
        sim0, chk0, comp0 = ex.sim_s, ex.check_s, ex.compile_s
        sets = [angle_list(theta, x, n, L, enc) for x in Xte]
        zs = np.array(fe.z0(sets, shots, [seed_base + 1_000_000 + 1000 * k + j for j in range(len(sets))]))
        exact = np.array([exact_z0(a, n, L) for a in sets])
        evals.append(dict(iteration=k, accuracy=float(np.mean(np.where(zs == 0, 0.5, np.sign(zs) == yte))),
                          margin=float(np.mean(yte * zs)), noiseless_accuracy=float(np.mean(np.sign(exact) == yte)),
                          noiseless_margin=float(np.mean(yte * exact)),
                          batch_qpu_s=spent["batch_qpu_s"], session_s=spent["session_s"],
                          batch_usd=spent["batch_qpu_s"] * cost["usd_per_s"],
                          session_usd=spent["session_s"] * cost["usd_per_s"],
                          compile_s=comp0, wall_s=time.perf_counter() - t0))
        if partial_path:  # long runs: the evaluations so far, rewritten at every evaluation
            with open(partial_path + ".tmp", "w", encoding="utf-8") as f:
                json.dump(dict(arm=spec, evals=evals, spent=dict(spent), at=_cest_now()), f)
            os.replace(partial_path + ".tmp", partial_path)
        return ex.sim_s - sim0, ex.check_s - chk0

    try:
        evaluate(0, theta)
        stop_usd = ev.get("stop_budget_usd")  # a hard QPU budget (batch mode): stop before the job that would pass it
        last_job, done = None, 0
        for k, (idx, delta) in enumerate(steps):
            if stop_usd is not None and last_job is not None and \
                    (spent["batch_qpu_s"] + last_job) * cost["usd_per_s"] > stop_usd + 1e-9:
                break
            it0, sim0, chk0 = time.perf_counter(), ex.sim_s, ex.check_s
            ak, ck = gains(k, opt)
            delta = np.array(delta)
            plus, minus = theta + ck * delta, theta - ck * delta
            sets = [angle_list(plus, Xtr[i], n, L, enc) for i in idx] + [angle_list(minus, Xtr[i], n, L, enc)
                                                                        for i in idx]
            zs = fe.z0(sets, shots, [seed_base + 1000 * k + j for j in range(len(sets))], check_first=k in check_at)
            B = len(idx)
            lp = float(np.mean([(1 - ytr[i] * z) / 2 for i, z in zip(idx, zs[:B])]))
            lm = float(np.mean([(1 - ytr[i] * z) / 2 for i, z in zip(idx, zs[B:])]))
            theta = theta - ak * (lp - lm) / (2 * ck) * delta
            job_qpu = qpu_seconds(ex.last_durations, shots, cost)
            classical = (time.perf_counter() - it0) - (ex.sim_s - sim0) - (ex.check_s - chk0)
            spent["batch_qpu_s"] += job_qpu
            last_job, done = job_qpu, k + 1
            spent["classical_s"] += classical
            spent["session_s"] += job_qpu + classical
            if (k + 1) % curve_every == 0:
                curve.append(dict(iteration=k + 1, loss=(lp + lm) / 2, job_qpu_s=job_qpu, classical_s=classical))
            if (k + 1) % ev["every"] == 0 or k + 1 == len(steps) or (k + 1) in eval_at:
                evaluate(k + 1, theta)
        if stop_usd is not None and (not evals or evals[-1]["iteration"] != done):
            evaluate(done, theta)  # the model the budget bought
        rec_stop = dict(stop_budget_usd=stop_usd, iterations_done=done) if stop_usd is not None else None
    except Exception as exc:  # noqa: BLE001 - recorded: the arm failed during the loop
        rec_stop = None
        rec["error"] = f"loop: {type(exc).__name__}: {exc}"
    rec.update(setup_s=t_setup, compile_s=ex.compile_s, sim_s=ex.sim_s, check_s=ex.check_s,
               wall_s=time.perf_counter() - t0, circuits=ex.circuits,
               per_circuit_compile_ms=1000 * (ex.compile_s - t_setup) / max(ex.circuits, 1),
               structural_fail=ex.structural_fail, on_failed_ops=ex.on_failed_ops, arm_stats=arm.stats,
               q2_mean=float(np.mean(ex.q2)) if ex.q2 else None,
               duration_us_mean=1e6 * float(np.mean(ex.durations)) if ex.durations else None,
               spent=dict(spent, batch_usd=spent["batch_qpu_s"] * cost["usd_per_s"],
                          session_usd=spent["session_s"] * cost["usd_per_s"]),
               equivalence=ex.equivalence, curve=curve, evals=evals, final_theta=[float(t) for t in theta])
    if rec_stop:
        rec["stop"] = rec_stop
    bad_eq = [e for e in ex.equivalence if e["checked"] and not e["equivalent"]]
    rec["valid"] = ("error" not in rec and not ex.structural_fail and not ex.on_failed_ops and not bad_eq)
    rec["to_target"] = {}
    for mode in ("batch", "session"):
        hit = next((e for e in evals if e["accuracy"] >= ev["target_accuracy"]), None)
        rec["to_target"][mode] = None if hit is None else dict(iteration=hit["iteration"], usd=hit[f"{mode}_usd"],
                                                               qpu_s=hit["batch_qpu_s" if mode == "batch" else
                                                                         "session_s"])
    return rec


# ------------------------------------------------------------------------------------------------ CLI

def main(argv):
    if len(argv) >= 4 and argv[0] == "arm":
        plan = json.load(open(argv[1], encoding="utf-8"))
        safe = argv[3].replace(":", "_")
        rec = run_arm(plan, argv[3], partial_path=os.path.join(argv[2], f"arm-{safe}.partial.json"))
        with open(os.path.join(argv[2], f"arm-{safe}.json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=1)
        print(json.dumps({k: rec.get(k) for k in ("arm", "valid", "compile_s", "sim_s", "error")}), flush=True)
        return 0
    if len(argv) >= 3 and argv[0] == "classical":
        from toqb.classical import run_classical
        plan = json.load(open(argv[1], encoding="utf-8"))
        rec = run_classical(plan)
        with open(os.path.join(argv[2], "classical.json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=1)
        print(json.dumps(rec["models"]), flush=True)
        return 0
    if len(argv) >= 3 and argv[0] == "run":
        plan_file, outdir = argv[1], argv[2]
        if os.path.exists(outdir) and os.listdir(outdir):
            print(f"{outdir} is not empty: a run never overwrites another", file=sys.stderr)
            return 2
        os.makedirs(outdir, exist_ok=True)
        plan = json.load(open(plan_file, encoding="utf-8"))
        with open(os.path.join(outdir, "plan.json"), "w", encoding="utf-8") as f:  # the plan the run used
            json.dump(plan, f, indent=1)
        env = dict(os.environ, **SINGLE_THREAD)
        for spec in plan["arms"]:
            subprocess.run([sys.executable, "-m", "toqb.task_loop", "arm", plan_file, outdir, spec], env=env,
                           check=False)
        subprocess.run([sys.executable, "-m", "toqb.task_loop", "classical", plan_file, outdir], env=env, check=False)
        from toqb.score_loop import report
        text = report(outdir, plan)
        with open(os.path.join(outdir, "report.md"), "w", encoding="utf-8") as f:
            f.write(text)
        print(text)
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
