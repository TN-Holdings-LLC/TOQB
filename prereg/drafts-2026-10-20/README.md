# Drafts of 2026-10-20

Written at the workplace (about 01:40 CEST) from the home handover of 2026-10-20; nothing in them was run there.

- `C_preregistration_skeleton_r6.md`: the device day as a timed schedule (6 h proposed from fetch to submission),
  a rule for choosing the device (eligibility E1-E4, then the fixed order marrakesh, fez, kingston), steps against a
  calibration update before submission (P1-P4), the open settings with proposals.
- `X22_preregistration_skeleton_r4.md`: the CUDA-Q cost per call (about 0.24 ms per inline noise operation), F3's
  list (current, C1, C3, C1 + C3) and a pod procedure for the measurements.

**Home review (2026-10-20, morning CEST):**

- C r6 §5, E4: PSF's placement does not follow from the coupling map alone; it leaves out failed elements (error
  >= 0.5). Checked on FakeFez with one coupler of PSF's ring set to error 0.9: PSF placed the ring elsewhere and every
  check passed. Whether Qiskit level 2 ever uses a failed element is not known. New: `python -m toqb.s2rc_device
  precheck --fetch DIR` compiles both compilers' circuits (L 8 and 16) on the fetched Target and applies assemble's
  ISA and failed-element checks, so a STOP comes minutes after the fetch, not after training (tested on FakeFez: all
  OK; the check itself flags a CZ on a failed coupler).
- C r6 §4, "Qiskit with the setting of X22 §4 `[ ]`": the tuning run, the rehearsal and the dry run all use Qiskit
  level 2 (`qiskit:2:target:template`). Recommended (owner): C fixes level 2, independently of X22's open choice.
- C r6 §3, "`[ ]` to confirm against toqb/s2rc.py" on the CE formula: confirmed in the home review of r2 (README of
  2026-10-19); it can be closed.
- C r6 §5, P1 (reading the properties history) is an IBM connection: it needs the owner's permission.
- X22 r4: no change proposed.
