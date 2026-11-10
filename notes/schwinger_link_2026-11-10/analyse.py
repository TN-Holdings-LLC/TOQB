"""Schwinger with link qubits (gpu/schwinger_link.py): CZ table, truncation and Trotter errors, circuit check.
Prints differences only (no answer values of the declared 11-09 sets).

Formats avoid four-decimal numbers (daily/seal.py leakcheck matches any 4-decimal string against the sealed values).
usage: python notes/schwinger_link_2026-11-10/analyse.py {cz|errors|circuit} [--Ns ...] [--steps ...]
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "gpu"))
import schwinger as S  # noqa: E402
import schwinger_link as SL  # noqa: E402


def cz_table(Ns):
    print("| N | qubits (link) | CZ per step (link) | CZ per qubit per step (link) | qubits (swap network) | "
          "CZ per step (swap network) | CZ per qubit per step (swap network) |")
    print("|---|---|---|---|---|---|---|")
    m1 = S.PARAMS[0]
    for N in Ns:
        c = SL.trotter(N, 1, m1).count_ops().get("cx", 0)
        assert c == SL.cz_per_step(N)
        nq = SL.nqubits(N)
        sw = S.trotter(N, 1, m1).count_ops().get("cx", 0)
        print(f"| {N} | {nq} | {c} | {c / nq:.2f} | {N} | {sw} | {sw / N:.0f} |")


def errors(Ns, steps):
    print("max over sites of |<Z_n> difference| and |nu difference|; t = steps x dt (dt 0.25)")
    print("truncation = truncated exact (exp(-i PHP t)) - full exact (gpu/schwinger.z_continuous);")
    print("Trotter(link) = link circuit - truncated exact; total = link circuit - full exact;")
    print("Trotter(swap) = gpu/schwinger's circuit - full exact (its own Trotter error, for comparison)")
    for N in Ns:
        _, confs = SL.trunc_hamiltonian(N, S.PARAMS[0])
        print(f"== N {N}: {SL.nqubits(N)} qubits, kept configurations {len(confs)} of {2 ** N} "
              f"(full model: all {2 ** N}; the charge-0 sector is inside them)")
        for p in S.PARAMS:
            print(f"-- {p[0]} (w {p[1]}, J {p[2]}, m {p[3]}, eps0 {p[4]})")
            print("| step | t | trunc Z | trunc nu | Trotter(link) Z | Trotter(link) nu | total Z | total nu | "
                  "Trotter(swap) Z | Trotter(swap) nu | Gauss |")
            print("|---|---|---|---|---|---|---|---|---|---|---|")
            for s in steps:
                t = s * S.DT
                zf = S.z_continuous(N, t, p)
                zt = SL.z_trunc_continuous(N, t, p)
                zc, g = SL.circuit_answers(N, s, p)
                zs = S.z_sites(S.trotter(N, s, p), N, s)
                d = lambda a, b: max(abs(x - y) for x, y in zip(a, b))
                dn = lambda a, b: abs(SL.nu(a) - SL.nu(b))
                print(f"| {s} | {t:.2f} | {d(zt, zf):.3f} | {dn(zt, zf):.1e} | {d(zc, zt):.3f} | {dn(zc, zt):.1e} | "
                      f"{d(zc, zf):.3f} | {dn(zc, zf):.1e} | {d(zs, zf):.3f} | {dn(zs, zf):.1e} | {g:.0e} |",
                      flush=True)


def circuit(Ns, steps):
    print("link circuit by statevector (Aer above 20 qubits) against the same Trotter product on the kept "
          "configurations (z_trotter_reduced); Gauss = max_n <G_n^2>")
    worst = 0.0
    for N in Ns:
        for p in (S.PARAMS if N <= 10 else S.PARAMS[:1]):
            for s in steps:
                t0 = time.time()
                z, g = SL.circuit_answers(N, s, p)
                t1 = time.time()
                zr = SL.z_trotter_reduced(N, s, p)
                d = max(abs(a - b) for a, b in zip(z, zr))
                worst = max(worst, d, g)
                print(f"N {N} ({SL.nqubits(N)} qubits) {p[0]} steps {s}: max |circuit - reduced| {d:.1e}, Gauss {g:.0e}"
                      f"  {'MATCH' if max(d, g) <= 1e-10 else 'DIFFERS'}  ({t1 - t0:.1f} s)", flush=True)
    print(f"== CIRCUIT CHECK: worst {worst:.1e} ({'MATCH' if worst <= 1e-10 else 'DIFFERS'}, tolerance 1e-10)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["cz", "errors", "circuit"])
    ap.add_argument("--Ns", default=None)
    ap.add_argument("--steps", default=None)
    a = ap.parse_args()
    Ns = [int(v) for v in a.Ns.split(",")] if a.Ns else None
    st = [int(v) for v in a.steps.split(",")] if a.steps else None
    if a.what == "cz":
        cz_table(Ns or [6, 8, 10, 12, 14, 16])
    elif a.what == "errors":
        errors(Ns or [6, 8], st or list(range(1, 9)))
    else:
        circuit(Ns or [6, 8, 10], st or [1, 2, 4])
