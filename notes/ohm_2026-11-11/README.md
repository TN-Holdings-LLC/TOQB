# Where Ohm's law comes from, desk study (home, 2026-11-11 night; owner 23:39 / 23:42 JST, "試して")

Owner's idea (a joke question with a real core): the same "flow proportional to push" form (Ohm, Fourier, Fick) appears
everywhere. Real question on a chain: from a domain wall, does the transferred magnetization grow like t (ballistic,
no resistance), t^(2/3)-ish (isotropic, superdiffusive) or t^(1/2) (diffusive, Ohmic)?

`dw_scan.py`: Floquet XXZ brickwork of fSim(theta, phi), 2 gate layers per cycle, N = 40, domain wall, 16 cycles,
quimb MPS (bond 103-420 < cap 512; exact to the cutoff). theta = pi/4:

| phi | regime | M(t) at t = 2 / 4 / 8 / 16 | exponent from t = 2 to 8 | from 8 to 16 |
|---|---|---|---|---|
| 0 | easy-plane (free) | 1.000 / 2.000 / 4.000 / 8.000 | 1.00 | 1.00 |
| pi/2 (= 2 theta) | isotropic | 0.750 / 1.224 / 1.966 / 3.042 | 0.69 | 0.63 |
| pi (= 4 theta) | easy-axis | 0.500 / 0.328 / 0.343 / 0.373 | (frozen) | (frozen) |

- The three regimes separate already by 8 cycles (16 gate layers). The isotropic local exponent alternates between
  even and odd cycles (0.44-0.90); over doubled times it is 0.68 -> 0.63, falling towards the 3/5-2/3 range.
- Diffusion (t^(1/2), the Ohmic case) does not appear from a pure domain wall in this integrable circuit: the
  easy-axis wall freezes. Reaching it needs a weakly polarised (mixed) wall or broken integrability: not studied yet.
- Device caution: noise mixes the spins and so raises M, which looks like extra transport. Raw exponents would be
  biased upward; the comparison must be against the sealed exact M(t), with the free (phi = 0) arm, exact at any size
  by free fermions (gpu/ff_xx.py), beside it.
- Not counted yet: CZ per fSim on the heavy-hex chain after compilation (2 CZ at phi = 0, likely 3 at phi = pi/2), so
  4-6 CZ layers per cycle; tonight's reads stopped between 48 and 72 CZ layers (Hubbard), so about 8-10 cycles.

## 2026-11-12: where diffusion (the Ohmic t^(1/2)) appears (owner 08:31 JST)

Weakly polarised wall = infinite temperature, linear response, exact by statevector with quantum typicality
(`inf_temp.py`, `inf_temp_break.py`; N = 20 and 24 agree, two seeds agree). theta = pi/4. Exponent of S(t) over t -> 2t:

| circuit | 2->4 | 4->8 | 6->12 | reading |
|---|---|---|---|---|
| phi 0 (free) | 1.02 | 1.01 | - | ballistic |
| phi pi/2 (isotropic, integrable) | 0.77 | 0.73 | 0.73 (N 24) | superdiffusive (towards 2/3) |
| phi pi (easy-axis, integrable) | 0.58 | 0.59 | 0.58 (N 24) | slow approach to diffusion |
| phi pi/2 + period-3 Z field (H = 1, 1, -1, 0 pattern) | 0.47 | 0.51 | 0.49 (N 24) | **diffusive** |
| phi pi + period-3 Z field H 1 / 2 | 0.46 / 0.52 | 0.50 / 0.52 | - | diffusive |
| phi pi even layer, pi/2 odd layer | 0.64 | 0.52 | - | diffusive by 8 cycles |
| phi 0 + field (still free) | 0.72 | 1.22 | - | not diffusive (no interaction) |

- The Ohmic exponent 1/2 appears when the chain is interacting **and** not integrable (a fixed period-3 Z field, which
  keeps total Z conserved, is enough): by 4 -> 8 cycles. Free stays ballistic; integrable isotropic stays near 0.73.
- So within 8 cycles (16 gate layers) one circuit family shows all three: 1.0 (free), 0.73 (integrable isotropic),
  0.50 (interacting + field). The joke question becomes: "Ohm's law appears when interactions and chaos are present".
- Device design still to do: (1) the weak wall needs many random initial bit strings (linear response: uniform random
  bit strings b, weight Z_L(b), average Z_R(t)), so many circuits per time point; (2) exact answers per bit string by
  statevector up to about 28 qubits (home VS or POD for many strings); (3) CZ per cycle on the heavy-hex chain;
  (4) noise raises apparent transport: sealed exact values and the free arm beside, as before.
