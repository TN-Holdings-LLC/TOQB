"""TOQB layer 3, the variational-loop scenario (v15, smoke size): a classifier trained by SPSA on a noisy device model,
with every circuit of every iteration compiled by the compiler under test.

What compounds. Each iteration evaluates 2 x B circuits (the SPSA pair over a batch of B training points). A compiler
pays its compile time on every one of them, and its output's noise enters every gradient. Better circuits give
cleaner gradients, so the same number of iterations reaches a better model; faster compiles make the loop cheaper.
Both are measured, separately and together.

The task (identical for every arm; nothing depends on the compiler but the circuits):
  - model: data re-uploading on a ring (DEPTH1's / RING1's classifier). Per layer: RY(enc x_q) on every qubit, then
    RY(a_q) RZ(b_q) on every qubit, then a CZ ring (0,1) ... (n-1,0); after the last layer RY(c_q); measure all. The
    prediction is sign(<Z_0>), read from clbit 0.
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

Arms ("compiler:mode"):
  qiskit:L:target:template   Qiskit's loop practice: the circuit with every angle a Parameter, transpiled once at
                             level L with the device's Target; each circuit is `assign_parameters`.
  qiskit:L:target:recompile  the concrete circuit transpiled every time.
  psfai:template             PSF-Zero's AI front end (a21): `ring_template` built once, `bind_values` each time.
  psfai:recompile            `compile_for_model_circuit` every time.
The PSF-Zero files come from $PSF_ZERO_REPO: psf_compile.py ($PSF_COMPILE_FILE, default the release at its root) and
the front end ($PSF_AI_FILE, default patches/psf_ai_compile_a21_2026-10-15/psf_ai_compile.py).

Measured per arm (one process each, one thread):
  - compile time: the template's build plus every bind, or every compile (perf_counter around the compiler's calls
    only); the simulation's time separately;
  - every output: the structural check, operations on failed elements, two-qubit count, duration; TOQB's equivalence
    check on the first circuit of the first, middle and last iteration (a failure there, or any structural failure or
    operation on a failed element, makes the arm invalid);
  - the training: loss per iteration (the SPSA pair's mean), test accuracy and margin on the noisy model at the
    evaluation points, and the noiseless test accuracy of the final angles;
  - time to target: the first evaluation at which the noisy test accuracy reaches `target_accuracy`, with the
    iterations and the compile and loop time spent until then.
The budget: an arm's compile time per loop against the reference arm's (`reference`), with the floor `budget_floor_s`;
tiers 1x, 3x, 10x.

    python -m toqb.task_loop run PLAN.json OUTDIR      every arm of the plan, one process each, then the report
    python -m toqb.task_loop arm PLAN.json OUTDIR SPEC one arm (what `run` starts)
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
        steps.append((idx.tolist(), rng.choice([-1.0, 1.0], d).tolist()))
    return theta0, steps


def _cest_now():
    """The time in Central European time, as TOQB's records give it."""
    import datetime
    from zoneinfo import ZoneInfo
    return datetime.datetime.now(ZoneInfo("Europe/Zurich")).strftime("%Y-%m-%d %H:%M:%S %Z")


def gains(k, opt):
    return opt["a"] / (k + 1 + opt["A"]) ** 0.602, opt["c"] / (k + 1) ** 0.101


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

    def z0(self, circuits, shots, seeds):
        """<Z_0> (clbit 0) of each circuit, from `shots` samples with the given seeds."""
        out = []
        for c, s in zip(circuits, seeds):
            sc, act = self._compact(self.sched.run(c))
            nm, rp = self._model(act)
            counts = self.sim.run(rp(sc), noise_model=nm, shots=shots, seed_simulator=int(s)).result().get_counts()
            zero = sum(v for k, v in counts.items() if k.replace(" ", "")[-1] == "0")
            out.append((2 * zero - shots) / shots)
        return out


# ------------------------------------------------------------------------------------------------ arms

class QiskitLoop:
    def __init__(self, level, mode):
        self.level, self.mode = level, mode
        self.name = f"qiskit:{level}:target:{mode}"

    def version(self):
        import qiskit
        return qiskit.__version__

    def setup(self, task, target):
        from qiskit.circuit import ParameterVector
        from qiskit.transpiler import generate_preset_pass_manager
        self.pm = generate_preset_pass_manager(self.level, target=target, seed_transpiler=0)
        self.n, self.L = task["n"], task["layers"]
        if self.mode == "template":
            pv = ParameterVector("v", len(gate_kinds(self.n, self.L)))
            self.tq = self.pm.run(model_circuit(list(pv), self.n, self.L))

    def compile(self, angles):
        if self.mode == "template":
            return self.tq.assign_parameters(angles)
        return self.pm.run(model_circuit(angles, self.n, self.L))


class PSFAILoop:
    def __init__(self, mode):
        self.mode = mode
        self.name = f"psfai:{mode}"
        repo = os.environ.get("PSF_ZERO_REPO")
        if not repo:
            raise RuntimeError("set PSF_ZERO_REPO to a PSF-Zero checkout")
        pc_file = os.environ.get("PSF_COMPILE_FILE", os.path.join(repo, "psf_compile.py"))
        ai_file = os.environ.get("PSF_AI_FILE", os.path.join(repo, "patches", "psf_ai_compile_a21_2026-10-15",
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

    def version(self):
        return f"psf_compile {self.pc.VERSION}, psf_ai_compile {self.ai.AI_COMPILE_VERSION}"

    def setup(self, task, target):
        self.n, self.L, self.target = task["n"], task["layers"], target
        self.basis = [g for g in ("cz", "rz", "sx", "x") if g in target.operation_names]
        self.cmap = target.build_coupling_map()
        if self.mode == "template":
            example = model_circuit([0.1 * (k + 1) for k in range(len(gate_kinds(self.n, self.L)))], self.n, self.L)
            with contextlib.redirect_stdout(io.StringIO()):
                self.tpl = self.ai.ring_template(example, target)
            if self.tpl is None:
                raise RuntimeError("ring_template returned None for the model")
            if len(self.tpl.var_kinds) != len(gate_kinds(self.n, self.L)):
                raise RuntimeError("the template's angles are not the model's")

    def compile(self, angles):
        if self.mode == "template":
            out = self.tpl.bind_values(angles)
            out.metadata = dict(toqb_initial=list(self.tpl.layout), toqb_final=list(self.tpl.layout))
            return out
        with contextlib.redirect_stdout(io.StringIO()):
            return self.ai.compile_for_model_circuit(model_circuit(angles, self.n, self.L), self.cmap, self.basis,
                                                     target=self.target)


def make_loop_arm(spec):
    parts = spec.split(":")
    if parts[0] == "qiskit" and len(parts) == 4 and parts[2] == "target":
        return QiskitLoop(int(parts[1]), parts[3])
    if parts[0] == "psfai" and len(parts) == 2:
        return PSFAILoop(parts[1])
    raise ValueError(f"unknown loop arm {spec!r}")


# ------------------------------------------------------------------------------------------------ one arm

def run_arm(plan, spec):
    import numpy as np
    from toqb.devices import get_device
    from toqb.metrics import equivalence, failed_operations, metrics, structural_check
    task, opt, ev = plan["task"], plan["optimizer"], plan["evaluation"]
    n, L, enc = task["n"], task["layers"], task["enc"]
    device = get_device(plan["device"])
    rec = dict(arm=spec, plan=plan["name"], device=plan["device"], started=_cest_now())
    try:
        arm = make_loop_arm(spec)
        rec["version"] = arm.version()
    except Exception as exc:  # noqa: BLE001 - recorded: the arm could not be loaded
        rec["error"] = f"load: {type(exc).__name__}: {exc}"
        return rec
    Xtr, ytr, Xte, yte = teacher_data(task)
    theta, steps = spsa_schedule(task, opt)
    dev = NoisyDevice(device.target)
    shots = ev["shots"]
    seed_base = ev["shot_seed"]
    t_compile = 0.0
    t_sim = 0.0
    n_circ = 0
    stats = dict(structural_fail=0, on_failed_ops=0, q2=[], duration_s=[], equivalence=[])
    curve, evals = [], []
    t0 = time.perf_counter()
    try:
        s = time.perf_counter()
        arm.setup(task, device.target)
        t_setup = time.perf_counter() - s
    except Exception as exc:  # noqa: BLE001
        rec["error"] = f"setup: {type(exc).__name__}: {exc}"
        return rec
    t_compile += t_setup
    check_at = {0, opt["iterations"] // 2, opt["iterations"] - 1}

    def compile_many(angle_sets, check_first=False):
        nonlocal t_compile, n_circ
        outs = []
        for j, ang in enumerate(angle_sets):
            s = time.perf_counter()
            out = arm.compile(ang)
            t_compile += time.perf_counter() - s
            n_circ += 1
            if structural_check(out, device):
                stats["structural_fail"] += 1
            stats["on_failed_ops"] += failed_operations(out, device)
            m = metrics(out, device)
            stats["q2"].append(m["q2"])
            if isinstance(m.get("duration_s"), float):
                stats["duration_s"].append(m["duration_s"])
            if check_first and j == 0:
                e = equivalence(model_circuit(ang, n, L), out)
                stats["equivalence"].append(dict(checked=e.get("checked"), equivalent=e.get("equivalent"),
                                                 distance=e.get("distance"), why=e.get("why")))
            outs.append(out)
        return outs

    def evaluate(k, theta):
        nonlocal t_sim
        sets = [angle_list(theta, x, n, L, enc) for x in Xte]
        outs = compile_many(sets)
        s = time.perf_counter()
        zs = dev.z0(outs, shots, [seed_base + 1_000_000 + 1000 * k + j for j in range(len(outs))])
        t_sim += time.perf_counter() - s
        zs = np.array(zs)
        exact = np.array([exact_z0(a, n, L) for a in sets])
        evals.append(dict(iteration=k, accuracy=float(np.mean(np.where(zs == 0, 0.5, np.sign(zs) == yte))),
                          margin=float(np.mean(yte * zs)), noiseless_accuracy=float(np.mean(np.sign(exact) == yte)),
                          noiseless_margin=float(np.mean(yte * exact)), compile_s=t_compile, sim_s=t_sim,
                          wall_s=time.perf_counter() - t0))

    try:
        evaluate(0, theta)
        for k, (idx, delta) in enumerate(steps):
            ak, ck = gains(k, opt)
            delta = np.array(delta)
            plus, minus = theta + ck * delta, theta - ck * delta
            sets = [angle_list(plus, Xtr[i], n, L, enc) for i in idx] + [angle_list(minus, Xtr[i], n, L, enc)
                                                                        for i in idx]
            outs = compile_many(sets, check_first=k in check_at)
            s = time.perf_counter()
            zs = dev.z0(outs, shots, [seed_base + 1000 * k + j for j in range(len(outs))])
            t_sim += time.perf_counter() - s
            B = len(idx)
            lp = float(np.mean([(1 - ytr[i] * z) / 2 for i, z in zip(idx, zs[:B])]))
            lm = float(np.mean([(1 - ytr[i] * z) / 2 for i, z in zip(idx, zs[B:])]))
            theta = theta - ak * (lp - lm) / (2 * ck) * delta
            curve.append(dict(iteration=k + 1, loss=(lp + lm) / 2))
            if (k + 1) % ev["every"] == 0 or k + 1 == len(steps):
                evaluate(k + 1, theta)
    except Exception as exc:  # noqa: BLE001 - recorded: the arm failed during the loop
        rec["error"] = f"loop: {type(exc).__name__}: {exc}"
    rec.update(setup_s=t_setup, compile_s=t_compile, sim_s=t_sim, wall_s=time.perf_counter() - t0, circuits=n_circ,
               per_circuit_compile_ms=1000 * (t_compile - t_setup) / max(n_circ, 1),
               structural_fail=stats["structural_fail"], on_failed_ops=stats["on_failed_ops"],
               q2_mean=float(np.mean(stats["q2"])) if stats["q2"] else None,
               duration_us_mean=1e6 * float(np.mean(stats["duration_s"])) if stats["duration_s"] else None,
               equivalence=stats["equivalence"], curve=curve, evals=evals, final_theta=[float(t) for t in theta])
    bad_eq = [e for e in stats["equivalence"] if e["checked"] and not e["equivalent"]]
    rec["valid"] = ("error" not in rec and not stats["structural_fail"] and not stats["on_failed_ops"]
                    and not bad_eq)
    hit = next((e for e in evals if e["accuracy"] >= ev["target_accuracy"]), None)
    rec["to_target"] = None if hit is None else dict(iteration=hit["iteration"], compile_s=hit["compile_s"],
                                                     sim_s=hit["sim_s"], wall_s=hit["wall_s"])
    return rec


# ------------------------------------------------------------------------------------------------ CLI

def main(argv):
    if len(argv) >= 4 and argv[0] == "arm":
        plan = json.load(open(argv[1], encoding="utf-8"))
        rec = run_arm(plan, argv[3])
        safe = argv[3].replace(":", "_")
        with open(os.path.join(argv[2], f"arm-{safe}.json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=1)
        print(json.dumps({k: rec.get(k) for k in ("arm", "valid", "compile_s", "sim_s", "error")}), flush=True)
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
