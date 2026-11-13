# ibm_marrakesh refused every job on 11-12: why, and a fallback that changes nothing elsewhere (workplace, 2026-11-13)

Owner 10:53 JST, item 3. Desk only. Reads the coupling graph and failed marks of the records only (no error numbers).
Records: `results/ohm-2026-11-12/fetch_in/ibm_marrakesh` (11:19 CET), `results/ohm-kingston-2026-11-12/fetch_in/
ibm_marrakesh` (12:06), `results/xx91-2026-11-12/fetch_in/ibm_marrakesh` (15:33): the same failed elements in all
three, qubits 30, 32, 34, 41, 46, 47, 48, 56, 73, 82, 113, 119, 130, 136 and coupler 113-119:

```
row 0 (  0- 15) ................   bridges 16-19 ok
row 1 ( 20- 35) ..........X.X.X.   bridges 36-39 ok
row 2 ( 40- 55) .X....XXX.......   bridge 56 failed
row 3 ( 60- 75) .............X..
row 4 ( 80- 95) ..X.............
row 5 (100-115) .............X..   bridge 119 failed
row 6 (120-135) ..........X.....   bridge 136 failed
row 7 (140-155) ................
```

## Two different causes

1. **Ohm (40 qubits) and Hubbard (40 / 60): the ring sentinel.** `user2d.build_batch` puts one 40-site ring sentinel
   in every job. On this record a 40-site ring needs a cycle of 32 with 8 pendant qubits (`place.rule_choice`: kind
   "pend"). The user's model circuit and the sentinel's echo are both compiled by the same rule and land on **the same
   40 physical qubits, but the pendants come in another order** (user 64, 65, 66, 57, 67 ...; sentinel 65, 64, 66, 67,
   57 ...). `sentinel.build` compared the orders and refused. On fez and kingston no pendant is needed and the orders
   agree. The chains of the user circuits themselves were fine (rule C, start (+1, 0, 0)).
2. **XX91 (91 qubits): no chain exists.** Rule C reached 84 from its fixed starts; from every row qubit as a start it
   also reaches 84; and the exact longest simple path on the usable graph (CP-SAT, `longest_path.py`, OPTIMAL, bound
   = value) is **84**. No chain rule can place 91 sites on this record; a "rule C2" would not help.

## The fallback (psf-os `sentinel.build`, option `fallback="same_qubits"`, off by default)

When asked, a sentinel whose ring holds exactly the user's physical qubits in another order is kept, and its record
says so (`"fallback": {"rule": "same_qubits", "user_ring": ..., "sentinel_ring": ...}` in `runs/ksent_*.json`, which
the manifest hashes). The verdict already reads the sentinel's own order, so dead and weak runs stay runs of
neighbours on the sentinel's ring. Builders: `--sentinel-fallback same_qubits` in `gpu/hub_build.py`, `ohm_build.py`,
`hub_dt.py`, `ffxx91.py`; build.json then carries `sentinel_fallback: {asked, used}` (unchanged when not asked).

## Nothing changes where the old rule built (`regress.py`, `regress.json`)

Each declared job of 11-11 and 11-12 rebuilt on its own fetch record with the current psf-os, without and with the
fallback, compared with the recorded job by psf-os's gate hash (`psf_os.gatehash`; the QPY bytes, circuits_sha256,
differ because this machine has another Qiskit (2.6.1), as recorded on 11-05):

| job | device | without | with fallback |
|---|---|---|---|
| hubbard 11-11 | fez | same gates (1af20d01...) | same gates |
| hubbard-big 11-11 | fez | same gates (ebe6b5c2...) | same gates |
| hub-dt 11-12 | fez | same gates (6e1c5376...) | same gates |
| ohm 11-12 | fez | same gates (860d3133...) | same gates |
| ohm repeat 11-12 | kingston | same gates (138851f7...) | same gates |
| xx91 11-12 | fez | same gates (9e8330a9...) | same gates |

psf-os tests: `tests/test_sentinel_fallback.py` (3: marrakesh refused by default and built with the fallback; fez
byte-identical with and without; unknown option refused; needs TOQB_DIR), with test_m6_sentinel and test_user2d: 16
passed.

## On ibm_marrakesh with the fallback

| job | without | with fallback |
|---|---|---|
| Ohm (11:19 and 12:06 records) | refused (sentinel) | builds: 508 circuits, 158.4 s by the model; chain rule C (start +1, 0, 0); CZ (layers) A0 234 (12) / 468 (24), A1 = A2 351 (18) / 702 (36), as on fez |
| Hubbard L 20 / 30 (11-11 record) | refused (sentinel) | builds: 40 circuits, 47.6 s; CZ 384-1752, arms equal |
| XX91 (15:33 record) | refused (chain) | refused: the longest possible chain is 84 |

Using the fallback in a declaration is the owner's choice; the record shows it either way.
