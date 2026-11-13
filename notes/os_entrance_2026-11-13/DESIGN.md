# One entrance for any circuit: design only (workplace, 2026-11-13; owner 10:53 JST, item 2; not built)

Today every experiment has its own builder (`gpu/hub_build.py`, `ohm_build.py`, `ffxx91.py`, `hub_dt.py`, the 3D
`grid3d` / `grid3d_line` paths, the honeycomb strip of `notes/ohm_honeycomb_2026-11-13`). They repeat the same
steps: choose a shape, put the logical qubits on it, hand the circuits to `user2d.build_batch`, add the mirror from the
compiled circuit, check CZ counts, write answers by label. This note designs one entrance that does those steps from
the circuit alone, by fixed rules, keeping the project's policy: placement from the coupling graph and failed marks
only (no error numbers, no search such as SABRE), no mitigation, controls in the same job, answers sealed.

## 1. Input

```
entrance.build(dev, circuits, observables, answers=None, shots=4000, max_seconds=160, options={})
```
- `circuits`: logical circuits (Qiskit), qubit k = logical site k; one- and two-qubit gates, final measurements only
  (as `user2d.analyse` already refuses anything else). Several circuits share one placement (same interaction graph),
  as every builder above does (arms x times x strings).
- `observables`: per-qubit Z (default), or Pauli products per circuit (written as `exact_tn` takes them).
- `answers`: optional exact values per circuit and observable. If absent, the entrance can try to compute them
  (`card.exact` / `exact_tn`, under their guards) and says which method and cost; otherwise the card reports the
  Clifford twin's share kept (section 4).
- `options`: shape family forced or "auto"; the sentinel fallback (`same_qubits`, off by default); controls on or off.

## 2. Choosing the placement family by fixed rules (no search)

From the union of the circuits' two-qubit pairs (the interaction graph G):

| test on G (in this order) | family | existing code |
|---|---|---|
| G is a path (max degree 2, connected, no cycle) | chain: daily/du91 shapes first, then rule C (`psf_os.chain`) | `hub_build.chain_of` |
| G is a cycle | ring: the rule's ring (`place.rule_choice`, pendants allowed) | `compile.RuleCompiler`, `place` |
| G is a subgraph of heavy-hex written on Heron labels | translation copy (`lattice2d.place`) | `user2d` |
| G is a 3D grid 4 x M x N with M N <= 6 | fold v3.1 / v3.2 carry, or line (`grid3d`, `grid3d_line`) | `grid3d` |
| G is a honeycomb strip (rows and bridges of Heron r2) | strip rule (rows 0 .. R-1, columns 0 .. c) | notes/ohm_honeycomb_2026-11-13 (to port) |
| G is a 2D square grid | not native: map onto a strip or 3D layer with swaps (cost reported, section 3) | partly in `grid3d` |
| anything else | refused, with the reason and the nearest family | - |

Recognition is by graph tests (isomorphism to a path, a cycle, a grid, a strip) that are deterministic; when two
families fit, the table order decides. The chosen family, the rule inside it, the start or translation found, and the
step counts go into `build.json` (as rule C already records its start and steps). If the family refuses on the day's
record, the entrance says why (e.g. "longest usable chain 84, need 91": `notes/placement_fallback_2026-11-13`) and
does not fall through to a different family on its own; a fallback is a named option the user asks for.

## 3. Cost report (before anything runs)

Per circuit and in total: CZ count and CZ layers after compilation; the inflation against the circuit's own depth
(two-qubit layers of the logical circuit against CZ layers on the device: an fSim is 3 CZ, an XX+YY 2 CZ, a SWAP 3 CZ,
an RZZ(+-pi/2) 1 CZ, a generic block up to 3); CZ per qubit; the qubits used; the job's seconds by the time model;
whether the job fits `max_seconds`. And a readability hint from the records (not a verdict): the CZ layers at which the
same family last read and first did not (from `notes/boundary_*`), e.g. "Hubbard-like brickwork: read at 48 layers,
not at 72". The user sees "this circuit becomes N times deeper here" before submitting.

## 4. Controls added automatically

Already in `user2d.build_batch`: the floor (the compiled circuit with every one-qubit gate removed: readout and idle),
the mirror (here: the compiled circuit, a barrier, its inverse, as `hub_build._mirror_from_compiled`), one ring
sentinel per job (with the optional fallback). New: the **Clifford twin** (home's item 1, being designed today): the
compiled circuit with every one-qubit rotation angle rounded to a multiple of pi/2 and the CZ left as they are, so the
twin has the same two-qubit gates and layers and an exact answer by the stabilizer method at any size. The twin's
share kept r_twin = sum z e / sum e^2 estimates how much of a signal the device keeps through this very gate pattern.

## 5. Output: the answer card

Per circuit: READS / AGREES against the answers when there are answers (as `user2d.card`, `hub_score`); the share kept
r and the split MSE / mean square = (1 - r)^2 + rest (`notes/paper9/r_thread_2026-11-13`); floor, mirror, sentinel,
CZ and layers. Without answers: r_twin and whether r_twin >= 1 - 1/sqrt(2) = 0.293 ("would read if the error were a
pure shrink"), with the caution of the r thread: for circuits whose error also bends the pattern (Hubbard U = 4 at 6
steps read r 0.38-0.42 and still did not read), r_twin over-promises. The card says which.

## 6. What exists and what is missing

| piece | exists | missing | effort (rough) |
|---|---|---|---|
| analyse the circuit, refuse what is not read | `user2d.analyse` | observables other than per-qubit Z in the card | 0.5 day |
| family recognition (section 2) | - | graph tests, the order table, refusal reasons | 1 day |
| chain placement | `chain`, du91 shapes, `hub_build.chain_of` | move `chain_of` into psf-os | 0.5 day |
| ring placement | `place`, `compile` | (none) | - |
| 2D copy by translation | `lattice2d`, `user2d` | (none) | - |
| 3D layers | `grid3d`, `grid3d_line` (kicked Ising only) | a generic 3D circuit through the fold schedule (today the schedule is written for the Ising step) | 2-3 days |
| honeycomb strip | notes only | the strip rule in psf-os, tests | 0.5 day |
| mirror from the compiled circuit | in `hub_build` (patched into user2d at run time) | a supported option of `user2d.build_batch` (user2d is not to be changed: a wrapper module instead) | 0.5 day |
| sentinel and its fallback | `sentinel` (fallback `same_qubits` added 2026-11-13) | (none) | - |
| Clifford twin | - (home designs it today) | build, stabilizer answers, card fields | 1 day after home's design |
| exact answers | `card.exact`, `exact_tn`, `kim`, MPS scripts in the notebook | a single "answers" step with the method chosen by size and cost, and its guard | 1 day |
| cost report and readability hint | CZ counts in builders, `job.qpu_seconds` | inflation, layers, the boundary lookup | 0.5 day |
| card with r and the split | `user2d.card`, `hub_score` | r, rest, r_twin, without-answers mode | 0.5 day |
| one command | `cli.py` (run2d) | `psf-os entrance build / check / score` | 0.5 day |

About 8-10 working days in all, the 3D generalisation being the largest piece. The existing builders keep working;
each can later become a thin call of the entrance, checked by the regression of `notes/placement_fallback_2026-11-13`
(same gate hash on the recorded jobs).
