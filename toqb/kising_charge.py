"""Noise wall, stage 1, probe P1 (2026-10-29; design: the workplace's noise_wall_test_design_r2_2026-10-29): the
weight-2 conserved charge of the kicked-Ising ring (J = pi/4) read on the device from Z-basis product inputs.

    python -m toqb.kising_charge charges --n 20 [--h 0.6]                         (coefficients and the chosen charge)
    python -m toqb.kising_charge build FETCH RUNS --arm fold:rule --n 20 --L 24 [--h 0.6] [--shots 1000]
    python -m toqb.kising_charge rehearse RUNS --p 0.0051                          (predicted rho and shot-noise SE)
    python -m toqb.kising_charge score JOB RUNS [--p 0.0051 [--p-range LO HI] | --p-from-n 20 [--p-L 50]]
                                  [--self-ref-n 20 --self-ref-L 24]     (second device: p from its own L = 24 cell)
                                  [--p2-job JOB2 --p2-runs RUNS2] [--out-name charge_score.json]

The charge. One Floquet step S = (RX(2h) Z)^{(x)n} CZ_ring is a free-fermion step (toqb.kising). Its conserved quadratic
operators are found in the Majorana-bilinear space (both parity sectors, as the workplace's slow_probe2.py); those of
least Pauli weight are translation invariant and contain only nearest-neighbour ZZ, YZ and ZY terms (weight 2), a
two-dimensional space at h = 0.6. The combination used is fixed by a noiseless criterion only: the largest share of
the ZZ coefficient, c_ZZ^2 / (c_ZZ^2 + c_YZ^2 + c_ZY^2), which maximises |<Q>_0| / SE for Z-basis inputs (only ZZ
terms are non-zero there; every term is read with the same shot noise). It is normalised to c_ZZ = 1:

    Q = sum_j ( Z_j Z_{j+1} + b Y_j Z_{j+1} + c Z_j Y_{j+1} ),   j + 1 taken mod n.

The circuit (task_loop.model_circuit order: per layer RY on every qubit; RY, RZ on every qubit; the CZ ring; a final
RY). With U = RX(2h) Z = e^{ia} RZ(phi) RY(theta) RZ(lam), A = RZ(phi) RY(theta) and B = RZ(lam) CZ_ring, S = A B and
S^L = A (B A)^{L-1} B, where B A = CZ_ring RZ(phi + lam) RY(theta) is one model layer. So:
  - layer 1: RY(pi z_q) (the input, z_q in {0, 1}), RY(0), RZ(lam), the CZ ring  (= B on |z>);
  - layers 2..L: RY(theta), RY(0), RZ(phi + lam), the CZ ring  (= B A);
  - then A and the readout rotation M_q (identity for Z, H S^dagger for Y) per qubit: M_q A = RZ(.) RY(g_q) RZ(c_q)
    (ZYZ); RZ(c_q) commutes with the CZ ring and goes into the last layer's RZ, RY(g_q) is the final RY, and the
    leftmost RZ does not change a Z measurement.
All L steps are in the circuit (no shortcut). Every circuit of one (n, L) has the same structure, so each arm builds
one template.

Settings (n even): "Z" all qubits in Z (the ZZ terms); "YZ" Y on even, Z on odd qubits; "ZY" Y on odd, Z on even. Each
YZ and ZY term is read in exactly one of the last two. Inputs: |0..0>, |1..1>, Neel |0101..> (qubit 0 in |0>) and
anti-Neel. Noiseless <Q> = sum_j z_j z_{j+1} (ZZ terms; YZ and ZY vanish on Z-basis states) is the same at every L.

Readout reference (L = 0). The folded schedules and Qiskit read a logical qubit on a physical qubit that depends on L,
so a separate L = 0 circuit would not cancel readout. Each (n, L, arm) record therefore carries its own reference: the
four inputs prepared with X gates directly on the physical qubits the compiled circuit measures, read in Z (only ZZ
terms are non-zero at L = 0, so the Y settings are not needed there).

Four-input ratio (cancels the first-order drift of energy relaxation and of readout asymmetry; r2 section 3):
    rho(L) = [Q(0..0) + Q(1..1) - Q(Neel) - Q(anti-Neel)]_L / [same]_ref.
The |0..0>-only ratio is reported as the relaxation diagnostic. Uniform depolarizing noise p per qubit per step gives
rho(L) = (1 - 4p/3)^(2L); p_eff = 3 (1 - sqrt(r)) / 4 with r = rho^(1/L).

`build` writes RUNS/<name>.json and .qpy in the form `toqb.s2rc_device assemble` reads (as lam_device: "test_labels"
and the prediction are placeholders, +1 and P(1) = 1/2, needed only to assemble; nothing is scored against them).
`score` reads the job's full bitstrings (raw_counts.json; key's rightmost character is clbit 0). Nothing here connects
to IBM.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

from toqb import kising as K

SETTINGS = ("Z", "YZ", "ZY")
INPUTS = ("zero", "one", "neel", "antineel")
SIGN = {"zero": 1, "one": 1, "neel": -1, "antineel": -1}  # sign of each input in the four-input numerator


# ------------------------------------------------------------------------------------------------ the charge

def _gamma(k, n):
    """Majorana k as a Pauli string (list over qubits 0..n-1), Jordan-Wigner in the X basis: g_2j = X_<j Z_j,
    g_2j+1 = X_<j Y_j (toqb.kising's convention)."""
    j = k // 2
    return ["X"] * j + ["Z" if k % 2 == 0 else "Y"] + ["I"] * (n - j - 1)


_MUL = {("X", "Y"): (1j, "Z"), ("Y", "Z"): (1j, "X"), ("Z", "X"): (1j, "Y"),
        ("Y", "X"): (-1j, "Z"), ("Z", "Y"): (-1j, "X"), ("X", "Z"): (-1j, "Y")}


def _mul(a, b):
    ph, s = 1 + 0j, []
    for x, y in zip(a, b):
        if x == "I":
            s.append(y)
        elif y == "I":
            s.append(x)
        elif x == y:
            s.append("I")
        else:
            q, c = _MUL[(x, y)]
            ph *= q
            s.append(c)
    return ph, s


def _pauli_terms(A, B, n):
    """{pauli string: coefficient} of O = sum_{k<l} A_kl i g_k g_l + B_kl P i g_k g_l (P = prod X); string index =
    qubit."""
    m = 2 * n
    terms = {}
    P = ["X"] * n
    for k in range(m):
        for l in range(k + 1, m):
            for coef, withp in ((A[k, l], False), (B[k, l], True)):
                if abs(coef) < 1e-12:
                    continue
                ph, s = _mul(_gamma(k, n), _gamma(l, n))
                ph *= 1j
                if withp:
                    q, s = _mul(P, s)
                    ph *= q
                key = "".join(s)
                terms[key] = terms.get(key, 0) + coef * ph
    return {k: v for k, v in terms.items() if abs(v) > 1e-9}


def _edge_coefficients(terms, n):
    """Per edge (j, j+1 mod n): coefficients of ZZ, YZ (Y on j), ZY (Y on j+1); raises if another term occurs."""
    out = np.zeros((n, 3), dtype=complex)
    idx = {"ZZ": 0, "YZ": 1, "ZY": 2}
    for key, v in terms.items():
        sites = [i for i, ch in enumerate(key) if ch != "I"]
        if len(sites) != 2:
            raise ValueError(f"term {key} is not two-local")
        a, b = sites
        if b - a == 1:
            j, lab = a, key[a] + key[b]
        elif a == 0 and b == n - 1:
            j, lab = n - 1, key[n - 1] + key[0]
        else:
            raise ValueError(f"term {key} is not nearest-neighbour")
        if lab not in idx:
            raise ValueError(f"term {key} ({lab}) is not ZZ, YZ or ZY")
        out[j, idx[lab]] += v
    return out


def charges(n, h, J=np.pi / 4):
    """The conserved weight-2 charges of S at (n, h), and the chosen combination.
    Returns dict(basis=[(n, 3) real arrays of the basis charges' edge coefficients], coef=(b, c) of the chosen charge
    normalised to c_ZZ = 1, edge_spread = max deviation of the chosen charge's coefficients across edges, dim)."""
    from scipy.linalg import eigh, null_space
    m = 2 * n
    iu = np.triu_indices(m, 1)
    d = len(iu[0])

    def vec2A(v):
        A = np.zeros((m, m))
        A[iu] = v
        return A - A.T

    def lin(M):
        E = np.eye(d)
        return np.column_stack([(M @ vec2A(E[:, i]) @ M.T)[iu] for i in range(d)])

    Mp, Mm = K._step_map(n, h, +1, J), K._step_map(n, h, -1, J)
    Np, Nm = null_space(lin(Mp) - np.eye(d), rcond=1e-9), null_space(lin(Mm) - np.eye(d), rcond=1e-9)
    # O = A + P B with A = (S+ + S-)/2, B = (S+ - S-)/2, S+ conserved in the + sector, S- in the - sector
    Ba = np.vstack([np.hstack([Np / 2, Nm / 2]), np.hstack([Np / 2, -Nm / 2])])
    W, WP = K._weights(n)
    wt = np.concatenate([W[iu], WP[iu]]).astype(float)
    vals, vecs = eigh(Ba.T @ (wt[:, None] * Ba), Ba.T @ Ba)
    low = [k for k in range(len(vals)) if abs(vals[k] - 2.0) < 1e-6]  # mean string weight exactly 2
    basis = []
    for k in low:
        v = Ba @ vecs[:, k]
        ec = _edge_coefficients(_pauli_terms(vec2A(v[:d]), vec2A(v[d:]), n), n)
        if np.abs(ec.imag).max() > 1e-9:
            raise ValueError("charge coefficients are not real")
        basis.append(ec.real)
    if len(basis) < 1:
        raise ValueError("no weight-2 conserved charge found")
    # the combination with the largest ZZ share (noiseless criterion), from the edge-0 coefficients
    E = np.array([b[0] for b in basis])  # (dim, 3)
    Mzz = np.outer(E[:, 0], E[:, 0])
    Mall = E @ E.T
    w, V = eigh(Mzz, Mall)
    x = V[:, -1]
    ch = sum(x[i] * basis[i] for i in range(len(basis)))
    ch = ch / ch[0, 0]
    return dict(basis=[b.tolist() for b in basis], coef=(float(ch[0, 1]), float(ch[0, 2])),
                edge_spread=float(np.abs(ch - ch[0]).max()), dim=len(basis), zz_share=float(w[-1]))


# ------------------------------------------------------------------------------------------------ circuits

def input_bits(name, n):
    if name == "zero":
        return [0] * n
    if name == "one":
        return [1] * n
    if name == "neel":
        return [q % 2 for q in range(n)]
    if name == "antineel":
        return [1 - q % 2 for q in range(n)]
    raise ValueError(name)


def bases(setting, n):
    """Per qubit 'Z' or 'Y'."""
    if setting == "Z":
        return ["Z"] * n
    if setting == "YZ":
        return ["Y" if q % 2 == 0 else "Z" for q in range(n)]
    if setting == "ZY":
        return ["Y" if q % 2 == 1 else "Z" for q in range(n)]
    raise ValueError(setting)


def _readout_angles(h, basis):
    """(c, g): RZ(c) then RY(g) equals M A up to a final RZ, with A = RZ(phi) RY(theta), M = I (Z) or H S^dagger (Y)."""
    from qiskit.synthesis import OneQubitEulerDecomposer

    def rz(t):
        return np.diag([np.exp(-1j * t / 2), np.exp(1j * t / 2)])

    def ry(t):
        return np.array([[np.cos(t / 2), -np.sin(t / 2)], [np.sin(t / 2), np.cos(t / 2)]])

    theta, phi, _ = K.step_euler(h)
    A = rz(phi) @ ry(theta)
    if basis == "Z":
        M = np.eye(2)
    else:
        M = np.array([[1, 1], [1, -1]]) / np.sqrt(2) @ np.diag([1, -1j])  # H S^dagger: Y -> Z
    t, p, l = OneQubitEulerDecomposer("ZYZ").angles(M @ A)  # M A = e^{ia} RZ(p) RY(t) RZ(l)
    return float(l), float(t)


def angles(bits, setting, n, L, h):
    """The model_circuit angle list (L >= 1)."""
    if L < 1:
        raise ValueError("L >= 1; L = 0 is the per-record readout reference")
    theta, phi, lam = K.step_euler(h)
    ro = {b: _readout_angles(h, b) for b in ("Z", "Y")}
    bs = bases(setting, n)
    a = []
    for k in range(L):
        last = k == L - 1
        if k == 0:
            a += [np.pi * bits[q] for q in range(n)]
            for q in range(n):
                a += [0.0, lam + (ro[bs[q]][0] if last else 0.0)]
        else:
            a += [theta] * n
            for q in range(n):
                a += [0.0, phi + lam + (ro[bs[q]][0] if last else 0.0)]
    a += [ro[bs[q]][1] for q in range(n)]
    return a


def circuit(bits, setting, n, L, h):
    from toqb import task_loop as TL
    return TL.model_circuit(angles(bits, setting, n, L, h), n, L)


def reference_circuit(compiled, bits):
    """The L = 0 readout reference on the physical qubits `compiled` measures: X where the logical input bit is 1,
    then the same measurements (clbit q from the same physical qubit as in `compiled`)."""
    from qiskit import ClassicalRegister, QuantumCircuit
    meas = {compiled.find_bit(i.clbits[0]).index: compiled.find_bit(i.qubits[0]).index
            for i in compiled.data if i.operation.name == "measure"}
    n = len(meas)
    qc = QuantumCircuit(compiled.num_qubits)
    qc.add_register(ClassicalRegister(compiled.num_clbits, "meas"))
    for q in range(n):
        if bits[q]:
            qc.x(meas[q])
    for q in range(n):
        qc.measure(meas[q], q)
    return qc, meas


def q_noiseless(bits, n):
    """Exact noiseless <Q> on a Z-basis product state (the same at every L): the ZZ terms."""
    z = 1 - 2 * np.asarray(bits)
    return float(np.sum(z * np.roll(z, -1)))


def setting_noiseless(bits, setting, n, L=0):
    """The noiseless contribution of one setting at L = 0 (the ZZ terms for "Z", 0 for the Y settings). For L >= 1 only
    the sum over the three settings is conserved (q_noiseless); a single setting's share changes with L and is not
    computed here (None)."""
    if L:
        return None
    return q_noiseless(bits, n) if setting == "Z" else 0.0


# ------------------------------------------------------------------------------------------------ estimation

def setting_value(counts, setting, n, coef):
    """(mean, variance of the mean) of the setting's part of Q from full-bitstring counts. Setting "Z": sum_j Z_j Z_j+1;
    "YZ"/"ZY": the YZ and ZY terms read there, with weights b (Y on j) and c (Y on j+1)."""
    b, c = coef
    w = np.zeros(n)  # weight of edge j in this setting
    for j in range(n):
        if setting == "Z":
            w[j] = 1.0
        else:
            yj = bases(setting, n)[j] == "Y"
            w[j] = b if yj else c
    tot, vals, cnts = 0, [], []
    for key, cnt in counts.items():
        k = key.replace(" ", "")
        z = np.array([1 - 2 * int(k[-1 - q]) for q in range(n)])
        vals.append(float(np.sum(w * z * np.roll(z, -1))))
        cnts.append(cnt)
        tot += cnt
    vals, cnts = np.array(vals), np.array(cnts, dtype=float)
    mean = float(np.sum(vals * cnts) / tot)
    var = float(np.sum(cnts * (vals - mean) ** 2) / (tot - 1)) / tot if tot > 1 else float("nan")
    return mean, var


def q_of_input(counts_by_setting, n, coef):
    """<Q> and its variance from the three settings of one input (independent shots per setting)."""
    m, v = 0.0, 0.0
    for s in SETTINGS:
        a, b = setting_value(counts_by_setting[s], s, n, coef)
        m, v = m + a, v + b
    return m, v


def ratio(num, var_num, den, var_den):
    """rho = num / den and its delta-method SE (num and den independent)."""
    r = num / den
    return r, float(np.sqrt(var_num + r * r * var_den) / abs(den))


def p_eff(rho, L):
    """Uniform depolarizing rate per qubit per step from rho(L) = (1 - 4p/3)^(2L); None if rho <= 0."""
    if rho <= 0:
        return None
    r = rho ** (1.0 / L)
    return 3 * (1 - np.sqrt(r)) / 4


def rho_predicted(p, L):
    return (1 - 4 * p / 3) ** (2 * L)


def decay_length_predicted(p):
    """Decay length L* (the 1/e depth) of rho(L) = (1 - 4p/3)^(2L) = exp(-L / L*)."""
    return float(-1.0 / (2 * np.log(1 - 4 * p / 3)))


def decay_length(Ls, rhos, ses):
    """Readable-depth measure of one (arm, n): the decay length L* of a one-parameter fit rho(L) = exp(-L / L*) to the
    measured four-input ratios (weighted least squares on the rho scale, weights 1 / SE^2; points with rho <= 0 are
    kept). rho(0) = 1 by construction (each record's own readout reference), so there is no amplitude parameter.
    Returns (L*, SE) with the SE from the curvature of the weighted sum of squares, or (None, None) if every rho is
    <= 0."""
    Ls, rhos, ses = (np.asarray(v, float) for v in (Ls, rhos, ses))
    if not np.any(rhos > 0):
        return None, None
    w = 1.0 / ses ** 2

    def chi2(k):  # k = 1 / L*
        return float(np.sum(w * (rhos - np.exp(-k * Ls)) ** 2))
    # initial bracket from the per-point estimates, then golden-section search in k
    ks = [-np.log(r) / L for r, L in zip(rhos, Ls) if 0 < r < 1]
    lo, hi = 1e-6, max(ks + [1.0 / Ls.min()]) * 10
    g = (np.sqrt(5) - 1) / 2
    a, b = lo, hi
    for _ in range(200):
        c, d = b - g * (b - a), a + g * (b - a)
        if chi2(c) < chi2(d):
            b = d
        else:
            a = c
    k = (a + b) / 2
    J = Ls * np.exp(-k * Ls)  # -d rho / d k
    se_k = 1.0 / np.sqrt(np.sum(w * J * J))
    return float(1.0 / k), float(se_k / k ** 2)


def wall(cells, p=None, p_range=None, ref="fold:rule"):
    """Readable depth (owner, 2026-10-29: the noise wall reported as L* and Delta L).

    Per (arm, n): L* from decay_length over the arm's L cells. Per other arm X at the same n, with the cells of both
    arms at the same L:
      - kappa_X = L*_ref / L*_X (the ratio of per-step decay rates) and Delta L_X = L*_ref - L*_X, SE by the delta
        method (the two fits independent);
      - the structure ratios g_X = sum G_X / sum G_ref (two-qubit gates) and t_X = sum T_X / sum T_ref (scheduled
        duration), from the records only (no error rate is read);
      - the structure model kappa = (1 - phi) g + phi t, phi in [0, 1] the duration share of the reference's decay.
        Rule A (no free parameter): kappa_X inside [min(g, t) - 2 SE, max(g, t) + 2 SE] -> INSIDE, else BELOW or
        ABOVE. Its use is for the arm whose g and t are both away from 1 (fold:zipcyc).
      - phi_X = (kappa_X - g) / (t - g) when |t - g| > 0.2 (else None), with its SE.
    Rule B (n-consistency of phi, per arm): |phi(n2) - phi(n1)| <= 2 SE -> SAME, else DIFFERENT.
    If p is given, the reference's L* is also compared with decay_length_predicted(p): INSIDE if
    |L* - L*_pred| <= 2 sqrt(SE^2 + SE_pred^2), SE_pred half the spread over p_range."""
    by = {}
    for c in cells:
        by.setdefault((c["arm"], c["n"]), {})[c["L"]] = c
    fits = {}
    for (arm, n), g in sorted(by.items()):
        Ls = sorted(g)
        Lst, se = decay_length(Ls, [g[L]["rho4"] for L in Ls], [g[L]["se4"] for L in Ls])
        fits[(arm, n)] = dict(arm=arm, n=n, Ls=Ls, L_star=Lst, se=se)
    ref_pred = None
    if p is not None:
        lp = decay_length_predicted(p)
        ends = [decay_length_predicted(q) for q in (p_range or []) if q is not None]
        sp = (max(ends) - min(ends)) / 2 if len(ends) == 2 else 0.0
        ref_pred = []
        for (arm, n), f in sorted(fits.items()):
            if arm != ref or f["L_star"] is None:
                continue
            tol = 2 * float(np.hypot(f["se"], sp))
            d = f["L_star"] - lp
            ref_pred.append(dict(arm=arm, n=n, L_star=f["L_star"], se=f["se"], pred=lp, se_pred=sp, two_se=tol,
                                 verdict="INSIDE" if abs(d) <= tol else ("BELOW" if d < 0 else "ABOVE")))
    rel = []
    for (arm, n), f in sorted(fits.items()):
        if arm == ref or (ref, n) not in fits:
            continue
        r = fits[(ref, n)]
        common = sorted(set(by[(arm, n)]) & set(by[(ref, n)]))
        x = dict(arm=arm, n=n, L_star=f["L_star"], se=f["se"], L_star_ref=r["L_star"], se_ref=r["se"])
        G = [by[(k, n)][L].get("q2") for k in (arm, ref) for L in common]
        T = [by[(k, n)][L].get("us") for k in (arm, ref) for L in common]
        h = len(common)
        g = (sum(G[:h]) / sum(G[h:])) if common and None not in G else None
        t = (sum(T[:h]) / sum(T[h:])) if common and None not in T else None
        x.update(g=g, t=t)
        if f["L_star"] is None or r["L_star"] is None:
            rel.append(x)
            continue
        kap = r["L_star"] / f["L_star"]
        se_k = kap * float(np.hypot(r["se"] / r["L_star"], f["se"] / f["L_star"]))
        x.update(kappa=kap, se_kappa=se_k, delta_L=r["L_star"] - f["L_star"],
                 se_delta_L=float(np.hypot(r["se"], f["se"])))
        if g is not None and t is not None:
            lo, hi = min(g, t), max(g, t)
            x["bracket"] = [lo, hi]
            x["rule_A"] = ("INSIDE" if lo - 2 * se_k <= kap <= hi + 2 * se_k
                           else ("BELOW" if kap < lo else "ABOVE"))
            if abs(t - g) > 0.2:
                x["phi"] = (kap - g) / (t - g)
                x["se_phi"] = se_k / abs(t - g)
        rel.append(x)
    cons = []
    by_arm = {}
    for x in rel:
        if x.get("phi") is not None:
            by_arm.setdefault(x["arm"], []).append(x)
    for arm, xs in sorted(by_arm.items()):
        xs = sorted(xs, key=lambda v: v["n"])
        for i in range(len(xs)):
            for j in range(i + 1, len(xs)):
                d = xs[j]["phi"] - xs[i]["phi"]
                se = float(np.hypot(xs[i]["se_phi"], xs[j]["se_phi"]))
                cons.append(dict(arm=arm, n=[xs[i]["n"], xs[j]["n"]], diff=d, se=se,
                                 verdict="SAME" if abs(d) <= 2 * se else "DIFFERENT"))
    return dict(fits=list(fits.values()), ref_prediction=ref_pred, relative=rel, phi_consistency=cons)


def estimate(cell_counts, n, L, coef):
    """cell_counts: {(input, setting): counts} with setting in SETTINGS or "ref". Returns the four-input rho, the
    |0..0>-only rho, both with SE, and p_eff."""
    Q, ref = {}, {}
    for i in INPUTS:
        Q[i] = q_of_input({s: cell_counts[(i, s)] for s in SETTINGS}, n, coef)
        ref[i] = setting_value(cell_counts[(i, "ref")], "Z", n, coef)
    num = sum(SIGN[i] * Q[i][0] for i in INPUTS)
    vnum = sum(Q[i][1] for i in INPUTS)
    den = sum(SIGN[i] * ref[i][0] for i in INPUTS)
    vden = sum(ref[i][1] for i in INPUTS)
    r4, se4 = ratio(num, vnum, den, vden)
    r1, se1 = ratio(Q["zero"][0], Q["zero"][1], ref["zero"][0], ref["zero"][1])
    pe = p_eff(r4, L)
    pr = [p_eff(r4 + se4, L), p_eff(r4 - se4, L)]
    return dict(rho4=r4, se4=se4, rho1=r1, se1=se1, p_eff=pe, p_eff_range=pr,
                Q={i: Q[i][0] for i in INPUTS}, ref={i: ref[i][0] for i in INPUTS})


# ------------------------------------------------------------------------------------------------ build / score

def sha256_file(p):
    import hashlib
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def cmd_charges(argv):
    import argparse
    p = argparse.ArgumentParser(prog="kising_charge charges")
    p.add_argument("--n", type=int, nargs="+", default=[20])
    p.add_argument("--h", type=float, default=0.6)
    a = p.parse_args(argv)
    for n in a.n:
        ch = charges(n, a.h)
        print(json.dumps(dict(n=n, h=a.h, dim=ch["dim"], coef_b_YZ=ch["coef"][0], coef_c_ZY=ch["coef"][1],
                              zz_share=ch["zz_share"], edge_spread=ch["edge_spread"],
                              basis_edge0=[bb[0] for bb in ch["basis"]])))
    return 0


def cmd_build(argv):
    import argparse
    p = argparse.ArgumentParser(prog="kising_charge build")
    p.add_argument("fetch")
    p.add_argument("out")
    p.add_argument("--arm", required=True)
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--L", type=int, required=True)
    p.add_argument("--h", type=float, default=0.6)
    p.add_argument("--shots", type=int, default=1000)
    p.add_argument("--coef", type=float, nargs=2, default=None,
                   help="the declared charge (b, c); default: computed by charges() at this n")
    a = p.parse_args(argv)
    if a.n % 2:
        print("STOP: n must be even (Neel inputs, two Y settings)", file=sys.stderr)
        return 2
    from toqb import s2r as S
    from toqb import s2r2 as S2
    from toqb.fold_lam import active
    from toqb.s2rc import predict_job
    tfile = os.path.abspath(os.path.join(a.fetch, "target.pkl"))
    fj = json.load(open(os.path.join(a.fetch, "fetch.json"), encoding="utf-8"))
    if sha256_file(tfile) != fj["target_sha256"]:
        print("STOP: target.pkl differs from fetch.json's hash", file=sys.stderr)
        return 2
    name = f"kcharge_n{a.n}_L{a.L}_h{a.h:g}-{a.arm.replace(':', '_')}"
    os.makedirs(a.out, exist_ok=True)
    jf, qf = os.path.join(a.out, name + ".json"), os.path.join(a.out, name + ".qpy")
    for f in (jf, qf):
        if os.path.exists(f):
            print(f"STOP: {f} exists: a run never overwrites another", file=sys.stderr)
            return 2
    t0 = time.perf_counter()
    if a.coef is not None:
        coef, cinfo = tuple(a.coef), dict(source="declared")
    else:
        ch = charges(a.n, a.h)
        coef, cinfo = ch["coef"], dict(source=f"charges(n={a.n}, h={a.h})", zz_share=ch["zz_share"],
                                       edge_spread=ch["edge_spread"], dim=ch["dim"])
    task = dict(n=a.n, layers=a.L, enc=float(np.pi / 2))
    pr = dict(traj=0, seed=7, shots=a.shots, reps=200, level=0.99)
    plan = dict(name=f"noise wall P1: {name}", device="file:" + tfile, verify=False, task=task, predict=pr,
                standin=dict(t12=0.3, over=0.01, zz_hz=1e4, seed=20261017))
    R = S2.Runner(plan, a.arm)
    points, cs = [], []
    for i in INPUTS:
        for s in SETTINGS:
            bits = input_bits(i, a.n)
            cs.append(R.arm.compile(circuit(bits, s, a.n, a.L, a.h)))
            points.append(dict(input=i, setting=s, noiseless=None, q_exact_input=q_noiseless(bits, a.n)))
    meas0 = None
    for i in INPUTS:
        bits = input_bits(i, a.n)
        rc, meas = reference_circuit(cs[0], bits)
        meas0 = meas
        cs.append(rc)
        points.append(dict(input=i, setting="ref", noiseless=q_noiseless(bits, a.n), q_exact_input=q_noiseless(bits, a.n)))
    # every dynamic circuit of the record must measure on the same physical qubits as cs[0] (one template)
    for c in cs[:len(INPUTS) * len(SETTINGS)]:
        mm = {c.find_bit(x.clbits[0]).index: c.find_bit(x.qubits[0]).index for x in c.data if x.operation.name == "measure"}
        if mm != meas0:
            print("STOP: the compiled circuits of one record measure on different qubits", file=sys.stderr)
            return 2
    d, q2 = R.arm.duration(cs[0], (a.n, a.L))
    labels = np.ones(len(cs), dtype=int)
    p1 = np.full(len(cs), 0.5)
    rec = dict(kind="s2rc", lam_test=True, charge_test=True, arm=a.arm, seed=0, plan=plan["name"], task=task,
               predict=pr, standin=plan["standin"], verify=False, device=plan["device"],
               target_sha256=fj["target_sha256"], version=R.arm.version(), final_mean=[], loops=0, started=S._cest(),
               charge=dict(h=a.h, J="pi/4", coef_YZ=coef[0], coef_ZY=coef[1], info=cinfo, inputs=list(INPUTS),
                           settings=list(SETTINGS), measured_qubits={str(k): v for k, v in sorted(meas0.items())}),
               points=points, q_exact={i: q_noiseless(input_bits(i, a.n), a.n) for i in INPUTS},
               inputs=[input_bits(p_["input"], a.n) for p_ in points],
               noiseless_z=[float(p_["q_exact_input"]) for p_ in points], twin=None,
               q2=int(q2), us=round(d * 1e6, 3), active=int(active(cs[0])))
    rec["prediction"] = predict_job(p1, labels, a.shots, pr["reps"], pr["level"], pr["seed"] + 1)
    rec["prediction_shots_only"] = predict_job(p1, labels, a.shots, pr["reps"], pr["level"], pr["seed"] + 1)
    rec["prediction"]["twin_p1"] = [float(x) for x in p1]
    rec["test_labels"] = [int(v) for v in labels]  # placeholders: only so that assemble can read the record
    from qiskit import qpy
    with open(qf, "wb") as f:
        qpy.dump(list(cs), f)
    rec["export"] = dict(qpy=os.path.basename(qf), circuits=len(cs), sha256=sha256_file(qf))
    rec.update(wall_s=time.perf_counter() - t0, structural_fail=R.arm.structural_fail,
               on_failed_ops=R.arm.on_failed_ops, ended=S._cest())
    rec["valid"] = not R.arm.structural_fail and not R.arm.on_failed_ops
    json.dump(rec, open(jf, "w", encoding="utf-8"))
    print(f"{name}: {len(cs)} circuits (12 + 4 references), {q2} two-qubit gates, {d * 1e6:.2f} us; charge (b, c) = "
          f"({coef[0]:.5f}, {coef[1]:.5f}); valid {rec['valid']}")
    return 0 if rec["valid"] else 2


def p2_predict(cells, p, p_range):
    """Formula slope for P2 cells (kising lam records) at a given p, with the declared rule of toqb.kising_formula."""
    from toqb import kising_formula as KF
    out = []
    for c in cells:
        a = (c["inputs"], c["noiseless_z"], c["n"], c["L"], c["h"])
        lp = KF.lam_formula(*a, p)
        ends = [KF.lam_formula(*a, q) for q in p_range if q is not None]
        sp = (max(ends) - min(ends)) / 2 if len(ends) == 2 else 0.0
        tol = 2 * float(np.hypot(c["se"], sp))
        d = c["lam"] - lp
        out.append(dict(name=c["name"], arm=c["arm"], n=c["n"], L=c["L"], lam_device=c["lam"], se_device=c["se"],
                        lam_pred=lp, se_pred=sp, diff=d, two_se=tol,
                        verdict="AGREE" if abs(d) <= tol else ("BELOW" if d < 0 else "ABOVE")))
    return out


def self_ref_verdicts(cells, ref_n=20, ref_L=24, arm="fold:rule"):
    """Second-device rule (noise wall stage 1, second device): p is fixed by the device's own reference cell (arm, ref_n,
    ref_L) alone, p = p_eff(rho_ref), with its range from rho_ref -+ SE; every other cell of the same arm is then
    predicted, rho_pred = (1 - 4p/3)^(2L), with SE_pred = half the spread of rho_pred over the p range, and judged
    INSIDE if |rho - rho_pred| <= 2 sqrt(SE^2 + SE_pred^2) (as toqb.kising_formula). Returns (p, p_range, verdicts);
    p is None if the reference is missing or rho_ref <= 0."""
    ref = [c for c in cells if c["arm"] == arm and c["n"] == ref_n and c["L"] == ref_L]
    if len(ref) != 1 or ref[0]["p_eff"] is None:
        return None, [None, None], []
    r = ref[0]
    p = r["p_eff"]
    p_lo, p_hi = p_eff(r["rho4"] + r["se4"], ref_L), p_eff(r["rho4"] - r["se4"], ref_L)
    out = []
    for c in cells:
        if c["arm"] != arm or c is r:
            continue
        pred = rho_predicted(p, c["L"])
        ends = [rho_predicted(q, c["L"]) for q in (p_lo, p_hi) if q is not None]
        sp = (max(ends) - min(ends)) / 2 if len(ends) == 2 else float("nan")
        tol = 2 * float(np.hypot(c["se4"], sp)) if np.isfinite(sp) else 2 * c["se4"]
        out.append(dict(name=c["name"], arm=c["arm"], n=c["n"], L=c["L"], rho4=c["rho4"], se4=c["se4"], rho_pred=pred,
                        se_pred=sp, two_se=tol, inside_2se=bool(abs(c["rho4"] - pred) <= tol)))
    return p, [p_lo, p_hi], out


def cmd_score(argv):
    import argparse
    p = argparse.ArgumentParser(prog="kising_charge score")
    p.add_argument("job")
    p.add_argument("runs")
    p.add_argument("--p", type=float, default=None, help="the declared p for the predictions (e.g. 0.0051)")
    p.add_argument("--p-range", type=float, nargs=2, default=None)
    p.add_argument("--p-from-n", type=int, default=None, help="take p from P1 of fold:rule at this n (at --p-L)")
    p.add_argument("--p-L", type=int, default=50)
    p.add_argument("--self-ref-n", type=int, default=None,
                   help="second-device rule: p from this device's own fold:rule cell at this n (and --self-ref-L)")
    p.add_argument("--self-ref-L", type=int, default=24)
    p.add_argument("--p2-job", default=None, help="the P2 job folder (lam_device score must have run there)")
    p.add_argument("--p2-runs", default=None)
    p.add_argument("--out-name", default="charge_score.json", help="output file in JOB (never overwritten)")
    a = p.parse_args(argv)
    man = json.load(open(os.path.join(a.job, "manifest.json")))
    raw = json.load(open(os.path.join(a.job, "raw_counts.json")))
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    cells = []
    for cid, c in enumerate(man["cells"]):
        rf = os.path.join(a.runs, c["name"] + ".json")
        if sha256_file(rf) != c["run_sha256"]:
            raise SystemExit(f"STOP: {rf} differs from the manifest")
        rec = json.load(open(rf))
        if not rec.get("charge_test"):
            continue
        n, L = rec["task"]["n"], rec["task"]["layers"]
        coef = (rec["charge"]["coef_YZ"], rec["charge"]["coef_ZY"])
        cc = {}
        for k, pub in enumerate(man["pubs"]):
            if pub["cell"] == cid:
                pt = rec["points"][pub["point"]]
                cc[(pt["input"], pt["setting"])] = rows[k]
        est = estimate(cc, n, L, coef)
        cells.append(dict(name=c["name"], arm=rec["arm"], n=n, L=L, q2=rec.get("q2"), us=rec.get("us"),
                          measured_qubits=rec["charge"]["measured_qubits"], **est))
    self_ref = a.self_ref_n is not None
    if self_ref:
        p_used, p_rng, verdicts = self_ref_verdicts(cells, a.self_ref_n, a.self_ref_L)
        if p_used is None:
            raise SystemExit("STOP: no usable fold:rule cell for --self-ref-n / --self-ref-L")
        p_src = f"self-reference fold:rule n={a.self_ref_n} L={a.self_ref_L}"
    elif a.p_from_n is not None:
        ref = [c for c in cells if c["arm"] == "fold:rule" and c["n"] == a.p_from_n and c["L"] == a.p_L]
        if len(ref) != 1 or ref[0]["p_eff"] is None:
            raise SystemExit("STOP: no usable reference cell for --p-from-n")
        p_used, p_rng, p_src = ref[0]["p_eff"], ref[0]["p_eff_range"], f"P1 fold:rule n={a.p_from_n} L={a.p_L}"
    else:
        p_used, p_rng, p_src = a.p, a.p_range or [None, None], "declared"
    if not self_ref:
        verdicts = []
    for c in ([] if self_ref else cells):
        if p_used is None:
            break
        pred = rho_predicted(p_used, c["L"])
        ok = abs(c["rho4"] - pred) <= 2 * c["se4"]
        c["rho_pred"] = pred
        verdicts.append(dict(name=c["name"], arm=c["arm"], n=c["n"], L=c["L"], rho4=c["rho4"], se4=c["se4"],
                             rho_pred=pred, inside_2se=bool(ok)))
    # n-independence (same arm and L): |rho(n1) - rho(n2)| <= 2 SE
    nind = []
    keyd = {}
    for c in cells:
        keyd.setdefault((c["arm"], c["L"]), []).append(c)
    for (arm, L), g in sorted(keyd.items()):
        g = sorted(g, key=lambda x: x["n"])
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                d = g[j]["rho4"] - g[i]["rho4"]
                se = float(np.hypot(g[i]["se4"], g[j]["se4"]))
                nind.append(dict(arm=arm, L=L, n=[g[i]["n"], g[j]["n"]], diff=d, se=se, same=bool(abs(d) <= 2 * se)))
    # arms against each other (same n, L): WIN / LOSS / TIE at 2 SE, as D6
    duel = []
    keyn = {}
    for c in cells:
        keyn.setdefault((c["n"], c["L"]), {})[c["arm"]] = c
    for (n, L), g in sorted(keyn.items()):
        if "fold:rule" not in g:
            continue
        r = g["fold:rule"]
        for other in sorted(g):
            if other == "fold:rule":
                continue
            o = g[other]
            d = r["rho4"] - o["rho4"]
            se = float(np.hypot(r["se4"], o["se4"]))
            duel.append(dict(n=n, L=L, other=other, diff=d, se=se,
                             verdict="WIN" if d > 2 * se else ("LOSS" if d < -2 * se else "TIE")))
    for c in cells:
        pe = "n/a" if c["p_eff"] is None else f"{c['p_eff']:.5f}"
        print(f"{c['name']:44s} rho4 {c['rho4']:.4f} +- {c['se4']:.4f} | |0..0> only {c['rho1']:.4f} +- {c['se1']:.4f}"
              f" | p_eff {pe} | {c['q2']} two-qubit gates, {c['us']} us")
    for v in verdicts:
        print(f"P1 n {v['n']} L {v['L']} {v['arm']}: rho4 {v['rho4']:.4f} +- {v['se4']:.4f}, predicted {v['rho_pred']:.4f}"
              f" ({p_src} p = {p_used:.5f}): {'INSIDE' if v['inside_2se'] else 'OUTSIDE'} 2 SE")
    for x in nind:
        print(f"n-independence {x['arm']} L {x['L']} n {x['n']}: diff {x['diff']:+.4f} +- {x['se']:.4f}: "
              f"{'SAME' if x['same'] else 'DIFFERENT'}")
    for x in duel:
        print(f"n {x['n']} L {x['L']}: fold:rule - {x['other']}: {x['diff']:+.4f} +- {x['se']:.4f}: {x['verdict']}")
    wl = wall(cells, p_used, p_rng)
    for f in wl["fits"]:
        ls = "n/a" if f["L_star"] is None else f"{f['L_star']:.1f} +- {f['se']:.1f}"
        print(f"readable depth {f['arm']} n {f['n']}: L* {ls} (fit over L = {f['Ls']})")
    for x in wl["ref_prediction"] or []:
        print(f"L* fold:rule n {x['n']}: {x['L_star']:.1f} +- {x['se']:.1f}, predicted {x['pred']:.1f} +- "
              f"{x['se_pred']:.1f} ({p_src}): {x['verdict']}")
    for x in wl["relative"]:
        if "kappa" not in x:
            print(f"Delta L {x['arm']} n {x['n']}: n/a")
            continue
        s = (f"Delta L {x['arm']} n {x['n']}: L* {x['L_star']:.1f}, Delta L {x['delta_L']:+.1f} +- {x['se_delta_L']:.1f},"
             f" kappa {x['kappa']:.2f} +- {x['se_kappa']:.2f}")
        if "bracket" in x:
            s += f" | gates {x['g']:.2f}, duration {x['t']:.2f}: rule A {x['rule_A']}"
        if "phi" in x:
            s += f" | phi {x['phi']:.2f} +- {x['se_phi']:.2f}"
        print(s)
    for x in wl["phi_consistency"]:
        print(f"phi n-consistency {x['arm']} n {x['n']}: diff {x['diff']:+.2f} +- {x['se']:.2f}: {x['verdict']}")
    p2 = None
    if a.p2_job and a.p2_runs and p_used is not None:
        sc = json.load(open(os.path.join(a.p2_job, "lam_score.json")))
        pc = []
        for c in sc["cells"]:
            rec = json.load(open(os.path.join(a.p2_runs, c["name"] + ".json")))
            if not rec.get("kising"):
                continue
            pc.append(dict(name=c["name"], arm=c["arm"], n=c["n"], L=c["L"], h=rec["kising"]["h"],
                           inputs=rec["inputs"], noiseless_z=rec["noiseless_z"], lam=c["device"]["lam"],
                           se=c["device"]["se"]))
        p2 = p2_predict(pc, p_used, p_rng)
        for x in p2:
            print(f"P2 {x['name']}: device {x['lam_device']:.3f} +- {x['se_device']:.3f} | formula {x['lam_pred']:.3f}"
                  f" +- {x['se_pred']:.3f}: {x['verdict']}")
    out = os.path.join(a.job, a.out_name)
    res = dict(cells=cells, p=dict(value=p_used, range=p_rng, source=p_src), p1_verdicts=verdicts,
               n_independence=nind, duels=duel, wall=wl, p2=p2)
    if os.path.exists(out):
        print(f"{out} exists; not written")
    else:
        json.dump(res, open(out, "w"), default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    return 0


def se_model(rho, n, shots, coef):
    """Approximate SE of the four-input rho from shot noise alone, treating the n terms of each setting as independent
    +-1 variables (per shot: variance n for "Z", n (b^2 + c^2) / 2 for each Y setting; reference: n)."""
    b, c = coef
    v_in = n * (1 + (b * b + c * c)) / shots  # one input, three settings
    v_num, v_den = 4 * v_in, 4 * n / shots
    return float(np.sqrt(v_num + rho * rho * v_den) / (4 * n))


def cmd_rehearse(argv):
    """Before any device: the predicted rho of every P1 record at the declared p, and its shot-noise SE (se_model)."""
    import argparse
    import glob
    p = argparse.ArgumentParser(prog="kising_charge rehearse")
    p.add_argument("runs")
    p.add_argument("--p", type=float, required=True)
    a = p.parse_args(argv)
    cells = []
    for f in sorted(glob.glob(os.path.join(a.runs, "kcharge_*.json"))):
        r = json.load(open(f))
        n, L, S = r["task"]["n"], r["task"]["layers"], r["predict"]["shots"]
        coef = (r["charge"]["coef_YZ"], r["charge"]["coef_ZY"])
        rho = rho_predicted(a.p, L)
        print(f"{os.path.basename(f)[:-5]:44s} predicted rho {rho:.4f}, shot-noise SE about {se_model(rho, n, S, coef):.4f}"
              f" ({S} shots per circuit); {r['q2']} two-qubit gates, {r['us']} us")
        cells.append(dict(arm=r["arm"], n=n, L=L, q2=r["q2"], us=r["us"], rho4=rho, se4=se_model(rho, n, S, coef)))
    # readable depth: the reference's predicted L*, and each other arm's structure bracket from its records alone
    lp = decay_length_predicted(a.p)
    print(f"predicted L* (fold:rule) at p = {a.p}: {lp:.1f}")
    for x in wall(cells)["relative"]:
        if x.get("g") is None or x.get("t") is None:
            continue
        lo, hi = min(x["g"], x["t"]), max(x["g"], x["t"])
        print(f"{x['arm']} n {x['n']}: gates {x['g']:.2f}, duration {x['t']:.2f} -> kappa in [{lo:.2f}, {hi:.2f}], "
              f"L* in [{lp / hi:.1f}, {lp / lo:.1f}], Delta L in [{lp - lp / lo:.1f}, {lp - lp / hi:.1f}]")
    return 0


def main(argv):
    if not argv or argv[0] not in ("charges", "build", "score", "rehearse"):
        print(__doc__)
        return 1
    return {"charges": cmd_charges, "build": cmd_build, "score": cmd_score,
            "rehearse": cmd_rehearse}[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
