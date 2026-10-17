"""S2R, stage 0: many candidates chosen in a simulator, a few run on the "device" (PSF-Zero idea memo
docs/ideas/s2r-sim-to-real-2026-10-16.md; the owner's decisions of 2026-10-17).

The question: when a cheap simulator chooses which parameter vectors are sent to an expensive device, do PSF-Zero's
shorter circuits keep "good in simulation" closer to "good on the device", so that the same device budget reaches a
better model?

The task is TOQB's loop classifier (`toqb.task_loop`: n = 6, L = 8, data re-uploading on a ring, teacher-student
data, loss (1 - y z) / 2). Both compilers compile every circuit for FakeFez's Target, as in every TOQB loop run.

- **The simulator** knows FakeFez's calibration: TOQB's noise model on FakeFez (`toqb.fast_noise`), the exact <Z_0>
  of each compiled circuit (no shots). It costs nothing.
- **The stand-in device** is what the simulator does not know (`StandIn`): ibm_marrakesh's calibration of
  2026-10-13 11:37 CEST (the same coupling map as FakeFez), with every qubit's T1 and T2 multiplied by a factor drawn
  once in [1 - t12, 1 + t12]; a systematic over-rotation of every sx and x by a fraction `over` of its angle; and a
  static ZZ interaction of `zz_hz` between every pair of neighbouring qubits (a spectator in |0> gives its neighbour a
  Z rotation). It is scheduled ALAP with its own durations, evolved by Aer's density matrix and sampled with shots. Its
  circuits are billed at IBM's price, as in TOQB: per circuit 0.036 s + shots x (0.27 ms + the circuit's duration on
  FakeFez's Target, the duration the compiler sees), $96 per minute.

**One S2R loop** (`run_s2r`): N candidates theta_i = m + sigma_t eps_i around the current mean m (the mean itself is
candidate 0); each is evaluated in the simulator on the loop's batch of B training points; the k with the lowest
simulated loss are run on the stand-in on the same B points with `shots` shots (k x B circuits, billed); the mean
moves to the weighted mean of the best mu of those k by the stand-in's loss (log weights, as CMA-ES); sigma_{t+1} =
sigma_t x `decay`. The loop stops before the one that would pass the budget. After every loop the mean is evaluated on
the stand-in's test set (not billed) and in the simulator.

**The device-only baseline** (`run_spsa`): no simulator; TOQB's SPSA (run 1's settings) on the stand-in, stopped
before the job that would pass the budget, its model evaluated on the stand-in's test set.

Every random draw (the batches, eps, the initial mean, shot seeds) comes from the seed and is the same for both
compilers; only the circuits differ.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time

import numpy as np

from toqb import task_loop as TL

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, "data", "ns_snapshot_ibm_marrakesh_2026-10-13.json")
SNAPSHOT_SHA256 = "c4caf4cb6708c18ce36292833f81292377c39a5316d40ea62622bb2a5b9357ac"
CHUNK = 400  # circuits simulated together (memory: about 25 MB of density matrices per 400 six-qubit circuits)


# ------------------------------------------------------------------------------------------------ the stand-in device

def standin_target(t12, seed, dt):
    """ibm_marrakesh's snapshot as a Target on FakeFez's dt, T1 and T2 of every qubit multiplied by a factor uniform in
    [1 - t12, 1 + t12] (drawn from `seed`); a value the snapshot lacks is the median of the others."""
    from qiskit.circuit import Delay, Measure, Parameter
    from qiskit.circuit.library import CZGate, RZGate, SXGate, XGate
    from qiskit.transpiler import InstructionProperties, QubitProperties, Target
    raw = open(SNAPSHOT, "rb").read()
    if hashlib.sha256(raw).hexdigest() != SNAPSHOT_SHA256:
        raise RuntimeError("the Marrakesh snapshot differs from the pre-registered one")
    d = json.loads(raw)
    n = max(int(q) for q in d["qubits"]) + 1
    Q = d["qubits"]

    def med(key):
        v = [Q[q][key] for q in Q if Q[q].get(key) is not None]
        return float(np.median(v))
    fill = {k: med(k) for k in ("t1_s", "t2_s", "sx_error", "sx_length_s", "readout_error", "readout_length_s")}

    def get(q, k):
        v = Q.get(str(q), {}).get(k)
        return fill[k] if v is None else v
    rng = np.random.default_rng(seed)
    f1 = rng.uniform(1 - t12, 1 + t12, n)
    f2 = rng.uniform(1 - t12, 1 + t12, n)
    qp = []
    for q in range(n):
        t1 = get(q, "t1_s") * f1[q]
        qp.append(QubitProperties(t1=t1, t2=min(get(q, "t2_s") * f2[q], 2 * t1)))
    t = Target(num_qubits=n, dt=dt, qubit_properties=qp)

    def dur(x):
        return round(x / dt) * dt
    one = {(q,): InstructionProperties(error=get(q, "sx_error"), duration=dur(get(q, "sx_length_s"))) for q in range(n)}
    t.add_instruction(SXGate(), one)
    t.add_instruction(XGate(), dict(one))
    t.add_instruction(RZGate(Parameter("theta")), {(q,): InstructionProperties(error=0.0, duration=0.0)
                                                   for q in range(n)})
    t.add_instruction(Measure(), {(q,): InstructionProperties(error=get(q, "readout_error"),
                                                              duration=dur(get(q, "readout_length_s")))
                                  for q in range(n)})
    t.add_instruction(Delay(Parameter("t")), {(q,): None for q in range(n)})
    t.add_instruction(CZGate(), {(int(a), int(b)): InstructionProperties(error=e, duration=dur(ln))
                                 for a, b, e, ln in d["couplers"]})
    return t


class StandIn:
    """The stand-in device (see the module's description): counts of compiled circuits, with shots."""

    def __init__(self, t12=0.3, over=0.01, zz_hz=1.0e4, seed=20261017, dt=4e-9):
        from qiskit.transpiler import PassManager
        from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDelay
        from qiskit_aer import AerSimulator
        self.params = dict(t12=t12, over=over, zz_hz=zz_hz, seed=seed)
        self.target = standin_target(t12, seed, dt)
        self.sched = PassManager([ALAPScheduleAnalysis(target=self.target), PadDelay(target=self.target)])
        self.sim = AerSimulator(method="density_matrix", max_parallel_threads=1, max_parallel_experiments=1)
        self.edges = sorted({tuple(sorted(e)) for e in self.target.build_coupling_map().get_edges()})
        self.nbr = {}
        for a, b in self.edges:
            self.nbr.setdefault(a, []).append(b)
            self.nbr.setdefault(b, []).append(a)
        self._models = {}

    def with_crosstalk(self, sc):
        """The scheduled circuit in time order, with the static ZZ accumulated between the non-diagonal gates: before
        each sx or x on qubit q (at its middle), RZZ(pi zz t) with every active neighbour and RZ(pi zz t) for every
        idle neighbour (a spectator in |0>), t being the time since that pair's last such gate. ZZ commutes with every
        other operation here (rz, cz, delays, the final measurements), so this is exact up to the gates' own length."""
        from qiskit import QuantumCircuit
        from qiskit.circuit.library import RZGate, RZZGate
        dt = self.target.dt
        idx = {q: k for k, q in enumerate(sc.qubits)}
        active = {idx[q] for i in sc.data if i.operation.name not in ("delay", "barrier") for q in i.qubits}
        clock, items = {}, []
        for j, ins in enumerate(sc.data):
            qs = [idx[q] for q in ins.qubits]
            nm = ins.operation.name
            if nm == "delay":
                d = float(ins.operation.params[0]) * (dt if ins.operation.unit == "dt" else 1.0)
            elif nm in ("barrier",):
                d = 0.0
            else:
                p = self.target[nm].get(tuple(qs))
                d = (p.duration or 0.0) if p is not None else 0.0
            s = max(clock.get(q, 0.0) for q in qs) if qs else 0.0
            for q in qs:
                clock[q] = s + d
            items.append((s, j, ins, qs, d))
        items.sort(key=lambda x: (x[0], x[1]))
        out = QuantumCircuit(*sc.qregs, *sc.cregs)
        last = {}
        k = math.pi * self.params["zz_hz"]
        for s, j, ins, qs, d in items:
            if ins.operation.name in ("sx", "x") and k:
                q = qs[0]
                tm = s + d / 2
                for r in self.nbr.get(q, ()):
                    key = (min(q, r), max(q, r))
                    if r in active:
                        th = k * (tm - last.get(key, 0.0))
                        if th:
                            out.append(RZZGate(th), [sc.qubits[q], sc.qubits[r]])
                    else:
                        th = k * (tm - last.get((q, r), 0.0))
                        if th:
                            out.append(RZGate(th), [sc.qubits[q]])
                        last[(q, r)] = tm
                    last[key] = tm
            out.append(ins.operation, ins.qubits, ins.clbits)
        return out

    def _model(self, act):
        if act in self._models:
            return self._models[act]
        from qiskit.circuit import Delay
        from qiskit.circuit.library import RXGate
        from qiskit.quantum_info import Operator
        from qiskit_aer.noise import (NoiseModel, ReadoutError, RelaxationNoisePass, coherent_unitary_error,
                                      depolarizing_error, thermal_relaxation_error)
        t = self.target
        nm = NoiseModel(basis_gates=["cz", "rz", "sx", "x", "rzz"])
        T1 = [t.qubit_properties[q].t1 for q in act]
        T2 = [min(t.qubit_properties[q].t2, 2 * t.qubit_properties[q].t1) for q in act]
        ov = self.params["over"]
        for k, q in enumerate(act):
            for g, ang in (("sx", math.pi / 2), ("x", math.pi)):
                p = t[g][(q,)]
                err = coherent_unitary_error(Operator(RXGate(ov * ang)))
                err = err.compose(depolarizing_error(min(max(p.error or 0.0, 0.0), 0.5), 1))
                nm.add_quantum_error(err.compose(thermal_relaxation_error(T1[k], T2[k], p.duration)), g, [k])
            e = min(max(t["measure"][(q,)].error or 0.0, 0.0), 0.5)
            nm.add_readout_error(ReadoutError([[1 - e, e], [e, 1 - e]]), [k])
        for a in range(len(act)):
            for b in range(len(act)):
                p = t["cz"][(act[a], act[b])] if (act[a], act[b]) in t["cz"] else None
                if p is None:
                    continue
                th = thermal_relaxation_error(T1[a], T2[a], p.duration).expand(
                    thermal_relaxation_error(T1[b], T2[b], p.duration))
                nm.add_quantum_error(depolarizing_error(min(max(p.error or 0.0, 0.0), 0.75), 2).compose(th), "cz",
                                     [a, b])
        rp = RelaxationNoisePass(T1, T2, dt=t.dt, op_types=[Delay])
        self._models[act] = (nm, rp)
        return nm, rp

    def prepared(self, c):
        """(the circuit Aer runs, its active qubits): scheduled, crosstalk added, compacted, relaxation on delays."""
        from qiskit import QuantumCircuit
        sc = self.with_crosstalk(self.sched.run(c))
        act = sorted({sc.find_bit(q).index for i in sc.data if i.operation.name not in ("delay", "barrier")
                      for q in i.qubits})
        pos = {q: k for k, q in enumerate(act)}
        out = QuantumCircuit(len(act), sc.num_clbits)
        for i in sc.data:
            qs = [sc.find_bit(q).index for q in i.qubits]
            if i.operation.name == "barrier" or any(q not in pos for q in qs):
                continue
            out.append(i.operation, [pos[q] for q in qs], [sc.find_bit(b).index for b in i.clbits])
        act = tuple(act)
        nm, rp = self._model(act)
        return rp(out), nm

    def counts(self, circuits, shots, seeds):
        out = []
        for c, s in zip(circuits, seeds):
            r, nm = self.prepared(c)
            out.append(self.sim.run(r, noise_model=nm, shots=shots, seed_simulator=int(s)).result().get_counts())
        return out


# ------------------------------------------------------------------------------------------------ the compilers

class Arm:
    """One compiler (`toqb.task_loop`'s loop arms, template mode) with its outputs' checks and FakeFez durations."""

    def __init__(self, spec, device):
        from toqb.metrics import failed_operations, structural_check
        self.spec, self.device = spec, device
        self.arm = TL.make_loop_arm(spec)
        self.arm.setup(device.target)
        self._check = (structural_check, failed_operations)
        self._dur = {}
        self.structural_fail = self.on_failed_ops = 0
        self.compile_s = 0.0
        self.compiled = 0

    def version(self):
        return self.arm.version()

    def compile(self, qc):
        s = time.perf_counter()
        out = self.arm.compile_circuit(qc)
        self.compile_s += time.perf_counter() - s
        self.compiled += 1
        return out

    def duration(self, out, scan_key):
        """FakeFez duration of a compiled circuit (seconds); checked once per structure."""
        if scan_key not in self._dur:
            from toqb.metrics import metrics
            sc, fo = self._check
            self.structural_fail += bool(sc(out, self.device))
            self.on_failed_ops += fo(out, self.device)
            d = metrics(out, self.device).get("duration_s")
            self._dur[scan_key] = (d if isinstance(d, float) else 0.0, metrics(out, self.device)["q2"])
        return self._dur[scan_key]


def _z(counts):
    return TL.z_of_counts(counts)


def _cest():
    return TL._cest_now()


def _weights(mu):
    w = np.array([math.log(mu + 0.5) - math.log(i + 1) for i in range(mu)])
    return w / w.sum()


# ------------------------------------------------------------------------------------------------ S2R

def run_s2r(plan, spec, sim=None, standin=None, progress=None):
    """One S2R run (one compiler, one seed). Returns the record."""
    from toqb.devices import get_device
    from toqb.fast_noise import FastNoisyDevice
    task, s2r, ev = plan["task"], plan["s2r"], plan["evaluation"]
    cost = dict(TL.DEFAULT_COST, **plan.get("qpu_cost", {}))
    n, L, enc = task["n"], task["layers"], task["enc"]
    device = get_device(plan["device"])
    rec = dict(kind="s2r", arm=spec, seed=s2r["seed"], plan=plan["name"], started=_cest(), s2r=s2r, qpu_cost=cost)
    arm = Arm(spec, device)
    rec["version"] = arm.version()
    sim = sim or FastNoisyDevice(device.target)
    standin = standin or StandIn(**plan["standin"])
    rec["standin"] = standin.params
    Xtr, ytr, Xte, yte = TL.teacher_data(task)
    rng = np.random.default_rng(s2r["seed"])
    d = TL.n_params(n, L)
    m = rng.uniform(-s2r["init"], s2r["init"], d)
    sigma = s2r["sigma0"]
    N, B, k, mu = s2r["candidates"], s2r["batch"], s2r["top_k"], s2r["mu"]
    w = _weights(mu)
    shots, budget = ev["shots"], s2r["budget_usd"]
    spent = 0.0
    loops, evals = [], []
    t0 = time.perf_counter()
    sim_s = dev_s = 0.0

    def sim_loss(thetas, X, y):
        """Simulated losses of every theta on the points X (one compiled circuit per theta and point)."""
        nonlocal sim_s
        z = np.empty(len(thetas) * len(X))
        pairs = [(th, x) for th in thetas for x in X]
        for c0 in range(0, len(pairs), CHUNK):  # in chunks: memory stays flat for any N
            outs = [arm.compile(TL.model_circuit(TL.angle_list(th, x, n, L, enc), n, L))
                    for th, x in pairs[c0:c0 + CHUNK]]
            s = time.perf_counter()
            for o in outs:
                o._toqb_scan = sim._scan(o)
                arm.duration(o, o._toqb_scan[0])
            z[c0:c0 + len(outs)] = 1 - 2 * sim.p1_fast(outs)
            sim_s += time.perf_counter() - s
        z = z.reshape(len(thetas), len(X))
        return ((1 - z * y[None, :]) / 2).mean(axis=1), z

    def dev_run(thetas, X, seed0):
        """The stand-in's <Z_0> of every theta on the points X, with shots; and the job's QPU seconds."""
        nonlocal dev_s
        outs, durs = [], []
        for th in thetas:
            for x in X:
                o = arm.compile(TL.model_circuit(TL.angle_list(th, x, n, L, enc), n, L))
                dur, _ = arm.duration(o, sim._scan(o)[0])
                outs.append(o)
                durs.append(dur)
        s = time.perf_counter()
        cnt = standin.counts(outs, shots, [seed0 + j for j in range(len(outs))])
        dev_s += time.perf_counter() - s
        z = np.array([_z(c) for c in cnt]).reshape(len(thetas), len(X))
        return z, TL.qpu_seconds(durs, shots, cost)

    def evaluate(t, m):
        zt, _ = dev_run([m], Xte, ev["shot_seed"] + 1_000_000 + 1000 * t)
        zs = sim_loss([m], Xte, yte)[1][0]
        acc = float(np.mean(np.where(zt[0] == 0, 0.5, np.sign(zt[0]) == yte)))
        evals.append(dict(loop=t, accuracy=acc, margin=float(np.mean(yte * zt[0])),
                          sim_accuracy=float(np.mean(np.sign(zs) == yte)), usd=spent * cost["usd_per_s"],
                          noiseless_accuracy=float(np.mean([np.sign(TL.exact_z0(TL.angle_list(m, x, n, L, enc), n, L))
                                                            == y for x, y in zip(Xte, yte)])),
                          wall_s=time.perf_counter() - t0))

    try:
        evaluate(0, m)
        last_job = None
        for t in range(s2r["max_loops"]):
            if last_job is not None and (spent + last_job) * cost["usd_per_s"] > budget + 1e-9:
                break
            idx = rng.choice(task["n_train"], B, replace=False)
            eps = rng.standard_normal((N - 1, d))
            cands = np.vstack([m[None, :], m[None, :] + sigma * eps])
            ls, _ = sim_loss(cands, Xtr[idx], ytr[idx])
            top = np.argsort(ls, kind="stable")[:k]
            zd, job = dev_run(cands[top], Xtr[idx], ev["shot_seed"] + 10_000_000 * (t + 1))
            if (spent + job) * cost["usd_per_s"] > budget + 1e-9:  # the job would pass the budget: not run
                break
            spent += job
            last_job = job
            ld = ((1 - zd * ytr[idx][None, :]) / 2).mean(axis=1)
            order = np.argsort(ld, kind="stable")
            m = (w[:, None] * cands[top][order[:mu]]).sum(axis=0)
            rs = _spearman(ls[top], ld)
            loops.append(dict(loop=t + 1, sigma=sigma, sim_best=float(ls[top[0]]), sim_top_mean=float(ls[top].mean()),
                              dev_top=[float(x) for x in ld], sim_top=[float(x) for x in ls[top]], spearman=rs,
                              chosen_rank_in_sim=[int(x) for x in order[:mu]], job_qpu_s=job, usd=spent * cost["usd_per_s"],
                              wall_s=time.perf_counter() - t0))
            sigma *= s2r["decay"]
            evaluate(t + 1, m)
            if progress:
                progress(loops[-1], evals[-1])
    except Exception as exc:  # noqa: BLE001 - recorded
        rec["error"] = f"loop: {type(exc).__name__}: {exc}"
    rec.update(loops=loops, evals=evals, spent_qpu_s=spent, spent_usd=spent * cost["usd_per_s"],
               wall_s=time.perf_counter() - t0, sim_s=sim_s, dev_s=dev_s, compile_s=arm.compile_s,
               compiled=arm.compiled, structural_fail=arm.structural_fail, on_failed_ops=arm.on_failed_ops,
               durations_us=sorted({round(v[0] * 1e6, 4) for v in arm._dur.values()}),
               q2=sorted({v[1] for v in arm._dur.values()}), final_mean=[float(x) for x in m], ended=_cest())
    rec["valid"] = "error" not in rec and not arm.structural_fail and not arm.on_failed_ops
    return rec


def _spearman(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)

    def rank(x):
        o = np.argsort(x, kind="stable")
        r = np.empty(len(x))
        r[o] = np.arange(len(x))
        for v in np.unique(x):  # ties: mean rank
            m = x == v
            r[m] = r[m].mean()
        return r
    ra, rb = rank(a), rank(b)
    if ra.std() == 0 or rb.std() == 0:
        return None
    return float(np.corrcoef(ra, rb)[0, 1])


# ------------------------------------------------------------------------------------------------ device-only SPSA

def run_spsa(plan, spec, standin=None):
    """The device-only baseline: TOQB's SPSA (the plan's `spsa`) on the stand-in, stopped at the budget."""
    from toqb.devices import get_device
    from toqb.fast_noise import FastNoisyDevice
    task, opt, ev = plan["task"], plan["spsa"], plan["evaluation"]
    cost = dict(TL.DEFAULT_COST, **plan.get("qpu_cost", {}))
    n, L, enc = task["n"], task["layers"], task["enc"]
    device = get_device(plan["device"])
    rec = dict(kind="spsa", arm=spec, seed=opt["loop_seed"], plan=plan["name"], started=_cest(), spsa=opt,
               qpu_cost=cost)
    arm = Arm(spec, device)
    rec["version"] = arm.version()
    scan = FastNoisyDevice(device.target)._scan
    standin = standin or StandIn(**plan["standin"])
    rec["standin"] = standin.params
    Xtr, ytr, Xte, yte = TL.teacher_data(task)
    theta, steps = TL.spsa_schedule(task, opt)
    shots, budget = ev["shots"], plan["s2r"]["budget_usd"]
    spent, last_job, evals = 0.0, None, []
    t0 = time.perf_counter()

    def run(sets, seed0):
        outs, durs = [], []
        for a in sets:
            o = arm.compile(TL.model_circuit(a, n, L))
            dur, _ = arm.duration(o, scan(o)[0])
            outs.append(o)
            durs.append(dur)
        cnt = standin.counts(outs, shots, [seed0 + j for j in range(len(outs))])
        return np.array([_z(c) for c in cnt]), TL.qpu_seconds(durs, shots, cost)

    def evaluate(it):
        z, _ = run([TL.angle_list(theta, x, n, L, enc) for x in Xte], ev["shot_seed"] + 1_000_000 + 1000 * it)
        evals.append(dict(iteration=it, accuracy=float(np.mean(np.where(z == 0, 0.5, np.sign(z) == yte))),
                          margin=float(np.mean(yte * z)), usd=spent * cost["usd_per_s"],
                          wall_s=time.perf_counter() - t0))

    done = 0
    try:
        evaluate(0)
        for k, (idx, delta) in enumerate(steps):
            if last_job is not None and (spent + last_job) * cost["usd_per_s"] > budget + 1e-9:
                break
            ak, ck = TL.gains(k, opt)
            delta = np.array(delta)
            plus, minus = theta + ck * delta, theta - ck * delta
            sets = [TL.angle_list(plus, Xtr[i], n, L, enc) for i in idx] + [TL.angle_list(minus, Xtr[i], n, L, enc)
                                                                            for i in idx]
            z, job = run(sets, ev["shot_seed"] + 1000 * k)
            Bn = len(idx)
            lp = float(np.mean([(1 - ytr[i] * zz) / 2 for i, zz in zip(idx, z[:Bn])]))
            lm = float(np.mean([(1 - ytr[i] * zz) / 2 for i, zz in zip(idx, z[Bn:])]))
            theta = theta - ak * (lp - lm) / (2 * ck) * delta
            spent += job
            last_job, done = job, k + 1
            if done % ev.get("spsa_every", 10) == 0:
                evaluate(done)
        if not evals or evals[-1]["iteration"] != done:
            evaluate(done)
    except Exception as exc:  # noqa: BLE001
        rec["error"] = f"loop: {type(exc).__name__}: {exc}"
    rec.update(evals=evals, iterations=done, spent_qpu_s=spent, spent_usd=spent * cost["usd_per_s"],
               wall_s=time.perf_counter() - t0, compiled=arm.compiled, structural_fail=arm.structural_fail,
               on_failed_ops=arm.on_failed_ops, ended=_cest())
    rec["valid"] = "error" not in rec and not arm.structural_fail and not arm.on_failed_ops
    return rec


# ------------------------------------------------------------------------------------------------ CLI

def main(argv):
    """python -m toqb.s2r <s2r|spsa> PLAN.json OUT.json SPEC"""
    import sys
    if len(argv) != 4 or argv[0] not in ("s2r", "spsa"):
        print(main.__doc__)
        return 1
    kind, plan_file, out, spec = argv
    if os.path.exists(out):
        print(f"{out} exists: a run never overwrites another", file=sys.stderr)
        return 2
    plan = json.load(open(plan_file, encoding="utf-8"))
    rec = (run_s2r if kind == "s2r" else run_spsa)(plan, spec)
    with open(out + ".tmp", "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    os.replace(out + ".tmp", out)
    print(json.dumps({k: rec.get(k) for k in ("kind", "arm", "seed", "valid", "spent_usd", "wall_s", "error")}),
          flush=True)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
