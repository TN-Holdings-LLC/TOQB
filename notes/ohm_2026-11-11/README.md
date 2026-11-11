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
