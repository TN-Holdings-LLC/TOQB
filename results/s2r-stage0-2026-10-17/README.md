# TOQB S2R stage 0: the scored run (2026-10-17 to 2026-10-18)

Pre-registration: [`prereg/2026-10-17-s2r-stage0.md`](../../prereg/2026-10-17-s2r-stage0.md) (SHA-256 `9fa868b7...`).
Score: [`score.md`](score.md) (`python -m toqb.score_s2r` on this folder; re-run on the authors' cloud from the
records alone: the same verdicts and numbers, the 95% intervals equal to the 15th digit).

| ID | verdict | numbers |
|---|---|---|
| S1 every run valid | CONFIRMED | 80 of 80 |
| S2 (primary) PSF-Zero's S2R model more accurate on the stand-in than Qiskit level 2's | NOT DECIDED | mean +0.015, 11 better / 2 equal / 7 worse of 20, p = 0.21 |
| S3 the simulator's ranking agrees better with the stand-in's for PSF-Zero | NOT DECIDED | mean Spearman +0.036, 13 / 0 / 7, p = 0.043 |
| S4 S2R beats device-only SPSA at $192, each compiler | CONFIRMED | PSF-Zero +0.231 (18 / 0 / 2, p = 1.6e-5); Qiskit +0.242 (20 / 0 / 0, p = 9.5e-7) |

Per the pre-registration (section 5), stage 1 is proposed only if S2 or S3 is confirmed: it is not proposed.

## How the 80 runs were made (deviations from section 2, recorded)

The run was interrupted and resumed under the pre-registration's interruption rule ("a run that stops is started
again into a new folder; the first complete run is scored"; a run is one of the 80). `sources.txt` says, for every
run, which folder its record came from; `runs/` holds each folder's logs and times.

1. **First folder, the owner's home PC (WSL), `run.sh`, ten processes.** Started 2026-10-17 07:39:18 CEST. By about
   18:00 CEST 30 runs were complete (the S2R runs of seeds 9001-9015, both compilers; 3.1 hours each) when the PC
   froze under the load and was restarted; the 10 S2R runs then in progress left no record (a record is written
   only when a run ends). No SPSA run had started. The pre-registration's time estimate (7-8 hours) was wrong: about
   25 hours were needed at that pace.
2. **Resume, a rented RunPod pod** (AMD EPYC 7773X, 32 processes; `runs/pod_machine.txt`; Python 3.12.3 with the
   home PC's numpy 2.5.3 and scipy 1.18.1, Qiskit 2.5.2, Aer 0.17.2; TOQB at `133be56` and PSF-Zero at `9cf31744`, the
   same commits as at home), with [`resume.sh`](../../prereg/s2r-stage0-2026-10-17/resume.sh) (run.sh's checks, then
   only the runs without a record): folder `resume1`, 2026-10-18 01:22-03:43 CEST. Its 25 Qiskit runs completed. **Its
   25 PSF-Zero runs stopped at import** because PSF-Zero's Rust core had not been built on the pod (`ImportError:
   psf_zero_core ...`, in `runs/s2r-stage0-2026-10-17-resume1/logs/`); they left no record.
3. **Second resume on the same pod after building the core** (`maturin develop --release`, CORE_VERSION 2026-09-29.1,
   the same as the home PC's): folder `resume2`, `runs/run_psf2.sh`, the 25 PSF-Zero runs, 01:27-03:32 CEST.

So the 80 scored records are 30 from the home PC and 50 from the pod; every run used the pre-registered code, plans
and versions. The two machines were not compared on the same run.

**Looked at before the end:** at about 01:34 CEST on 2026-10-18 the owner asked how the 30 complete runs looked, and
the authors computed S2's and S3's differences on those 15 seeds (+0.022, p = 0.17; +0.042, p = 0.06). Nothing about
the remaining runs could change by then (their seeds and code were fixed); stated here because it was seen.

**Paths:** the pod's paths in the logs and in `runs/run_psf2.sh` are written `<pod>/` here (the zip the pod made
has them as they were).
