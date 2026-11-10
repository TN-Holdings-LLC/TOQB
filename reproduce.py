"""Re-score the committed device results from their committed raw counts, without IBM, and compare with the
committed scores.json files. Every scorer is run unchanged on a copy (the committed files are not touched).

usage (from the TOQB root, with psf-os installed or on PYTHONPATH):
    python reproduce.py [--psf-os PATH_TO_PSF_OS_CHECKOUT] [NAME ...]

Prints one line per result: SAME (every number equal to 1e-9), DIFFERENT (the first differing key), or FAILED.

--gate-hash: also rebuild the circuits of the run2d results (practice and daily) from their committed device record and
user circuits with the psf-os on the path, and compare psf_os.gatehash of every compiled circuit (user, floor, mirror,
sentinel; the job's circuits.qpy) with the committed ones: GATES SAME / GATES DIFFERENT. The gate hash does not depend
on Qiskit's QPY format (QPY bytes do).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))

# name: (result folder, folders to copy, scorer command with {T} = the copy's root, scores file in the copy[, rev])
# rev (optional): the commit whose gpu/ scorer made the committed scores.json, where the scorer has gained keys since
# (it is taken from `git archive rev gpu` into the temporary folder; needs the git history).
RESULTS = {
    "p6-fez-2026-11-04": ("results/p6-device-2026-11-04", ["V"], ["gpu/p6_score.py", "{T}"], "scores.json"),
    "p6-marrakesh-2026-11-04": ("results/p6-marrakesh-2026-11-04", ["V"], ["gpu/p6_score.py", "{T}"], "scores.json"),
    "os2d-fez-2026-11-04": ("results/os2d-2026-11-04", ["V"],
                            ["gpu/os2d_score.py", "{T}/V/job", "{T}/V/runs",
                             "results/p6-answers-2026-11-04/answers_cpu.json", "{T}/scores.json"], "scores.json"),
    "corr-fez-2026-11-04": ("results/corr-2026-11-04", ["V"], ["gpu/corr_score.py", "{T}"], "scores.json"),
    "corr-marrakesh-2026-11-04": ("results/corr-marrakesh-2026-11-04", ["V"], ["gpu/corr_score.py", "{T}"],
                                  "scores.json"),
    "practice-marrakesh-2026-11-04": ("results/practice-2026-11-04", ["run", "circuits"],
                                      ["gpu/practice_score.py", "{T}/run", "{T}/circuits/answers.json"],
                                      "run/scores.json"),
    "practice-fez-2026-11-04": ("results/practice-fez-2026-11-04", ["run", "circuits"],
                                ["gpu/practice_score.py", "{T}/run", "{T}/circuits/answers.json"], "run/scores.json"),
    "daily-2026-11-05-marrakesh": ("results/daily/2026-11-05", ["ibm_marrakesh", "answers.json"],
                                   ["gpu/daily_score.py", "{T}/ibm_marrakesh/run", "{T}/answers.json"],
                                   "ibm_marrakesh/run/scores.json"),
    "daily-2026-11-05-fez": ("results/daily/2026-11-05", ["ibm_fez", "answers.json"],
                             ["gpu/daily_score.py", "{T}/ibm_fez/run", "{T}/answers.json"], "ibm_fez/run/scores.json"),
    # added 2026-11-08 for paper 7 (the 11-06 run is FX-A alone, scored with its answers_by_tag.json)
    "daily-2026-11-06-marrakesh": ("results/daily/2026-11-06", ["ibm_marrakesh"],
                                   ["gpu/daily_score.py", "{T}/ibm_marrakesh/run", "{T}/ibm_marrakesh/answers_by_tag.json"],
                                   "ibm_marrakesh/run/scores.json"),
    "daily-2026-11-07-fez": ("results/daily/2026-11-07", ["ibm_fez", "answers.json"],
                             ["gpu/daily_score.py", "{T}/ibm_fez/run", "{T}/answers.json"], "ibm_fez/run/scores.json"),
    "du51-kingston-2026-11-07": ("results/du51-2026-11-07", ["ibm_kingston", "answers"],
                                 ["gpu/du51_score.py", "{T}/ibm_kingston/run", "{T}/answers/answers.json"],
                                 "ibm_kingston/run/scores.json"),
    "du71-kingston-2026-11-07": ("results/du71-2026-11-07", ["ibm_kingston", "answers"],
                                 ["gpu/du51_score.py", "{T}/ibm_kingston/run", "{T}/answers/answers.json"],
                                 "ibm_kingston/run/scores.json"),
    # added 2026-11-10 at the workplace for paper 8 (handover 11-09 item 3); same rule: the declared scorer, unchanged
    "physA-4x4x3-fez-2026-11-07": ("results/os3d-physA-2026-11-07", ["j1_4x4x3", "answers"],
                                   ["gpu/os3d_v31_score.py", "{T}/j1_4x4x3", "{T}/answers/answers_4x4x3.json", "top"],
                                   "j1_4x4x3/scores.json"),
    "physA-4x2x2-fez-2026-11-07": ("results/os3d-physA-2026-11-07", ["j2_4x2x2", "answers"],
                                   ["gpu/os3d_v31_score.py", "{T}/j2_4x2x2", "{T}/answers/answers_4x2x2.json", "top"],
                                   "j2_4x2x2/scores.json"),
    "heisB-fez-2026-11-08": ("results/os3d-heisB-2026-11-08", ["fez", "answers"],
                             ["gpu/heis3d_score.py", "{T}/fez", "{T}/answers/heis_answers_fez.json"], "fez/scores.json", "9eaf26c"),
    "heisE-marrakesh-2026-11-08": ("results/os3d-heisE-2026-11-08", ["marrakesh", "answers"],
                                   ["gpu/heis3d_score.py", "{T}/marrakesh", "{T}/answers/heis_answers_E_marrakesh.json"],
                                   "marrakesh/scores.json", "bc38d2c"),
    "heisE-kingston-2026-11-08": ("results/os3d-heisE-kingston-2026-11-08", ["kingston", "answers"],
                                  ["gpu/heis3d_score.py", "{T}/kingston", "{T}/answers/heis_answers_Ek.json"],
                                  "kingston/scores.json", "bc38d2c"),
    "du91-marrakesh-2026-11-09": ("results/du91-2026-11-09", ["ibm_marrakesh", "answers"],
                                  ["gpu/du51_score.py", "{T}/ibm_marrakesh/run", "{T}/answers/du91_answers_marrakesh.json"],
                                  "ibm_marrakesh/run/scores.json"),
    "schw-marrakesh-2026-11-09": ("results/schw-2026-11-09", ["ibm_marrakesh", "answers"],
                                  ["gpu/schw_score.py", "{T}/ibm_marrakesh", "{T}/answers/schw_answers_marrakesh.json"],
                                  "ibm_marrakesh/scores.json"),
    "lc3d-marrakesh-2026-11-09": ("results/lc3d-2026-11-09", ["ibm_marrakesh", "answers"],
                                  ["gpu/lc3d_score.py", "{T}/ibm_marrakesh", "{T}/answers/lc_answers_marrakesh.json"],
                                  "ibm_marrakesh/scores.json"),
    # added 2026-11-10 for paper 8: the N = 91 second run (ruler in every job) and the Ising line against fold
    "du91r-fez-2026-11-10": ("results/night-2026-11-10/du91r", ["ibm_fez", "answers"],
                             ["gpu/du91r_score.py", "{T}/ibm_fez", "{T}/answers/du91r_fez.json"],
                             "ibm_fez/scores.json"),
    "isingL-fez-2026-11-10": ("results/night-2026-11-10/isingL", ["ibm_fez", "answers"],
                              ["gpu/isingL_score.py", "{T}/ibm_fez", "{T}/answers/isingL_fez.json"],
                              "ibm_fez/scores.json"),
}


def first_difference(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                return f"{path}/{k} missing on one side"
            d = first_difference(a[k], b[k], f"{path}/{k}")
            if d:
                return d
        return None
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return f"{path} length {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_difference(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return None if abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b)) else f"{path}: {a} != {b}"
    return None if a == b else f"{path}: {a!r} != {b!r}"


# run2d results: (run folder, device record folder, user circuits folder)
REBUILD = {
    "practice-marrakesh-2026-11-04": ("results/practice-2026-11-04/run", "results/practice-2026-11-04/dev",
                                      "results/practice-2026-11-04/circuits"),
    "practice-fez-2026-11-04": ("results/practice-fez-2026-11-04/run", "results/practice-fez-2026-11-04/dev",
                                "results/practice-fez-2026-11-04/circuits"),
    "daily-2026-11-05-marrakesh": ("results/daily/2026-11-05/ibm_marrakesh/run",
                                   "results/daily/2026-11-05/ibm_marrakesh/dev", "results/daily/2026-11-05/circuits"),
    "daily-2026-11-05-fez": ("results/daily/2026-11-05/ibm_fez/run", "results/daily/2026-11-05/ibm_fez/dev",
                             "results/daily/2026-11-05/circuits"),
}


def gate_check(name):
    """Rebuild one run2d result and compare gate hashes; (ok, message)."""
    from psf_os import device as Dv
    from psf_os import gatehash as G
    from psf_os import user2d as U
    run, dev_dir, circ = (os.path.join(ROOT, p) for p in REBUILD[name])
    rep = json.load(open(os.path.join(run, "report.json")))
    man = json.load(open(os.path.join(run, "job", "manifest.json")))
    items = [(t, U.load(os.path.join(circ, f"{t}.qpy"))) for t in rep["tags"]]
    with tempfile.TemporaryDirectory() as t:
        U.build_batch(Dv.Device.load(dev_dir), items, t, shots=man["shots"], max_seconds=10 ** 6)
        old = G.qpy_hash(os.path.join(run, "job", "circuits.qpy"))
        new = G.qpy_hash(os.path.join(t, "job", "circuits.qpy"))
        per = sorted(f for f in os.listdir(os.path.join(run, "runs")) if f.endswith(".qpy"))
        bad = [f for f in per if G.qpy_hash(os.path.join(run, "runs", f)) != G.qpy_hash(os.path.join(t, "runs", f))]
    ok = old == new and not bad
    return ok, (f"GATES SAME ({old['circuits']} circuits, {old['gate_sha256'][:12]})" if ok else
                f"GATES DIFFERENT (job {old['gate_sha256'][:12]} vs {new['gate_sha256'][:12]}; records {bad})")


def _ignore(folder, names):
    """Leave out the committed scores, and raw_counts.json where the committed raw_counts.json.gz is beside it (older
    records commit the .gz only; the plain file there is a local, untracked copy). Records from 2026-11-06 on commit
    raw_counts.json itself, which is then the input."""
    out = {"scores.json"} & set(names)
    if "raw_counts.json.gz" in names:
        out.add("raw_counts.json")
    return out


def copy_result(src, parts, dst):
    for p in parts:
        s = os.path.join(ROOT, src, p)
        if os.path.isdir(s):
            shutil.copytree(s, os.path.join(dst, p), ignore=_ignore)
        else:
            shutil.copy(s, os.path.join(dst, p))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--psf-os", default=None, help="a psf-os checkout to put first on PYTHONPATH")
    ap.add_argument("--gate-hash", action="store_true", help="also rebuild the run2d results' circuits and compare gates")
    ap.add_argument("names", nargs="*")
    a = ap.parse_args()
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(p for p in (a.psf_os, ROOT, env.get("PYTHONPATH")) if p)
    names = a.names or list(RESULTS)
    bad = 0
    for name in names:
        src, parts, cmd, scores, *rev = RESULTS[name]
        with tempfile.TemporaryDirectory() as t:
            copy_result(src, parts, t)
            if rev:  # the scorer as it was when the committed scores were made
                arc = subprocess.run(["git", "archive", rev[0], "gpu"], cwd=ROOT, capture_output=True, check=True)
                subprocess.run(["tar", "-x", "-C", t], input=arc.stdout, check=True)
                os.rename(os.path.join(t, "gpu"), os.path.join(t, "_gpu_at_rev"))
                cmd = [os.path.join(t, "_gpu_at_rev", cmd[0][len("gpu/"):])] + cmd[1:]
            run = subprocess.run([sys.executable] + [c.replace("{T}", t) for c in cmd], cwd=ROOT, env=env,
                                 capture_output=True, text=True)
            if run.returncode != 0:
                print(f"{name:32} FAILED: {run.stderr.strip().splitlines()[-1] if run.stderr.strip() else run.returncode}")
                bad += 1
                continue
            new = json.load(open(os.path.join(t, scores)))
            old = json.load(open(os.path.join(ROOT, src, scores)))
            d = first_difference(json.loads(json.dumps(old)), json.loads(json.dumps(new)))
            print(f"{name:32} " + ("SAME" if d is None else f"DIFFERENT at {d}"))
            bad += d is not None
    print(f"{len(names) - bad} of {len(names)} reproduced")
    if a.gate_hash:
        if a.psf_os:
            sys.path.insert(0, a.psf_os)
        gbad = 0
        gnames = [n for n in names if n in REBUILD]
        for name in gnames:
            try:
                ok, msg = gate_check(name)
            except Exception as e:  # noqa: BLE001
                ok, msg = False, f"FAILED: {e}"
            print(f"{name:32} {msg}")
            gbad += not ok
        print(f"{len(gnames) - gbad} of {len(gnames)} rebuilt with the same gates")
        bad += gbad
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
