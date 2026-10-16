"""Runs the TOQB loop budget run (prereg/2026-10-16-loop-n6-budget.md) on any OS (Windows PowerShell included).

    python prereg/loop-n6-budget-2026-10-16/run_budget.py --psf <PSF-Zero files> --day <folder for the zip>
        [--par N] [--first 6001] [--last 7000] [--out results/loop-n6-budget-2026-10-16]

Run from the TOQB root. Checks every fixed hash and the versions, refuses an existing output folder, runs every
(seed, arm) as its own process, N at a time, then the classical reference, the score and a zip. No network.
"""
import argparse
import concurrent.futures as cf
import datetime
import hashlib
import os
import subprocess
import sys
import zipfile

PREREG = "prereg/2026-10-16-loop-n6-budget.md"
PREREG_SHA = "0e35edcf983da4887712716152e384e07170894c46da107528f36ac90b5130ea"
P = "prereg/loop-n6-budget-2026-10-16"
PLANS_SHA = "71a7f6996324891feaba549a7d7c1700da4a47a4c43a0ba006469ee473d487a7"
CODE_SHA = "dd3c443efade3aa37c1edd3b5e9f7d29975e0de8f890b753785fa2fc2b851470"
PSF_FILES = {
    "patches/psf_compile_c61_2026-10-15/psf_compile.py":
        "254cfabc5924118a5c54e159fa2284202d21b87894202f447333de07f06b3728",
    "patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py":
        "625f9431344cd0fad6715ea44dc347044b0c64507c008f69202145d03b14a8ce",
}
ARMS = ("psfai:template", "qiskit:2:target:template")
SINGLE = {k: "1" for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "RAYON_NUM_THREADS",
                           "QISKIT_NUM_PROCS", "NUMEXPR_NUM_THREADS")}
SINGLE["QISKIT_PARALLEL"] = "FALSE"


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def sums_ok(listing, base):
    for line in open(listing, encoding="utf-8"):
        if line.strip():
            h, name = line.split(None, 1)
            if sha(os.path.join(base, name.strip())) != h:
                return name.strip()
    return None


def now():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("Europe/Zurich")).strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:  # noqa: BLE001 - Windows without tzdata: central European summer time, fixed
        tz = datetime.timezone(datetime.timedelta(hours=2), "CEST")
        return datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z") + " (fixed +02:00)"


def stop(msg):
    print("STOP:", msg)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--psf", required=True)
    ap.add_argument("--day", required=True)
    ap.add_argument("--par", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--first", type=int, default=6001)
    ap.add_argument("--last", type=int, default=7000)
    ap.add_argument("--out", default="results/loop-n6-budget-2026-10-16")
    a = ap.parse_args()
    root = os.getcwd()
    psf = os.path.abspath(a.psf)
    if sha(PREREG) != PREREG_SHA:
        stop("pre-registration changed")
    if sha(os.path.join(P, "SHA256SUMS")) != PLANS_SHA:
        stop("plan list changed")
    if sha(os.path.join(P, "CODE_SHA256SUMS")) != CODE_SHA:
        stop("code list changed")
    bad = sums_ok(os.path.join(P, "SHA256SUMS"), P)
    if bad:
        stop(f"plan {bad} changed")
    bad = sums_ok(os.path.join(P, "CODE_SHA256SUMS"), root)
    if bad:
        stop(f"TOQB file {bad} differs from the pre-registered")
    for rel, h in PSF_FILES.items():
        if sha(os.path.join(psf, rel)) != h:
            stop(f"PSF-Zero file {rel} differs from the pre-registered")
    import qiskit
    import qiskit_aer
    if (qiskit.__version__, qiskit_aer.__version__) != ("2.5.2", "0.17.2"):
        stop(f"needs Qiskit 2.5.2 and Aer 0.17.2, found {qiskit.__version__} and {qiskit_aer.__version__}")
    if os.path.exists(a.out):
        stop(f"{a.out} exists; a run never overwrites another")
    seeds = list(range(a.first, a.last + 1))
    os.makedirs(os.path.join(a.out, "logs"))
    for s in seeds:
        os.makedirs(os.path.join(a.out, f"seed{s}"))
        with open(os.path.join(P, f"plan_s{s}.json"), "rb") as src, \
                open(os.path.join(a.out, f"seed{s}", "plan.json"), "wb") as dst:
            dst.write(src.read())
    times = os.path.join(a.out, "times.txt")
    with open(times, "w", encoding="utf-8") as f:
        f.write(f"machine: {sys.platform}, {os.cpu_count()} CPUs, {a.par} processes\n")
        f.write(f"prereg {PREREG_SHA}\nstart {now()}\n")
    print(open(times, encoding="utf-8").read(), end="", flush=True)
    env = dict(os.environ, **SINGLE, PSF_ZERO_REPO=psf, PYTHONWARNINGS="ignore",
               PSF_COMPILE_FILE=os.path.join(psf, "patches", "psf_compile_c61_2026-10-15", "psf_compile.py"),
               PSF_AI_FILE=os.path.join(psf, "patches", "psf_ai_compile_a22_2026-10-15", "psf_ai_compile.py"))

    def one(job):
        s, arm = job
        log = os.path.join(a.out, "logs", f"seed{s}-{arm.replace(':', '_')}.log")
        with open(log, "w", encoding="utf-8") as lf:
            subprocess.run([sys.executable, "-m", "toqb.task_loop", "arm", os.path.join(P, f"plan_s{s}.json"),
                            os.path.join(a.out, f"seed{s}"), arm], env=env, cwd=root, stdout=lf, stderr=lf,
                           check=False)
        return s, arm

    jobs = [(s, arm) for s in seeds for arm in ARMS]
    done = 0
    with cf.ThreadPoolExecutor(a.par) as pool:
        for _ in pool.map(one, jobs):
            done += 1
            if done % 200 == 0 or done == len(jobs):
                print(f"{done // 2} of {len(seeds)} seeds done {now()}", flush=True)
    subprocess.run([sys.executable, "-m", "toqb.task_loop", "classical", os.path.join(P, f"plan_s{seeds[0]}.json"),
                    os.path.join(a.out, f"seed{seeds[0]}")], env=env, cwd=root, capture_output=True, check=False)
    with open(times, "a", encoding="utf-8") as f:
        f.write(f"end {now()}\n")
    with open(os.path.join(a.out, "logs", "score.log"), "w", encoding="utf-8") as lf:
        subprocess.run([sys.executable, "-m", "toqb.score_loop_preg4", a.out, "--seeds", f"{a.first}-{a.last}"],
                       env=env, cwd=root, stdout=lf, stderr=lf, check=False)
    md = open(os.path.join(a.out, "score.md"), encoding="utf-8").read()
    print(md.split("## Reported")[0])
    os.makedirs(a.day, exist_ok=True)
    z = os.path.join(a.day, "loop_n6_budget_results.zip")
    if os.path.exists(z):
        stop(f"{z} exists; the results stay in {a.out}")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for dp, _, fs in os.walk(a.out):
            for fn in fs:
                p = os.path.join(dp, fn)
                zf.write(p, os.path.relpath(p, os.path.dirname(os.path.abspath(a.out))))
    print("== DONE:", z)


if __name__ == "__main__":
    main()
