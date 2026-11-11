"""Answers for the 1D Fermi-Hubbard device job (home, 2026-11-11): per-qubit <Z> of the Trotter circuit itself
(interleaved Jordan-Wigner, fermionic swaps, Neel start, J 1, dt 0.25; notes/hubbard_2026-11-11/hub_cost.py, checked
exact against the model there), for U = 4 by quimb's CircuitMPS on two-qubit blocks (cutoff 1e-12, bond cap CHI) and
for U = 0 by free fermions (hub_ruler.ruler_z, exact at any size). Values go only to OUT.json (sealed until the
verdicts); printed are checks only: bond, quimb's error estimate, the conserved sums (sum <Z> = 0 at half filling;
up minus down = 0), the per-site charge (Z_up(i) + Z_dn(i) = 0 for the Neel start at any U), and for U = 0 the quimb
pipeline against the free-fermion values.
usage: python gpu/hub_answers.py OUT.json --L 20 30 --steps 2 4 6 [--chi 1024] [--pipeline-check]
"""
import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "notes", "hubbard_2026-11-11"))
sys.path.insert(0, HERE)  # a flat copy (hub_cost.py, hub_ruler.py next to this file) also works
import hub_cost as HC  # noqa: E402
import hub_ruler as HR  # noqa: E402

U4 = 4.0


def circuit(L, steps, U):
    """hub_cost.circuit with U as a parameter (hub_cost fixes U = 4)."""
    old = HC.U
    HC.U = U
    try:
        return HC.circuit(L, steps)
    finally:
        HC.U = old


def checks(z, L):
    up, dn = z[0::2], z[1::2]
    charge = np.array([z[2 * i] + z[2 * i + 1] for i in range(L)])
    return dict(sum_z=float(z.sum()), up_minus_dn=float(up.sum() - dn.sum()), charge_max=float(np.abs(charge).max()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--L", type=int, nargs="+", default=[20])
    ap.add_argument("--steps", type=int, nargs="+", default=[2, 4, 6])
    ap.add_argument("--chi", type=int, default=1024)
    ap.add_argument("--pipeline-check", action="store_true")
    a = ap.parse_args()
    vals = json.load(open(a.out)) if os.path.exists(a.out) else {}
    for L in a.L:
        for s in a.steps:
            z0 = np.array(HR.ruler_z(L, s), dtype=float)
            vals[f"L{L}_s{s}_U0"] = z0.tolist()
            print(f"L {L} steps {s} U 0 (free fermions): {checks(z0, L)}", flush=True)
            if a.pipeline_check:
                t0 = time.time()
                zq, bond, err = HC.run_quimb(HC.blocks(circuit(L, s, 0.0)), a.chi)
                print(f"   pipeline: quimb on the U = 0 circuit against free fermions |diff| "
                      f"{np.abs(zq - z0).max():.1e} (bond {bond}, {time.time() - t0:.0f} s)", flush=True)
            t0 = time.time()
            z4, bond, err = HC.run_quimb(HC.blocks(circuit(L, s, U4)), a.chi)
            vals[f"L{L}_s{s}_U4"] = z4.tolist()
            print(f"L {L} steps {s} U 4 (quimb chi {a.chi}): bond {bond} error estimate {err} {checks(z4, L)} "
                  f"{time.time() - t0:.0f} s", flush=True)
            json.dump(vals, open(a.out, "w"), sort_keys=True)


if __name__ == "__main__":
    main()
