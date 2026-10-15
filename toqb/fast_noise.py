"""A fast engine for TOQB's noise model: exact <Z> of clbit 0 from a density matrix, shots drawn from it.

TOQB's loop measures one number per circuit, <Z> on clbit 0. `NoisyDevice` gets it by asking Aer for counts, one
circuit at a time. This engine computes the same quantity exactly and draws the shots from it:

- **The same noisy circuit.** The circuit is scheduled (ALAP with the device's durations), compacted to its active
  qubits and given relaxation on its delays by `NoisyDevice`'s own passes, and every gate gets the error
  `NoisyDevice._model` gives it (depolarizing composed with thermal relaxation; rz is error-free; readout error at
  the measurement). Errors act after their gate, as in Aer.
- **Exact, then sampled.** The density matrix is evolved exactly. p1, the probability that clbit 0 reads 1 (readout
  error included), gives the shots as a binomial draw. For a single clbit this has the same distribution as Aer's
  counts; it is not the same random stream, so runs are not bit-identical to Aer's.
- **Fused.** Runs of one-qubit operations (gates, their errors, relaxation on delays) are multiplied into one 4 x 4
  superoperator per qubit and folded into the next two-qubit operation. A circuit becomes about one tensor
  contraction per two-qubit gate.
- **Scheduled once per structure.** A template's circuits differ only in their rz angles. The scheduled noisy circuit
  is cached per structure and only the angles are replaced, wire by wire.
- **Batched.** Circuits of the same structure are evolved together.

`check_against_aer` compares the final density matrix with Aer's, on the same noisy circuit.
"""
import math

import numpy as np

_SX = 0.5 * np.array([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]])
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_CZ = np.diag([1, 1, 1, -1]).astype(complex)


def _rz(theta):
    return np.diag([np.exp(-0.5j * theta), np.exp(0.5j * theta)])


def _sup1(kraus):
    """4 x 4 superoperator on (r, c) of one qubit from its Kraus operators."""
    return sum(np.kron(k, k.conj()) for k in kraus)


def _kraus_be(kraus_le, k):
    """Kraus operators from Qiskit's little-endian order over (q0, q1, ...) to big-endian over the same list."""
    out = []
    for K in kraus_le:
        t = np.asarray(K).reshape((2,) * (2 * k))
        perm = list(range(k - 1, -1, -1)) + list(range(2 * k - 1, k - 1, -1))
        out.append(t.transpose(perm).reshape(2 ** k, 2 ** k))
    return out


def _sup2(kraus_be):
    """16 x 16 superoperator on (r_a, r_b, c_a, c_b) from big-endian Kraus operators over (a, b)."""
    return sum(np.kron(K, K.conj()) for K in kraus_be)


def _lift1(Sa, Sb):
    """Two one-qubit superoperators as one 16 x 16 on (r_a, r_b, c_a, c_b)."""
    t = np.einsum("ACac,BDbd->ABCDabcd", Sa.reshape(2, 2, 2, 2), Sb.reshape(2, 2, 2, 2))
    return t.reshape(16, 16)


def _channel_kraus(op, k):
    from qiskit.quantum_info import Kraus
    return _kraus_be(Kraus(op).data, k)


class _Lazy:
    """A batch of density matrices whose axes are left where the last operation put them: each operation moves only
    the axes it acts on to the end (one copy), and the logical order is restored once, at the end."""

    def __init__(self, rho, n):
        self.rho, self.n = rho, n
        self.order = list(range(rho.ndim))  # physical position -> logical axis (0 is the batch, always first)

    def apply(self, qs, S):
        n, k = self.n, len(qs)
        need = [1 + q for q in qs] + [1 + n + q for q in qs]
        pos = {ax: i for i, ax in enumerate(self.order)}
        rest = [ax for ax in self.order if ax not in need]
        new = rest + need
        t = self.rho.transpose([pos[ax] for ax in new])
        sh = t.shape
        flat = t.reshape(sh[0], -1, 4 ** k)
        self.rho = np.matmul(flat, np.swapaxes(S, 1, 2)).reshape(sh)
        self.order = new

    def logical(self):
        pos = {ax: i for i, ax in enumerate(self.order)}
        return self.rho.transpose([pos[ax] for ax in range(self.rho.ndim)])


class FastNoisyDevice:
    """Drop-in for `NoisyDevice` where only <Z> of clbit 0 is needed (see the module's description)."""

    def __init__(self, target, noisy=None):
        from toqb.task_loop import NoisyDevice
        self.nd = noisy or NoisyDevice(target)
        self.target = target
        self._noise = {}
        self._skeleton = {}
        self.stats = dict(scheduled=0, reused=0)

    # ---------------------------------------------------------------------------------------------- noise per gate

    def _gate_noise(self, act):
        """Superoperators of the errors NoisyDevice._model attaches, keyed like its noise model, and readout errors."""
        if act in self._noise:
            return self._noise[act]
        from qiskit_aer.noise import depolarizing_error, thermal_relaxation_error
        t = self.target
        T1 = [t.qubit_properties[q].t1 for q in act]
        T2 = [min(t.qubit_properties[q].t2, 2 * t.qubit_properties[q].t1) for q in act]
        one, two, ro = {}, {}, {}
        for k, q in enumerate(act):
            for g in ("sx", "x"):
                p = t[g][(q,)]
                err = depolarizing_error(min(max(p.error or 0.0, 0.0), 0.5), 1).compose(
                    thermal_relaxation_error(T1[k], T2[k], p.duration))
                one[(g, k)] = _sup1(_channel_kraus(err, 1))
            ro[k] = min(max(t["measure"][(q,)].error or 0.0, 0.0), 0.5)
        g2 = next(g for g in ("cz", "ecr", "cx") if g in t.operation_names)
        for a in range(len(act)):
            for b in range(len(act)):
                p = t[g2][(act[a], act[b])] if (act[a], act[b]) in t[g2] else None
                if p is None:
                    continue
                th = thermal_relaxation_error(T1[a], T2[a], p.duration).expand(
                    thermal_relaxation_error(T1[b], T2[b], p.duration))
                err = depolarizing_error(min(max(p.error or 0.0, 0.0), 0.75), 2).compose(th)
                two[(g2, a, b)] = _sup2(_channel_kraus(err, 2))  # Qiskit order (a, b) = (q0, q1)
        self._noise[act] = (g2, one, two, ro)
        return self._noise[act]

    # ---------------------------------------------------------------------------------------------- the noisy circuit

    @staticmethod
    def _structure(c):
        return tuple((i.operation.name, tuple(c.find_bit(q).index for q in i.qubits),
                      tuple(c.find_bit(b).index for b in i.clbits)) for i in c.data)

    @staticmethod
    def _rz_by_wire(c):
        wires = {}
        for i in c.data:
            if i.operation.name == "rz":
                wires.setdefault(c.find_bit(i.qubits[0]).index, []).append(float(i.operation.params[0]))
        return wires

    def noisy_circuit(self, c):
        """(noisy circuit as Aer runs it, active qubits, noise model, relaxation pass), scheduled once per structure."""
        only_rz = all(not i.operation.params or i.operation.name in ("rz", "delay") for i in c.data)
        key = self._structure(c) if only_rz else None
        if key is not None and key in self._skeleton:
            r, act, nm, rp, wire_of = self._skeleton[key]
            self.stats["reused"] += 1
            angles = self._rz_by_wire(c)
            pos = {w: 0 for w in angles}
            out = r.copy_empty_like()
            for i in r.data:
                if i.operation.name == "rz":
                    w = wire_of[r.find_bit(i.qubits[0]).index]
                    from qiskit.circuit.library import RZGate
                    out.append(RZGate(angles[w][pos[w]]), i.qubits, i.clbits)
                    pos[w] += 1
                else:
                    out.append(i.operation, i.qubits, i.clbits)
            return out, act, nm, rp
        self.stats["scheduled"] += 1
        sc, act = self.nd._compact(self.nd.sched.run(c))
        nm, rp = self.nd._model(act)
        r = rp(sc)
        if key is not None:
            wire_of = {k: q for k, q in enumerate(act)}  # compact index -> original wire
            self._skeleton[key] = (r, act, nm, rp, wire_of)
        return r, act, nm, rp

    # ---------------------------------------------------------------------------------------------- the program

    def program(self, r, act):
        """Fused list of (qubits, superoperator) and the measurement of clbit 0 as (qubit, readout error, index)."""
        g2, one, two, ro = self._gate_noise(act)
        n = r.num_qubits
        pend = [None] * n
        ops = []

        def acc(q, S):
            pend[q] = S if pend[q] is None else S @ pend[q]

        def flush(q):
            if pend[q] is not None:
                ops.append(((q,), pend[q]))
                pend[q] = None

        meas = None
        for i in r.data:
            name = i.operation.name
            qs = tuple(r.find_bit(q).index for q in i.qubits)
            if name == "delay" or name == "barrier":
                continue
            if name == "measure":
                if r.find_bit(i.clbits[0]).index == 0:
                    flush(qs[0])
                    meas = (qs[0], ro[qs[0]], len(ops))
                continue
            if name == "rz":
                acc(qs[0], _sup1([_rz(float(i.operation.params[0]))]))
            elif name in ("sx", "x"):
                U = _SX if name == "sx" else _X
                S = _sup1([U])
                acc(qs[0], one[(name, qs[0])] @ S if (name, qs[0]) in one else S)
            elif len(qs) == 1:  # a channel (relaxation on a delay) or another one-qubit operation
                acc(qs[0], _sup1(_channel_kraus(i.operation, 1)))
            elif len(qs) == 2:
                a, b = qs
                if name == "cz":
                    U = _CZ
                else:
                    from qiskit.quantum_info import Operator
                    U = _kraus_be([Operator(i.operation).data], 2)[0]
                S = _sup2([U])
                if (name, a, b) in two:
                    S = two[(name, a, b)] @ S
                Pa = pend[a] if pend[a] is not None else np.eye(4)
                Pb = pend[b] if pend[b] is not None else np.eye(4)
                pend[a] = pend[b] = None
                ops.append(((a, b), S @ _lift1(Pa, Pb)))
            else:
                raise ValueError(f"unsupported operation {name} on {qs}")
        if meas is None:
            raise ValueError("no measurement on clbit 0")
        return n, ops, meas, [q for q in range(n) if pend[q] is not None], pend

    # ---------------------------------------------------------------------------------------------- evolution

    @staticmethod
    def _apply(rho, n, qs, S):
        """rho: (B, 2^n rows as n axes, 2^n cols as n axes); S: (B, 4^k, 4^k) on (r_qs..., c_qs...)."""
        axes = [1 + q for q in qs] + [1 + n + q for q in qs]
        k = len(qs)
        moved = np.moveaxis(rho, axes, list(range(-2 * k, 0)))
        sh = moved.shape
        flat = moved.reshape(sh[0], -1, 4 ** k)
        out = np.matmul(flat, np.swapaxes(S, 1, 2)).reshape(sh)
        return np.moveaxis(out, list(range(-2 * k, 0)), axes)

    def _evolve(self, n, progs, upto=None):
        """Evolve a batch of programs with the same structure; returns rho after `upto` ops (default: all)."""
        B = len(progs)
        rho = np.zeros((B,) + (2,) * (2 * n), dtype=complex)
        rho[(slice(None),) + (0,) * (2 * n)] = 1.0
        m = len(progs[0]) if upto is None else upto
        for j in range(m):
            qs = progs[0][j][0]
            S = np.stack([p[j][1] for p in progs])
            rho = self._apply(rho, n, qs, S)
        return rho

    @staticmethod
    def _p1(rho, n, q):
        diag = rho.reshape(rho.shape[0], 2 ** n, 2 ** n).diagonal(axis1=1, axis2=2).real
        bits = (np.arange(2 ** n) >> (n - 1 - q)) & 1  # row index is big-endian over qubits 0..n-1
        return diag[:, bits == 1].sum(axis=1)

    # ---------------------------------------------------------------------------------------------- fast path

    def _plan(self, c):
        """Per structure: the noisy circuit reduced to one-qubit chains (fixed 4 x 4 factors and rz slots) around
        each two-qubit operation, up to the measurement of clbit 0. Built once; a circuit then only supplies angles."""
        key = self._structure(c)
        plan = self._plans.get(key) if hasattr(self, "_plans") else None
        if plan is not None:
            return key, plan
        if not hasattr(self, "_plans"):
            self._plans = {}
        r, act, _, _ = self.noisy_circuit(c)
        g2, one, two, ro = self._gate_noise(act)
        n = r.num_qubits
        chains = [[] for _ in range(n)]
        slots = []  # (compact qubit, k-th rz on it)
        seen = [0] * n
        steps = []

        def push_fixed(q, F):
            if chains[q] and chains[q][-1][0] == "F":
                chains[q][-1] = ("F", F @ chains[q][-1][1])
            else:
                chains[q].append(("F", F))

        meas = None
        for i in r.data:
            name = i.operation.name
            qs = tuple(r.find_bit(q).index for q in i.qubits)
            if name in ("delay", "barrier"):
                continue
            if name == "measure":
                if r.find_bit(i.clbits[0]).index == 0:
                    meas = (qs[0], chains[qs[0]], ro[qs[0]])
                    break
                continue
            if name == "rz":
                q = qs[0]
                chains[q].append(("Z", len(slots)))
                slots.append((q, seen[q]))
                seen[q] += 1
            elif name in ("sx", "x"):
                S = _sup1([_SX if name == "sx" else _X])
                push_fixed(qs[0], one[(name, qs[0])] @ S if (name, qs[0]) in one else S)
            elif len(qs) == 1:
                push_fixed(qs[0], _sup1(_channel_kraus(i.operation, 1)))
            elif len(qs) == 2:
                a, b = qs
                if name == "cz":
                    U = _CZ
                else:
                    from qiskit.quantum_info import Operator
                    U = _kraus_be([Operator(i.operation).data], 2)[0]
                S = _sup2([U])
                if (name, a, b) in two:
                    S = two[(name, a, b)] @ S
                steps.append((a, b, S, chains[a], chains[b]))
                chains[a], chains[b] = [], []
            else:
                raise ValueError(f"unsupported operation {name} on {qs}")
        if meas is None:
            raise ValueError("no measurement on clbit 0")
        wire_of = {k: q for k, q in enumerate(act)}
        plan = dict(n=n, steps=steps, meas=meas, slots=[(wire_of[q], k) for q, k in slots])
        self._plans[key] = plan
        return key, plan

    @staticmethod
    def _chain(items, th):
        """Product of a chain for a batch of angle vectors th (B, slots): (B, 4, 4), or None if empty."""
        if not items:
            return None
        B = th.shape[0]
        M = None
        for kind, v in items:
            if kind == "F":
                M = np.broadcast_to(v, (B, 4, 4)).copy() if M is None else np.matmul(v, M)
            else:
                ph = np.exp(-1j * th[:, v])
                d = np.stack([np.ones(B), ph, ph.conj(), np.ones(B)], axis=1)
                M = (np.broadcast_to(np.diag(np.ones(4)), (B, 4, 4)) * d[:, :, None]) if M is None else d[:, :, None] * M
        return M

    @staticmethod
    def _scan(c):
        """One pass over a circuit: its structure (names, qubits, clbits) and its rz angles by wire."""
        qi = {q: k for k, q in enumerate(c.qubits)}
        ci = {b: k for k, b in enumerate(c.clbits)}
        key, wires = [], {}
        for i in c.data:  # the instruction's own name / params: no Python operation object is built
            name = i.name
            qs = tuple(qi[q] for q in i.qubits)
            key.append((name, qs, tuple(ci[b] for b in i.clbits)))
            if name == "rz":
                wires.setdefault(qs[0], []).append(float(i.params[0]))
        return tuple(key), wires

    def p1_fast(self, circuits):
        """p1 of clbit 0 (readout error included) for each circuit: exact, from the per-structure plan."""
        out = np.empty(len(circuits))
        groups = {}
        scans = []
        for j, c in enumerate(circuits):
            key, wires = getattr(c, "_toqb_scan", None) or self._scan(c)  # the Executor's scan, when it made one
            scans.append(wires)
            plan = getattr(self, "_plans", {}).get(key)
            if plan is None:
                key2, plan = self._plan(c)
                assert key2 == key
            groups.setdefault(key, (plan, []))[1].append(j)
        for key, (plan, idx) in groups.items():
            n = plan["n"]
            rows = []
            for j in idx:
                ang = scans[j]
                rows.append([ang[w][k] for w, k in plan["slots"]])
            th = np.array(rows, dtype=float).reshape(len(idx), len(plan["slots"]))
            B = len(idx)
            rho = np.zeros((B,) + (2,) * (2 * n), dtype=complex)
            rho[(slice(None),) + (0,) * (2 * n)] = 1.0
            lazy = _Lazy(rho, n)
            I4 = np.eye(4)
            for a, b, S, ca, cb in plan["steps"]:
                Ma, Mb = self._chain(ca, th), self._chain(cb, th)
                if Ma is None and Mb is None:
                    T = np.broadcast_to(S, (B, 16, 16))
                else:
                    Ma = np.broadcast_to(I4, (B, 4, 4)) if Ma is None else Ma
                    Mb = np.broadcast_to(I4, (B, 4, 4)) if Mb is None else Mb
                    lift = np.einsum("xACac,xBDbd->xABCDabcd", Ma.reshape(B, 2, 2, 2, 2),
                                     Mb.reshape(B, 2, 2, 2, 2)).reshape(B, 16, 16)
                    T = np.matmul(S, lift)
                lazy.apply((a, b), T)
            q, cq, e = plan["meas"]
            Mq = self._chain(cq, th)
            if Mq is not None:
                lazy.apply((q,), Mq)
            p = self._p1(lazy.logical(), n, q)
            out[idx] = p * (1 - e) + (1 - p) * e
        return out

    def p1_of(self, circuits):
        """p1 of clbit 0 (readout error included) for each circuit, exact (reference path, one program per circuit)."""
        built = []
        for c in circuits:
            r, act, _, _ = self.noisy_circuit(c)
            n, ops, meas, _, _ = self.program(r, act)
            built.append((n, ops, meas))
        out = np.empty(len(circuits))
        groups = {}
        for j, (n, ops, meas) in enumerate(built):
            groups.setdefault((n, tuple(o[0] for o in ops), meas[0], meas[2]), []).append(j)
        for (n, _, q, upto), idx in groups.items():
            rho = self._evolve(n, [built[j][1] for j in idx], upto)
            p = self._p1(rho, n, q)
            e = np.array([built[j][2][1] for j in idx])
            out[idx] = p * (1 - e) + (1 - p) * e
        return out

    def counts(self, circuits, shots, seeds):
        """Counts of clbit 0 only (as '0'/'1' keys), drawn from the exact p1; enough for TOQB's z_of_counts."""
        p1 = self.p1_fast(circuits)
        out = []
        for p, s in zip(p1, seeds):
            ones = int(np.random.default_rng(int(s)).binomial(shots, min(max(p, 0.0), 1.0)))
            out.append({"0": shots - ones, "1": ones})
        return out


def check_against_aer(fast, circuits):
    """Largest |rho_fast - rho_aer| over the circuits, both evolved on the same noisy circuit up to the measurement,
    and the largest |p1_fast - p1_aer|."""
    from qiskit_aer import AerSimulator
    sim = AerSimulator(method="density_matrix", max_parallel_threads=1)
    worst_rho = worst_p = 0.0
    for c in circuits:
        r, act, nm, _ = fast.noisy_circuit(c)
        n, ops, meas, _, pend = fast.program(r, act)
        mine = fast._evolve(n, [ops])  # all ops; pending one-qubit runs after the last op applied below
        for q in range(n):
            if pend[q] is not None:
                mine = fast._apply(mine, n, (q,), pend[q][None])
        mine = mine.reshape(2 ** n, 2 ** n)
        body = r.copy_empty_like()
        for i in r.data:
            if i.operation.name != "measure":
                body.append(i.operation, i.qubits, i.clbits)
        body.save_density_matrix()
        dm = np.asarray(sim.run(body, noise_model=nm).result().data()["density_matrix"])
        # Aer is little-endian over qubits; the engine is big-endian: reverse the qubit axes
        dm = dm.reshape((2,) * (2 * n)).transpose(list(range(n - 1, -1, -1)) + list(range(2 * n - 1, n - 1, -1)))
        worst_rho = max(worst_rho, float(np.max(np.abs(dm.reshape(2 ** n, 2 ** n) - mine))))
        q, e = meas[0], meas[1]
        bits = (np.arange(2 ** n) >> (n - 1 - q)) & 1
        pa = float(np.real(np.diagonal(dm.reshape(2 ** n, 2 ** n))[bits == 1].sum()))
        pa = pa * (1 - e) + (1 - pa) * e
        pf = float(fast.p1_of([c])[0])
        worst_p = max(worst_p, abs(pa - pf))
    return worst_rho, worst_p
