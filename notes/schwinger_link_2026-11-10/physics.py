"""What the one-qubit truncation keeps (gpu/schwinger_link.py): the configurations reachable from the bare vacuum,
whether a pair can separate, and nu(t) truncated against full (answers of 11-09 are released; values printed)."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "gpu"))
import schwinger as S  # noqa: E402
import schwinger_link as SL  # noqa: E402

for N in (6, 8):
    HP, confs = SL.trunc_hamiltonian(N, S.PARAMS[0])
    v = SL.vacuum_index(confs, N)
    reach, front = {v}, [v]
    while front:
        i = front.pop()
        for j in np.nonzero(np.abs(HP[i]) > 1e-12)[0]:
            if j not in reach:
                reach.add(int(j))
                front.append(int(j))
    vac = sum(1 << (k - 1) for k in range(2, N + 1, 2))
    pairs_only = True
    for i in reach:
        z = [1 - 2 * ((confs[i] >> (k - 1)) & 1) for k in range(1, N + 1)]
        L = SL.field_of_bits(z)
        n_p = bin(confs[i] ^ vac).count("1")
        n_l = sum(1 for x in L if x != 0)
        pairs_only &= (n_p == 2 * n_l)
    print(f"N {N}: reachable from the vacuum {len(reach)} configurations (kept {len(confs)}); every reachable one has "
          f"particles = 2 x non-zero links (only neighbouring pairs, no separated pair): {pairs_only}")
    full = S.hamiltonian(N, *S.PARAMS[0][1:])
    # full model's charge-0 sector reachable from the vacuum
    reach_f, front = {vac}, [vac]
    while front:
        i = front.pop()
        for j in np.nonzero(np.abs(full[i]) > 1e-12)[0]:
            if j not in reach_f:
                reach_f.add(int(j))
                front.append(int(j))
    print(f"N {N}: full model reachable from the vacuum {len(reach_f)} configurations")
    for t in (0.5, 1.0, 1.5, 2.0):
        z1, z3 = SL.z_trunc_continuous(N, t, S.PARAMS[0]), SL.z_trunc_continuous(N, t, S.PARAMS[2])
        f1, f3 = S.z_continuous(N, t, S.PARAMS[0]), S.z_continuous(N, t, S.PARAMS[2])
        print(f"   t {t}: truncated M1 - M3 max |dZ| {max(abs(a - b) for a, b in zip(z1, z3)):.1e}; full M1 - M3 "
              f"{max(abs(a - b) for a, b in zip(f1, f3)):.3f}")
    print(f"N {N}: nu(t), full exact / truncated exact")
    print("| t | " + " | ".join(f"{p[0]} full | {p[0]} trunc" for p in S.PARAMS) + " |")
    print("|---|" + "---|---|" * len(S.PARAMS))
    for s in range(1, 9):
        t = s * S.DT
        row = []
        for p in S.PARAMS:
            row += [f"{SL.nu(S.z_continuous(N, t, p)):.3f}", f"{SL.nu(SL.z_trunc_continuous(N, t, p)):.3f}"]
        print(f"| {t:.2f} | " + " | ".join(row) + " |")
