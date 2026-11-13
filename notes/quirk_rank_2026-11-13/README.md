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

- **Candidates:** chains of 20, 40 and 91 qubits on day D's own committed device record.
  - First the default chain: the du91 shape, else rule C, as `gpu/hub_build.chain_of`.
  - Then the rule C chain from every start that reaches n, in START_ORDER, dropping repeated qubit sets.
  - That gives 16 or 17 candidates.
- **Ordering:** quirk.rank orders them with the ledger before D.
- **Scoring:** the chosen chain and the default chain are compared on day D's floor, which the ranking never saw.

**Result:**

- **Moves:** the ranking moved the choice in 9 of 18 (day, n) cases.
- **Mean floor:** of those 9, the chosen chain's mean floor on day D was lower than the default's in **4** and
  higher in 5.
- **Weakest fifth:** it held fewer of day D's weakest fifth in 4, more in 4, and the same in 1.

**On these records the reordering did not make the next day's floor better.** The full table is in effect.md.

**Why this can differ from the ledger's 0.60 persistence:**

- **Day D's floor is known only on the qubits day D's jobs used.** The chosen chain often runs over qubits that day
  D did not measure. The two chains are then scored on different numbers of qubits: 16 for the chosen against 7 for
  the default on 11-05 at n = 20, and 22 against 31 on 11-07 at n = 40.
- **The default chain already holds few marked qubits.** It holds 0 to 6 at n = 20 and 40.
- **Swapping a few marked qubits brings in others.** The newly used qubits can be just as weak. The 0.60 says the
  weakest stay weak, but most of the floor's spread lies elsewhere.
- **A fair test needs a planned measurement.** One floor job on all 156 qubits on day D (a single short circuit)
  would score every candidate fully.

## Use

```
python gpu/quirk_ledger.py --psf-os PATH notes/quirk_rank_2026-11-13/quirk_ledger.json [--before YYYY-MM-DD]
python notes/quirk_rank_2026-11-13/effect.py --psf-os PATH
```

A builder that uses rank must write rank's report into build.json. That use is the special condition.
