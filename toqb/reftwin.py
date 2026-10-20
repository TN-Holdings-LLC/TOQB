"""The reference twin of TOQB v0.2's prediction layer (W4 section 2): Qiskit Aer with the vendor's standard noise model.

    python -m toqb.reftwin JOB_DIR FETCH_DIR OUT_DIR [--shots T] [--threads N] [--first K] [--device GPU]

For every cell of a `toqb.s2rc_device` job folder (manifest.json and circuits.qpy, written by `assemble` before any
submission), it predicts P(1) of clbit 0 for every point and writes one prediction artifact per cell
(`toqb-pred/0`, the format `toqb.predscore` scores), plus `reftwin.json` with the SHA-256 of each.

- **Model.** `qiskit_aer.noise.NoiseModel.from_backend` on the fetched Target (the documented library path, with its
  defaults): depolarizing gate errors, thermal relaxation over each gate's duration, readout errors. The circuits are
  run as compiled (not scheduled), so idle time adds no relaxation, and there is no crosstalk. That is what this twin
  stands for: "the vendor's standard model", not a truth. Neither TOQB's nor PSF-Zero's authors wrote it.
- **Method.** Aer's statevector with T noisy shots per point (each shot one trajectory), the same method for every
  cell, so the twin's Monte Carlo error is binomial: the artifact records traj = T and `toqb.predscore` mixes it in.
  A density matrix would be exact, but Qiskit's level 2 routes the 10-qubit ring onto 14 qubits on heavy-hex, where a
  density matrix (4^14 entries, 4 GB) is impractical for hundreds of circuits.
- **Blind.** It reads the job's circuits and the fetched Target only (both checked by SHA-256 against the manifest);
  it never reads results. Run it before submission, and fix its outputs' hashes with the manifest's.
- **Seeds.** Point i of the job (its position in circuits.qpy) is run with seed_simulator = 20261020 + i.
- **Device.** CPU by default. `--device GPU` needs `qiskit-aer-gpu` and runs the same model and method on the GPU,
  with Aer's batched shots (`batched_shots_gpu`): the same distribution, another random stream (2026-10-20: on the
  pod's CPU quota of about 24 cores a point took 15.6 s on average, too slow for the device day).

Exit 0 written, 2 STOP (a hash differs, or an output exists: nothing is overwritten).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pickle
import sys
import time
import types

VERSION = "toqb.reftwin 0.1 (2026-10-20)"
SEED0 = 20261020


class Stop(Exception):
    pass


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def noise_model(target):
    """Aer's standard model from a Target alone (from_backend reads only these four attributes of a BackendV2)."""
    from qiskit_aer.noise import NoiseModel
    shim = types.SimpleNamespace(version=2, target=target, operation_names=list(target.operation_names), dt=target.dt)
    return NoiseModel.from_backend(shim)


def p1_clbit0(counts):
    total = sum(counts.values())
    one = sum(v for k, v in counts.items() if k.replace(" ", "")[-1] == "1")
    return one / total


def run(job_dir, fetch_dir, out_dir, shots=1024, threads=0, first=None, device="CPU"):
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    import qiskit_aer
    man_f, qpy_f = os.path.join(job_dir, "manifest.json"), os.path.join(job_dir, "circuits.qpy")
    tgt_f = os.path.join(fetch_dir, "target.pkl")
    man = json.load(open(man_f, encoding="utf-8"))
    if sha256_file(qpy_f) != man["qpy_sha256"]:
        raise Stop("circuits.qpy differs from the manifest's hash")
    if sha256_file(tgt_f) != man["fetch"]["target_sha256"]:
        raise Stop("target.pkl differs from the Target the manifest was built on")
    if os.path.exists(os.path.join(job_dir, "raw_counts.json")):
        print("note: raw_counts.json exists in the job folder; this twin does not read it, but its outputs are then "
              "not blind by time", file=sys.stderr)
    if os.path.exists(out_dir):
        raise Stop(f"{out_dir} exists: outputs are never overwritten")
    with open(tgt_f, "rb") as f:
        target = pickle.load(f)
    with open(qpy_f, "rb") as f:
        circs = qpy.load(f)
    if len(circs) != len(man["pubs"]):
        raise Stop("the QPY file and the manifest disagree on the number of circuits")
    t0 = time.perf_counter()
    nm = noise_model(target)
    t_nm = time.perf_counter() - t0
    opts = dict(method="statevector", noise_model=nm, max_parallel_threads=threads, device=device)
    if device == "GPU":
        opts["batched_shots_gpu"] = True
    sim = AerSimulator(**opts)
    idx = list(range(len(circs)))
    if first:
        # smoke runs only: per cell, the first ceil(first / 2) points of class +1 and the first floor(first / 2) of
        # class -1 (the test points are ordered by class, so "the first K" would be one class, which predscore refuses)
        lab = {c["cell"]: c["labels"] for c in man["cells"]}
        seen = {}
        idx = []
        for i, p in enumerate(man["pubs"]):
            y = lab[p["cell"]][p["point"]]
            k = (p["cell"], y)
            if seen.get(k, 0) < ((first + 1) // 2 if y > 0 else first // 2):
                seen[k] = seen.get(k, 0) + 1
                idx.append(i)
    p1 = {}
    t1 = time.perf_counter()
    for i in idx:
        res = sim.run(circs[i], shots=shots, seed_simulator=SEED0 + i).result()
        p1[i] = p1_clbit0(res.get_counts(0))
    t_run = time.perf_counter() - t1
    os.makedirs(out_dir)
    summary = dict(version=VERSION, written=now(), aer=qiskit_aer.__version__, shots=shots, threads=threads, device=device,
                   points=len(idx), noise_model_s=round(t_nm, 3), run_s=round(t_run, 3),
                   inputs=dict(manifest_sha256=sha256_file(man_f), qpy_sha256=man["qpy_sha256"],
                               target_sha256=man["fetch"]["target_sha256"]),
                   smoke=bool(first), cells={})
    for c in man["cells"]:
        pts = [(p["point"], i) for i, p in enumerate(man["pubs"]) if p["cell"] == c["cell"] and i in p1]
        pts.sort()
        pred = dict(
            format="toqb-pred/0", written=now(), fixed_at=now(), fixed_by_hash=False,
            producer=dict(name="toqb.reftwin", version=VERSION, aer=qiskit_aer.__version__,
                          script_sha256=sha256_file(os.path.abspath(__file__))),
            inputs=dict(run_record_sha256=c["run_sha256"], manifest_sha256=summary["inputs"]["manifest_sha256"],
                        qpy_sha256=man["qpy_sha256"], target_sha256=man["fetch"]["target_sha256"],
                        role="reference twin for this cell's circuits"),
            twin=dict(name="aer-statevector-trajectories", traj=shots,
                      model="NoiseModel.from_backend(Target) defaults: depolarizing gate error, thermal relaxation "
                            "over gate durations, readout error; unscheduled (no idle relaxation), no crosstalk",
                      mc_error="binomial: P(1) estimated from `traj` noisy shots"),
            compiler=dict(arm=c["arm"]), cell=dict(layers=c["layers"], seed=c["seed"], name=c["name"]), device=device,
            shots=man["shots"],
            points=[dict(i=pt, label=int(c["labels"][pt]), p1=float(p1[i])) for pt, i in pts],
            job={}, cost=dict(run_s_all_cells=round(t_run, 3), threads=threads),
            notes=["fixed_by_hash becomes true when this file's SHA-256 is recorded before submission"])
        if first:
            pred["notes"].append(f"smoke run: {first} points of each cell, both classes")
        f = os.path.join(out_dir, f"ref_cell{c['cell']}.json")
        data = json.dumps(pred, indent=1, sort_keys=True).encode("utf-8")
        with open(f, "wb") as fh:
            fh.write(data)
        summary["cells"][str(c["cell"])] = dict(name=c["name"], arm=c["arm"], points=len(pts),
                                               file=os.path.basename(f), sha256=hashlib.sha256(data).hexdigest())
    with open(os.path.join(out_dir, "reftwin.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
    print(f"{summary['written']} reference twin: {len(idx)} points x {shots} shots in {t_run:.1f} s "
          f"(noise model {t_nm:.1f} s); outputs in {out_dir}")
    for k, v in summary["cells"].items():
        print(f"  cell {k} {v['name']} {v['arm']}: {v['points']} points, sha256 {v['sha256']}")
    return summary


def main(argv):
    def opt(name, conv, default):
        if name in argv:
            i = argv.index(name)
            val = conv(argv[i + 1])
            del argv[i:i + 2]
            return val
        return default
    argv = list(argv)
    shots = opt("--shots", int, 1024)
    threads = opt("--threads", int, 0)
    first = opt("--first", int, None)
    device = opt("--device", str, "CPU")
    if device not in ("CPU", "GPU"):
        print("--device is CPU or GPU")
        return 1
    if len(argv) != 3:
        print(__doc__)
        return 1
    try:
        run(argv[0], argv[1], argv[2], shots=shots, threads=threads, first=first, device=device)
    except Stop as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
