"""Build one device job of Schwinger-model pair production from the bare vacuum (Martinez et al. 2016 parameters),
raw, through psf-os's user entrance (owner 2026-11-09 15:30 JST "良いです"; workplace candidates
notes/schwinger_2026-11-09).

Per N (6 and 8): the chain is the first qualifying copy of the first qualifying shape (daily/du91.SHAPES, fixed order),
else rule C (psf_os.chain.place); the user circuits are gpu/schwinger.trotter on that chain's labels, without
measurement (the entrance measures every touched qubit in label order); psf_os.user2d.build_batch places each by
translation with its floor and mirror; one ring sentinel. Answers: the exact <Z> of every site (the Trotter circuit's
own output, full statevector) written on the label where the swap network leaves that site at the end.

usage: PYTHONPATH=<psf-os>:<TOQB>:<TOQB>/gpu python gpu/schw_build.py DEV OUT ANSWERS_OUT [--ns 6,8] [--steps 1,2,5]
       [--params M1,M2,M3] [--shots 4000] [--max-seconds 120] [--dry-clifford-sentinel]
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import schwinger as S  # noqa: E402
from daily import du91 as X  # noqa: E402


def chain_for(dev, n):
    pl = X.place(dev, n)
    if pl["shape"] is not None:
        sh = next(s for s in X.SHAPES if s[0] == pl["shape"])
        return dict(rule="shape " + pl["shape"], chain=list(X.snake(n, sh)), copy=[pl["drow"], pl["dcol"]])
    from psf_os import chain as CH
    c = CH.place(dev, n)
    return dict(rule="C", chain=list(c["chain"]), start=c["start"], steps=c["steps"])


def site_exact(n, st, p):
    """Exact <Z_site>, site 1..n, of the Trotter circuit."""
    return S.z_sites(S.trotter(n, st, p), n, st)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("device")
    ap.add_argument("out")
    ap.add_argument("answers_out")
    ap.add_argument("--ns", default="6,8")
    ap.add_argument("--steps", default="1,2,5")
    ap.add_argument("--params", default="M1,M2,M3")
    ap.add_argument("--shots", type=int, default=4000)
    ap.add_argument("--max-seconds", type=float, default=120)
    ap.add_argument("--dry-clifford-sentinel", action="store_true")
    a = ap.parse_args()
    for p in (a.out, a.answers_out):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    from psf_os import device as Dv
    from psf_os import user2d as U
    dev = Dv.Device.load(a.device)
    ns = [int(v) for v in a.ns.split(",")]
    steps = [int(v) for v in a.steps.split(",")]
    params = [next(x for x in S.PARAMS if x[0] == name) for name in a.params.split(",")]
    items, answers, chains, meta = [], {}, {}, {}
    for n in ns:
        chains[n] = chain_for(dev, n)
        lab = chains[n]["chain"]
        for p in params:
            for st in steps:
                tag = f"sw{n}_{p[0]}_s{st}"
                items.append((tag, S.trotter(n, st, p, chain=lab, measure=False)))
                z = site_exact(n, st, p)
                at = S.final_at(n, st)                      # site held at each chain position at the end
                answers[tag] = {str(lab[pos]): z[at[pos] - 1] for pos in range(n)}
                meta[tag] = dict(n=n, params=p[0], steps=st, label_of_site={str(at[pos]): lab[pos] for pos in range(n)})
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None
    rep = U.build_batch(dev, items, os.path.join(a.out, "job_build"), shots=a.shots, sentinel_spec=spec,
                        max_seconds=a.max_seconds)
    with open(a.answers_out, "w") as f:
        json.dump(answers, f, indent=1, sort_keys=True)
    ans_sha = hashlib.sha256(open(a.answers_out, "rb").read()).hexdigest()
    log = dict(device=dev.name, chains={str(k): v for k, v in chains.items()}, items=meta,
               cz={t: r["cz"] for t, r in rep["items"].items()}, copies={t: r["copy"] for t, r in rep["items"].items()},
               circuits=rep["circuits"], qpu_seconds_model=rep["qpu_seconds_model"], answers_sha256=ans_sha)
    json.dump(log, open(os.path.join(a.out, "build.json"), "w"), indent=1)
    for n, c in chains.items():
        print(f"N {n}: {c['rule']} chain {c['chain']}")
    for t, r in rep["items"].items():
        print(f"{t:14} CZ {r['cz']:4}  copy {r['copy']}")
    print(f"circuits {rep['circuits']}  model {rep['qpu_seconds_model']} s  answers sha256 {ans_sha}")


if __name__ == "__main__":
    main()
