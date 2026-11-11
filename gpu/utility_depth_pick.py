"""Device choice of prereg/utility_depth_2026-11-11.md, from the night's daily record only (home, 2026-11-11).

Order: fewest pending jobs (queue.json; ties in the order marrakesh, fez, kingston). The first device on which every
one of the seven cones avoids every failed element (on one of the two embeddings); none: the first on which z106_t4
to z106_t6 and w10_t5 do (the rest not built); none: not run. Prints the per-device table and the build command.
A device on which the ring sentinel does not land counts as not buildable: run the build, and on that failure take
the next device this script lists.
usage: python gpu/utility_depth_pick.py FETCH_DIR
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import utility_build as UB  # noqa: E402
import utility_exact as UE  # noqa: E402
import utility_tn as UT  # noqa: E402

ALL = ["z106_t4", "z106_t5", "z106_t6", "z106_t7", "z106_t8", "w10_t5", "w10_t6"]
CORE = ["z106_t4", "z106_t5", "z106_t6", "w10_t5"]
ORDER = ["ibm_marrakesh", "ibm_fez", "ibm_kingston"]


def placeable(dev_json):
    fq = {int(q) for q in dev_json["failed_qubits"]}
    fe = {tuple(sorted(map(int, e))) for e in dev_json["failed_couplers"]}
    embs, eg = UB.embeddings(dev_json, UE.eagle_edges())
    out = {}
    for name in ALL:
        obs, t, ex = UT.OBS[name]
        cq, ce = UB.cone(obs, t, eg)
        out[name] = next((i for i, inv in enumerate(embs)
                          if not any(inv[q] in fq for q in cq)
                          and not any(tuple(sorted((inv[x], inv[y]))) in fe for x, y in ce)), None)
    return out, len(fq), len(fe)


def main(fetch):
    q = json.load(open(os.path.join(fetch, "queue.json")))["pending"]
    devs = sorted((d for d in ORDER if os.path.exists(os.path.join(fetch, d, "dev", "device.json"))),
                  key=lambda d: (q.get(d, 10 ** 6), ORDER.index(d)))
    rows = []
    for d in devs:
        pl, nq, ne = placeable(json.load(open(os.path.join(fetch, d, "dev", "device.json"))))
        rows.append((d, pl))
        print(f"{d:14} pending {q.get(d)}  failed qubits {nq} couplers {ne}  " +
              " ".join(f"{n}:{'-' if pl[n] is None else pl[n]}" for n in ALL))
    for tier, need in (("all seven", ALL), ("core four", CORE)):
        cand = [d for d, pl in rows if all(pl[n] is not None for n in need)]
        if cand:
            pick = cand[0]
            obs = [n for n in ALL if dict(rows)[pick][n] is not None] if tier == "core four" else ALL
            print(f"CHOSEN ({tier}): {pick}; next if the sentinel does not land: {cand[1:] or 'none'}")
            print(f"build: python gpu/utility_build.py {fetch}/{pick}/dev OUT ANS SEALED_DIR --obs {','.join(obs)} "
                  f"--max-seconds 160")
            return pick
    print("NOT RUN: no device places the core four")
    return None


if __name__ == "__main__":
    main(sys.argv[1])
