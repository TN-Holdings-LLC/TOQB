# Hubbard: how far the classical check reaches (VS POD, 2026-11-11; workplace reading; not declared)

Source: `pod_vs/` (VS Claude's zip `VSから職場へ_ハバード検算_2026-11-11.zip`, sha256 674451ef...a83d, SHA256SUMS all OK at
the workplace). The values (mode <Z>) are in a separate zip `封印_ハバード値_2026-11-11.zip` (sha256 9bf89071...b7b9),
not opened here; the per-file hashes are in `pod_vs/報告.md`. The criteria were fixed at 02:13 CET before the POD ran
(`指示書_ハバード検算POD_2026-11-11.md`). U = 4 J, dt = 0.25 / J, Neel start, as `hub_count.py`.

## Verdicts (VS's, checked here against the report rows)

| L (qubits) | 4 steps | 6 steps | 8 steps |
|---|---|---|---|
| 20 (40) | criterion 1: Aer exact vs quimb chi 2048, 2.5e-8 | criterion 1: 7.8e-8 | criterion 2 |
| 24 (48) | criterion 1: 2.5e-8 | criterion 1: 7.8e-8 | criterion 2 |
| 30 (60) | criterion 1: 2.5e-8 | criterion 1: 7.8e-8 | criterion 2 |

All nine are "checked". At 8 steps the untruncated Aer run hit each POD's time and was stopped (L 20 / 24 / 30 after
5284 / 2889 / 5626 s), so 8 steps rest on criterion 2 only. Read here from the rows (`max_diff_to`):

- 8 steps, adjacent chi: 256/512 2.1-2.4e-5, 512/1024 2.1-2.5e-7, 1024/2048 5.9-8.0e-10; at chi 2048 the largest bond
  reached 1722 (below 2048), truncation estimate 1.1-1.9e-9, the two conserved-charge checks at most 3.8e-12.
  So the 8-step answers are converged to about 1e-9, far inside the criterion (1e-3), not only at the edge of it.
- The bond dimension does not grow with L (4 steps 214, 6 steps 610, 8 steps 1722 at every L), as expected for a
  fixed depth on a chain: the cost grows roughly in proportion to L. Not measured beyond L 30.

## Cost (16 vCPU PODs, quimb threads 1 for chi <= 512, 8 above, after 04:00 CET)

- quimb at 6 steps: 1.4-9 min per run (chi 256-2048); 8 steps, chi 2048: 16 / 24 / 41 min at L 20 / 24 / 30.
- Aer (untruncated): 4 steps 1-2.3 min; 6 steps 47 / 60 / 79 min; 8 steps over 48-94 min (stopped). Aer's MPS used
  about one core whatever the thread setting.
- Whole run 02:29-06:58 CET, 4 PODs, about $17.4 (limit $20). All PODs deleted.
- VS's changes are in `pod_vs/報告.md`: kit a, then c1 at 03:46; quimb threads changed at 04:00-04:03 (16 threads were
  about 40x slower on the POD); a gap of about 2 minutes (03:58-04:00) when a restart command was cut; rows before the
  change are marked by a `note` line in each report.

## What it means for a declaration (proposal for home and the owner)

- The classical check is not what limits the sizes: 60 qubits at 8 steps (2,336 CZ) are checked to about 1e-9, with
  a criterion fixed beforehand. What limits is the device: 4-6 steps (38-58 CZ per qubit) are inside what has been
  read; 8 steps (77 per qubit, 96 CZ layers) is at the edge (Schwinger N 8 at 105 per qubit did not read).
- Proposed range: L 20 and 30 (40 and 60 qubits), steps 2, 4, 6 (and 8 as the declared edge), U 4, with the U = 0
  ruler (`hub_ruler.py`, exact) of each L in the same job and the per-site charge check recorded beside. Answers for
  the declaration are to be recomputed by the declared script and sealed (the POD values are a cost measurement; their
  zip stays sealed and can serve as a second, independent computation).
- Larger L (e.g. 45, 90 qubits) is likely checkable at the same steps (cost about linear in L), but is not measured;
  it would need its own run before it is declared.
