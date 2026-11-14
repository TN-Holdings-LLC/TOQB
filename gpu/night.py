"""From a declaration to a committed result in two commands (home, 2026-11-13; OS item 5).

The owner's steps stay as they are (push with VPN on; fetch, submit and collect with VPN off; never mixed). This tool
does everything between them, from a spec file written with the declaration:

  prepare  fetch folder or zip -> device choice by the declared order (fewest pending, then the tie order), all jobs
           built on the first device where every job builds -> per job: circuits_sha256 against the checked try-builds
           listed in the spec (equal: the PASS carries over; otherwise the spec's checks run now, and any FAIL stops)
           -> one zip of the job folders, the answers' hashes, and the owner's submit / collect command (VPN off).
  record   the result zip -> job files compared byte for byte with what was built -> raw counts copied in -> the
           spec's scorers -> results/<name>/ (device folders, released answers, fetch record, README skeleton with the
           push and fetch times, job ids and the scorers' lines) -> reproduce.py entries -> reproduce run (must be SAME).
           Writing the prediction comparison stays a human / Claude step (the README marks the place).

Spec (JSON), placeholders {DEV} (device record folder), {OUT} (job folder), {ANS} (answers file), {ANS_TWIN}:
  {"name": "twin-2026-11-13", "declaration": "prereg/twin_2026-11-13.md", "tie_order": ["ibm_marrakesh", ...],
   "jobs": [{"key": "xx", "build": ["gpu/ffxx91.py", "{DEV}", "{OUT}", "{ANS}", ...],
             "checks": [["gpu/twin_check.py", "{OUT}", "{ANS_TWIN}"], ...],
             "checked": {"<circuits_sha256>": "<where the passing check is recorded>"},
             "score": ["gpu/twin_score.py", "{OUT}", "{ANS}", "{ANS_TWIN}"], "scores_file": "twin_scores.json",
             "answers": ["{ANS}", "{ANS_TWIN}"]}, ...]}

usage:
  PYTHONPATH=<psf-os>:<notebook>:<notebook>/gpu python gpu/night.py prepare SPEC FETCH WORK [--device ibm_fez]
  PYTHONPATH=... python gpu/night.py record SPEC WORK RESULT_ZIP --pushed "<reflog line of the push>"
"""
import argparse
import datetime as dt
import filecmp
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMIT_BYTES = 50 * 1024 * 1024  # GitHub's recommended size; bigger files are gzipped before committing


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def subst(args, **kw):
    return [a.format(**kw) for a in args]


def run(cmd, log):
    """Run a notebook script with the current interpreter; its output goes to `log`; returns the exit code."""
    with open(log, "a") as f:
        f.write("$ " + " ".join(cmd) + "\n")
        f.flush()
        p = subprocess.run([sys.executable, "-u"] + cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
    return p.returncode


def unpack(src, dest):
    """A fetch or result folder, or a zip of one (names written by Windows or Linux), into dest; returns its root."""
    if os.path.isdir(src):
        return src
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(src) as z:
        for i in z.infolist():
            n = i.filename.replace("\\", "/")
            if not (i.flag_bits & 0x800):
                try:
                    n = n.encode("cp437").decode("utf-8")
                except UnicodeError:
                    pass
            if ".." in n.split("/") or n.startswith("/"):
                raise SystemExit(f"STOP: unsafe name in the zip: {n}")
            if n.endswith("/"):
                continue
            os.makedirs(os.path.dirname(os.path.join(dest, n)), exist_ok=True)
            with open(os.path.join(dest, n), "wb") as f:
                f.write(z.read(i))
    tops = {p.split("/")[0] for p in os.listdir(dest)}
    return os.path.join(dest, sorted(tops)[0]) if len(tops) == 1 and os.path.isdir(os.path.join(dest, sorted(tops)[0])) else dest


def device_order(fetch, tie):
    q = json.load(open(os.path.join(fetch, "queue.json")))
    pend = q["pending"]
    have = [d for d in tie if os.path.exists(os.path.join(fetch, d, "dev", "device.json"))]
    return sorted(have, key=lambda d: (pend.get(d, 10 ** 9), tie.index(d))), q


def prepare(a):
    spec = json.load(open(a.spec))
    os.makedirs(a.work, exist_ok=True)
    fetch = unpack(a.fetch, os.path.join(a.work, "fetch_in"))
    order, queue = device_order(fetch, spec["tie_order"])
    if a.device:  # a companion job that must run on the device the main jobs of the night chose
        if a.device not in order:
            raise SystemExit(f"STOP: {a.device} is not in this fetch")
        order = [a.device]
    log = os.path.join(a.work, "prepare.log")
    print(f"queue read {queue['read']}; pending {queue['pending']}; order {order}")
    chosen, built = None, {}
    for d in order:
        built = {}
        for job in spec["jobs"]:
            out = os.path.join(a.work, d, job["key"])
            ans = os.path.join(a.work, d, job["key"] + "_ans.json")
            kw = dict(DEV=os.path.join(fetch, d, "dev"), OUT=out, ANS=ans, ANS_TWIN=ans[:-5] + "_twin.json")
            if a.resume and os.path.exists(os.path.join(out, "job", "manifest.json")):
                built[job["key"]] = kw  # built earlier in this work folder (a prepare that was interrupted)
                continue
            if run(subst(job["build"], **kw), log) != 0 or not os.path.exists(os.path.join(out, "job", "manifest.json")):
                print(f"{d}: job {job['key']} does not build (see {log}); next device")
                break
            built[job["key"]] = kw
        else:
            chosen = d
            break
    if chosen is None:
        raise SystemExit("STOP: no device builds every job")
    rec = dict(name=spec["name"], device=chosen, queue=queue, fetch=os.path.abspath(fetch), jobs={})
    for job in spec["jobs"]:
        kw = built[job["key"]]
        man = json.load(open(os.path.join(kw["OUT"], "job", "manifest.json")))
        h = man["circuits_sha256"]
        extra = json.load(open(a.checked)) if a.checked else {}
        carried = spec.get("checked", {}).get(h) or job.get("checked", {}).get(h) or extra.get(h)
        if carried:
            status = f"PASS carried over from {carried}"
        elif not job.get("checks"):
            status = "no pre-run check declared (measurement record)"
        else:
            status = "checks run now"
            for c in job.get("checks", []):
                if run(subst(c, **kw), log) != 0:
                    raise SystemExit(f"STOP: check failed for {job['key']}: {c} (see {log})")
                tail = open(log).read().strip().splitlines()[-1]
                if "ALL PASS" not in tail:
                    raise SystemExit(f"STOP: check did not print ALL PASS for {job['key']}: {tail}")
            status += ": ALL PASS"
        answers = {os.path.basename(p.format(**kw)): sha(p.format(**kw)) for p in job.get("answers", [])}
        rec["jobs"][job["key"]] = dict(out=kw["OUT"], circuits_sha256=h, circuits=len(man["pubs"]),
                                       seconds=man["qpu_seconds_model"], check=status, answers_sha256=answers)
        print(f"{job['key']}: {len(man['pubs'])} circuits, {man['qpu_seconds_model']} s, circuits_sha256 {h[:12]}..., "
              f"{status}")
        for n, s in answers.items():
            print(f"  {n} sha256 {s}")
    # one zip with each job's circuits and manifest, in folders <name>_<key>_job/job
    zname = os.path.join(a.work, f"job_{spec['name']}_{chosen.replace('ibm_', '')}.zip")
    with zipfile.ZipFile(zname, "w", zipfile.ZIP_DEFLATED) as z:
        for key, j in rec["jobs"].items():
            for f in ("circuits.qpy", "manifest.json"):
                z.write(os.path.join(j["out"], "job", f), f"{spec['name']}_{key}_job/job/{f}")
    rec["zip"] = zname
    json.dump(rec, open(os.path.join(a.work, "prepare.json"), "w"), indent=1)
    dirs = [f"/home/psf/{spec['name']}_{k}_job/job" for k in rec["jobs"]]
    print(f"\njob zip: {zname}  (total {sum(j['seconds'] for j in rec['jobs'].values()):.1f} s by the model)")
    print("owner, VPN OFF (after the zip is in psf_zero_project):")
    print("cd ~ && python -m zipfile -e /mnt/c/Users/Administrator/Desktop/psf_zero_project/" + os.path.basename(zname)
          + ' . && cd ~/psf-os && PYTHONPATH=~/psf-os python -c "\nfrom psf_os import ibm\ns = ibm.service()\n'
          + "".join(f"print('job', ibm.submit(s, '{d}'))\n" for d in dirs)
          + "".join(f"print('status', ibm.collect(s, '{d}', wait_s=3600))\n" for d in dirs)
          + '" && cd ~ && python -m zipfile -c /mnt/c/Users/Administrator/Desktop/psf_zero_project/res_'
          + os.path.basename(zname)[4:] + " " + " ".join(f"{spec['name']}_{k}_job" for k in rec["jobs"]) + " && echo ZIP_OK")


def gz_big(folder):
    for base, _, files in os.walk(folder):
        for f in files:
            p = os.path.join(base, f)
            if os.path.getsize(p) > LIMIT_BYTES:
                with open(p, "rb") as s, gzip.open(p + ".gz", "wb", compresslevel=9) as d:
                    shutil.copyfileobj(s, d)
                os.remove(p)


def record(a):
    spec = json.load(open(a.spec))
    prep = json.load(open(os.path.join(a.work, "prepare.json")))
    dev = prep["device"]
    res = unpack(a.result, os.path.join(a.work, "result_in"))
    m = re.search(r"@\{(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d [+-]\d{4})\}", a.pushed or "")
    pushed = dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S %z") if m else None
    read = dt.datetime.fromisoformat(prep["queue"]["read"])
    if pushed is None or pushed >= read:
        raise SystemExit(f"STOP: the push ({pushed}) is not before the queue read ({read}); not recorded")
    dest = os.path.join(ROOT, "results", spec["name"])
    if os.path.exists(dest):
        raise SystemExit(f"STOP: {dest} exists")
    lines, ids = [], {}
    for job in spec["jobs"]:
        key = job["key"]
        j = prep["jobs"][key]
        got = os.path.join(res, f"{spec['name']}_{key}_job", "job")
        if os.path.basename(os.path.normpath(res)) == f"{spec['name']}_{key}_job":  # a zip holding this one job folder
            got = os.path.join(res, "job")
        for f in ("circuits.qpy", "manifest.json"):
            if not filecmp.cmp(os.path.join(got, f), os.path.join(j["out"], "job", f), shallow=False):
                raise SystemExit(f"STOP: {key}/{f} differs from what was built")
        sub = json.load(open(os.path.join(got, "submission.json")))
        if sub.get("backend") != dev:
            raise SystemExit(f"STOP: {key} ran on {sub.get('backend')}, built for {dev}")
        for f in ("raw_counts.json", "submission.json"):
            shutil.copy(os.path.join(got, f), os.path.join(j["out"], "job", f))
        kw = dict(OUT=j["out"], ANS=j["out"] + "_ans.json", ANS_TWIN=j["out"] + "_ans_twin.json")
        log = os.path.join(a.work, f"record_{key}.log")
        if os.path.exists(log):
            os.remove(log)
        if run(subst(job["score"], **kw), log) != 0:
            raise SystemExit(f"STOP: scorer failed for {key} (see {log})")
        out_lines = open(log).read().strip().splitlines()
        lines.append((key, [l for l in out_lines if not l.startswith("$")][-12:]))
        ids[key] = sub.get("job_id")
        # copy into results/<name>/<device>_<key>/
        d = os.path.join(dest, f"{dev}_{key}")
        os.makedirs(d)
        for f in ("build.json", "report.json", job["scores_file"]):
            shutil.copy(os.path.join(j["out"], f), d)
        for f in ("job", "runs"):
            shutil.copytree(os.path.join(j["out"], f), os.path.join(d, f))
        for extra in ("check.json", "twin_check.json"):
            if os.path.exists(os.path.join(j["out"], extra)):
                shutil.copy(os.path.join(j["out"], extra), d)
        os.makedirs(os.path.join(dest, "answers"), exist_ok=True)
        for p in job.get("answers", []):
            shutil.copy(p.format(**kw), os.path.join(dest, "answers", f"{key}_" + os.path.basename(p.format(**kw))))
        # The scorer is called with {ANS} even when the spec releases no answers (a measurement record writes a stub):
        # keep that file too, so answers/ is never empty and reproduce.py runs from a fresh clone (git keeps no empty
        # folder; the 2026-11-13 floor record lacked it).
        ans = os.path.join(dest, "answers", f"{key}_" + os.path.basename(kw["ANS"]))
        if os.path.exists(kw["ANS"]) and not os.path.exists(ans):
            shutil.copy(kw["ANS"], ans)
    shutil.copytree(prep["fetch"], os.path.join(dest, "fetch_in"))
    gz_big(dest)
    # README skeleton
    q = prep["queue"]
    with open(os.path.join(dest, "README.md"), "w") as f:
        f.write(f"# {spec['name']} ({dev}) ({spec['declaration']})\n\n")
        f.write(f"- Declaration pushed {pushed.isoformat()} (reflog \"update by push\"); queue read {q['read']} "
                f"(pending {q['pending']}).\n")
        for key, j in prep["jobs"].items():
            f.write(f"- Job {key}: {j['circuits']} circuits, {j['seconds']} s by the model, circuits_sha256 "
                    f"{j['circuits_sha256'][:12]}..., {j['check']}; job id {ids[key]}; job files returned byte-identical.\n")
            for n, s in j["answers_sha256"].items():
                f.write(f"  - {n} sha256 {s[:12]}... (released in answers/)\n")
        f.write("- Files over 50 MB are gzipped (`gunzip` restores them).\n\n## Scorer output\n\n")
        for key, ls in lines:
            f.write(f"### {key}\n\n```\n" + "\n".join(ls) + "\n```\n\n")
        f.write("## Prediction (written before the data)\n\nTO FILL: compare with the declaration, line by line.\n\n"
                "## Reproduce\n\n" + ", ".join(f"`python reproduce.py {spec['name']}-{k}`" for k in prep["jobs"]) + ".\n")
    # reproduce entries
    rp = os.path.join(ROOT, "reproduce.py")
    s = open(rp).read()
    add = ""
    for job in spec["jobs"]:
        key = job["key"]
        d = f"{dev}_{key}"
        score = [x.replace("{OUT}", "{T}/" + d).replace("{ANS}", "{T}/answers/" + key + "_" + key + "_ans.json")
                 .replace("{ANS_TWIN}", "{T}/answers/" + key + "_" + key + "_ans_twin.json") for x in job["score"]]
        add += (f'    "{spec["name"]}-{key}": ("results/{spec["name"]}", ["{d}", "answers"],\n'
                f'        {json.dumps(score)},\n        "{d}/{job["scores_file"]}"),\n')
    i = s.index("\n}\n", s.index("RESULTS = {"))
    open(rp, "w").write(s[:i + 1] + add + s[i + 1:])
    names = [f"{spec['name']}-{k}" for k in prep["jobs"]]
    p = subprocess.run([sys.executable, "reproduce.py"] + (["--psf-os", a.psf_os] if a.psf_os else []) + names,
                       cwd=ROOT, capture_output=True, text=True)
    print(p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr[-500:])
    print(f"recorded in {dest}; README needs the prediction comparison")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("spec")
    p.add_argument("fetch")
    p.add_argument("work")
    p.add_argument("--device", default=None, help="build only on this device (companion job of the night)")
    p.add_argument("--resume", action="store_true", help="reuse jobs already built in WORK (after an interrupted prepare)")
    p.add_argument("--checked", default=None, help="JSON {circuits_sha256: where its passing check is recorded}")
    r = sub.add_parser("record")
    r.add_argument("spec")
    r.add_argument("work")
    r.add_argument("result")
    r.add_argument("--pushed", required=True, help="the reflog line of the declaration's push")
    r.add_argument("--psf-os", default=None)
    a = ap.parse_args()
    (prepare if a.cmd == "prepare" else record)(a)


if __name__ == "__main__":
    main()
