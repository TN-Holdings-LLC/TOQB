"""Task C, part 2 (home, 2026-11-12): Trotter error at dt 0.5 (half the depth) against dt 0.25 (the device's), same
times, two sizes, against the continuum from Richardson (dt/4, dt/8 of 0.25). usage: python coarse.py L [L ...]"""
import sys
import numpy as np
sys.path.insert(0, "../hubbard_2026-11-11")
import hub_cost as HC


def z(L, dt, jt):
    HC.DT = dt
    out, _, _ = HC.run_quimb(HC.blocks(HC.circuit(L, int(round(jt / dt)))), 1024)
    HC.DT = 0.25
    return np.asarray(out)


for L in map(int, sys.argv[1:]):
    for jt in (1.0, 1.5):
        z0 = 2 * z(L, 0.25 / 8, jt) - z(L, 0.25 / 4, jt)
        r = {dt: float(np.mean((z(L, dt, jt) - z0) ** 2)) for dt in (0.5, 0.25)}
        print(f"L {L} Jt {jt}: Trotter MSE dt 0.5 ({int(jt / 0.5)} steps) {r[0.5]:.2e}, dt 0.25 ({int(jt / 0.25)} steps) "
              f"{r[0.25]:.2e}; mean square of the continuum {np.mean(z0 ** 2):.4f}", flush=True)
