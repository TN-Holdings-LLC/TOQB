"""The floor probe before the 3D device test (draft prereg/drafts-2026-11-06/os3d_probe_DRAFT.md; not declared).

build : python gpu/os3d_probe.py build DEVICE_RECORD OUT [--k 4] [--t 3] [--shots 2000]   (offline)
        writes OUT/job and OUT/runs: the floor (CZ skeleton on |0>, every touched qubit read, bridges included) of
        the first k qualifying fold translations in the fixed order, at depth t.
choose: python gpu/os3d_probe.py choose OUT                                            (after psf-os collect)
        writes OUT/CHOICE.json: per candidate its lowest floor and the qubits below the threshold (0.8); the chosen
        translation is the first with none below; `avoid` lists the ones passed over (for os3d_compare_build.py
        --choice). No calibration number is read; nothing is scored or ranked.
"""
import argparse
import json
import os


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("build")
    b.add_argument("device")
    b.add_argument("out")
    b.add_argument("--k", type=int, default=4)
    b.add_argument("--t", type=int, default=3)
    b.add_argument("--shots", type=int, default=2000)
    c = sp.add_parser("choose")
    c.add_argument("out")
    a = ap.parse_args()
    from psf_os import device as Dv
    from psf_os import grid3d as G
    if a.cmd == "build":
        if os.path.exists(a.out):
            raise SystemExit(f"STOP: {a.out} exists")
        rep = G.probe_build(Dv.Device.load(a.device), 4, 2, 2, a.t, 0.8, a.out, k=a.k, shots=a.shots)
        for cd in rep["candidates"]:
            print(f"candidate {cd['index']}: r0 {cd['r0']} c0 {cd['c0']} ({len(cd['used'])} qubits)")
        print(f"circuits {rep['circuits']}  model {rep['qpu_seconds_model']:.1f} s")
    else:
        f = os.path.join(a.out, "CHOICE.json")
        if os.path.exists(f):
            raise SystemExit(f"STOP: {f} exists")
        ch = G.probe_choose(os.path.join(a.out, "job"), os.path.join(a.out, "runs"))
        json.dump(ch, open(f, "w"), indent=1)
        for r in ch["candidates"]:
            print(f"candidate {r['index']}: r0 {r['r0']} c0 {r['c0']}  lowest floor {r['min_floor']:.3f}  "
                  f"below {ch['threshold']}: {r['low']}")
        print(f"chosen: {ch['chosen']}  avoid: {ch['avoid']}")


if __name__ == "__main__":
    main()
