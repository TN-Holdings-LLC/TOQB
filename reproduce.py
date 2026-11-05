"""Re-score the committed device results from their committed raw counts, without IBM, and compare with the
committed scores.json files. Every scorer is run unchanged on a copy (the committed files are not touched).

usage (from the TOQB root, with psf-os installed or on PYTHONPATH):
    python reproduce.py [--psf-os PATH_TO_PSF_OS_CHECKOUT] [NAME ...]

Prints one line per result: SAME (every number equal to 1e-9), DIFFERENT (the first differing key), or FAILED.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))

# name: (result folder, folders to copy, scorer command with {T} = the copy's root, scores file in the copy)
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


def copy_result(src, parts, dst):
    for p in parts:
        s = os.path.join(ROOT, src, p)
        if os.path.isdir(s):
            shutil.copytree(s, os.path.join(dst, p), ignore=shutil.ignore_patterns("scores.json", "raw_counts.json"))
        else:
            shutil.copy(s, os.path.join(dst, p))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--psf-os", default=None, help="a psf-os checkout to put first on PYTHONPATH")
    ap.add_argument("names", nargs="*")
    a = ap.parse_args()
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(p for p in (a.psf_os, ROOT, env.get("PYTHONPATH")) if p)
    names = a.names or list(RESULTS)
    bad = 0
    for name in names:
        src, parts, cmd, scores = RESULTS[name]
        with tempfile.TemporaryDirectory() as t:
            copy_result(src, parts, t)
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
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
