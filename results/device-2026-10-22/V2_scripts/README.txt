Workplace V2 (2026-10-22): independent equality check of the Rust ring template (psfbind ring.rs via toqb.ringport)
against the Python (psf_ai_compile a22 model_template on psf_compile c61). Own devices, faults and seeds.

Run from a folder holding patches/ (a22, a21, a15, a14) and psf_compile c61 importable as psf_compile:
  PSF_BIND_LIB=<path>/libpsfbind.so PYTHONPATH=<c61 dir>:<psf_zero_core dir>:<TOQB> \
    python v2_check.py patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py v2_a22.json
  python v2_sched.py <ai file> /dev/null v2_check.py     # each schedule alone (reuses v2_check.py's setup)

Results of 2026-10-22: v2_a22.json (a22) and v2_a21.json (a21): 295/295 identical (tol 0 and bit for bit),
5 out of scope where the Python used VF2, 1,180 bindings bit-identical; per schedule 174/174 identical, 6 out of scope.
