# Quirk ledger for placement: psf_os.quirk.rank and a desk check (workplace VS Claude, 2026-11-13; desk only, not declared)

OS item 4. Owner 11:25 JST: the quirk ledger may be used for placement, as a **special condition** of the placement
policy, and every use must be written in the record. Nothing here places, builds or runs a job, and the builders'
default behaviour is unchanged (quirk.rank is called by nobody yet).

## Parts

- **psf-os `psf_os/quirk.py`**: `rank(dev_name, candidates, ledger, before) -> (ordered_candidates, report)`, the
  interface agreed with the workplace Claude. Rule `floor-fifth` version 1, fixed:
  1. Take the device's latest ledger day strictly before `before`. Nothing dated `before` or later is read.
  2. Mark that day's weakest fifth by floor loss (k = max(1, n // 5); ties by the smaller label; nothing marked
     below 10 qubits).
  3. Sort the candidates by how many marked qubits they hold, ascending and stable (ties keep the caller's order). No
     marks means no reordering.
  - The mirror value is not used. Its day-to-day rank correlation was about +0.3, against +0.8 for the floor
    (`notes/quirk_ledger_2026-11-13`).
  - No IBM calibration number is read.
  - The report carries the rule and version, the special-condition sentence, the ledger day used, the marked
    qubits, the count per candidate, the order, the chosen and default candidate, and whether the choice moved.
  - Tests: `tests/test_quirk.py`, 7 cases. They cover:
    - no look at days on or after `before`;
    - only the latest earlier day used;
    - ties keep the caller's order;
    - no marks means no reordering (no earlier day, another device, too few qubits);
    - path and string numbers;
    - other forms refused.
- **Notebook `gpu/quirk_ledger.py`**: writes the ledger in the form rank reads: `{"format": "psf-os quirk ledger 1",
  "devices": {device: {day: {qubit: {"floor", "mirror", "n"}}}}}`.
  - It reads the records as `notes/quirk_ledger_2026-11-13/ledger.py` does.
  - `--before DAY` leaves later days out of the file too.
  - `quirk_ledger.json` here is the full ledger: 3 devices, 16 device-days, 36 jobs. Its floor equals
    ledger.json of 11-13 (difference 0).
- **`effect.py`**: the desk check below. It writes `effect.json` and `effect.md`.

## Desk check on ibm_fez (not a verdict)

**For every fez ledger day D with an earlier ledger day (6 days, 11-05 to 11-12):**

- **Candidates:** chains of 20, 40 and 91 qubits on day D's own committed device record, from
  `psf_os.quirk_chain.candidates`: the chain rule's chains, one per start, in its own order (du91 shape copies, then
  rule C from every start). The first is chain_of's chain on physical qubits. That gives 16 to 28 candidates.
- **Ordering:** quirk.rank orders them with the ledger before D.
- **Scoring:** the chosen chain and the default chain are compared on day D's floor, which the ranking never saw.

**Correction (2026-11-13 g).** The first version of this check (commit fe73c515) took a du91 shape's own snake
labels as the default chain. On ibm_fez the shape's qualifying copy is shifted (for example by 4 rows on 11-11 at
n = 20: labels 0, 1, 2 ... placed on 80, 81, 82 ..., as the hubbard record's mapping shows), so the default rows at
n = 20 and 40 were on the wrong qubits. Its result ("moved 9 of 18, better in 4 of 9, no effect") is withdrawn.

**Result (corrected):**

- **Moves:** the ranking moved the choice in 15 of 18 (day, n) cases. It did not move at n = 91 on 11-08, 11-11 and
  11-12.
- **Mean floor:** of those 15, the chosen chain's mean floor on day D was lower than the default's in **13** and
  higher in 2 (11-07 and 11-10, both at n = 91).
- **Weakest fifth:** it held fewer of day D's weakest fifth in 11, more in 4, and never the same.
- At n = 20 the chosen chain's mean floor on D was lower every time (6 of 6), for example 0.059 to 0.018 on 11-12.

**On these records the reordering lowered the next day's floor of the chosen chain in most cases.** The full table
is in effect.md. This is a desk check, not a verdict, and nothing was placed by it.

**Cautions:**

- **Day D's floor is known only on the qubits day D's jobs used.** The two chains are often scored on different
  numbers of qubits (for example 39 for the default against 22 for the chosen on 11-07 at n = 40). A qubit that day
  D did not measure does not count.
- **The defaults were the chains day D's own jobs used,** so they are fully measured where those jobs ran, and the
  chosen chains are partly unmeasured. The comparison can lean either way.
- **A fair test needs a planned measurement.** One floor job on all 156 qubits on day D (a single short circuit)
  would score every candidate fully.

## Use

```
python gpu/quirk_ledger.py --psf-os PATH notes/quirk_rank_2026-11-13/quirk_ledger.json [--before YYYY-MM-DD]
python notes/quirk_rank_2026-11-13/effect.py --psf-os PATH
```

A builder that uses rank must write rank's report into build.json. That use is the special condition.
