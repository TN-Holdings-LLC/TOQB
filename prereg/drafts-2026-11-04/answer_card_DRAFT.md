# DRAFT (not declared): the answer card, a value with its chance spread and its bias indicators kept apart (workplace, 2026-11-04)

Status: a draft for home and the owner. It changes no verdict and no rule; it changes what a report shows next to each
value. A worked example on a past job is at the end (after the fact, reference only).

**Why.** A quantum device returns a distribution; a reported value (a <Z_q> or a magnetisation) is an estimate from
samples. Its distance from the true value has two parts that behave differently: **chance** (shot noise, shrinks as
1/sqrt(shots)) and **bias** (noise in the device, readout, drift; more shots do not remove it). Today's reports give one
number and a fixed line (AGREES within 0.05), which mixes the two. The card keeps them apart.

## The card (one row per reported value)

| field | meaning | from |
|---|---|---|
| value | the estimate (mean over the qubits scored) | counts |
| 2 SE | chance: two standard errors of shot noise, sqrt(sum_q (1 - z_q^2) / shots) / n_q x 2 | counts (`kim.z_values`, `ising2d` the same way) |
| exact, difference, difference / SE | where an answer exists: how far the value is, and in units of SE (a difference of many SE is bias, not chance) | sealed answers |
| floor | the theta = 0 control of the same job at the same t (readout and idle loss; ideal 1) | same job |
| sentinel | CLEAN / WEAK / DEAD of the ring sentinel (and, when present, the mirror sentinel's flags) | same job |
| scored qubits | which qubits were averaged (answered qubits only at large t) | answers |

Rules for writing it: the verdicts stay those of the declaration; the card is printed beside them. A difference within
the AGREES line but many SE away is written as **within the line, but a bias** (it would not shrink with more shots).
A value without an answer (t = 20) gets value, 2 SE, floor and sentinel only.

## Where it goes

The scorers (`gpu/kim_*_score.py`, `gpu/os2d_score.py`, the P6 scorer) add the card to `scores.json`; README tables show
"value +- 2 SE" and, where answered, "difference (difference / SE)". Proposed to start with the next declaration (P6's
run or the OS2D test), without changing its verdicts; the OS2D draft already reports 2 SE beside AGREES.

## Example (after the fact): P5 stage E, job K on ibm_kingston (suspect lattice), `results/kim-e-2026-11-03/K`

`notes/uncertainty_2026-11-04/answer_card.py` -> `out/answer_card_kingston_K.json`. Sentinel CLEAN; floor 0.977,
0.977, 0.976 at t = 6, 7, 8.

| theta | t | M answered +- 2 SE | exact | difference | difference / SE |
|---|---|---|---|---|---|
| 0.4 | 6 | 0.870 +- 0.001 | 0.902 | -0.031 | -45 |
| 0.4 | 7 | 0.858 +- 0.002 | 0.887 | -0.029 | -38 |
| 0.4 | 8 | 0.877 +- 0.002 | 0.904 | -0.027 | -31 |
| 0.8 | 6 | 0.432 +- 0.003 | 0.440 | -0.008 | -6 |
| 0.8 | 7 | 0.446 +- 0.003 | 0.458 | -0.012 | -9 |
| 0.8 | 8 | 0.474 +- 0.003 | 0.484 | -0.009 | -6 |
| 1.0 | 6 | 0.173 +- 0.003 | 0.169 | +0.004 | +3 |
| 1.0 | 7 | 0.184 +- 0.003 | 0.180 | +0.004 | +3 |
| 1.0 | 8 | 0.193 +- 0.004 | 0.186 | +0.007 | +4 |

What the card adds to "AGREES at all three theta": at theta 0.4 the device is 30-45 SE below the answer, so the miss is
bias, not chance; the floor (0.977) accounts for about 0.02 of the 0.03 (0.902 x 0.977 = 0.881 against 0.870 measured).
At theta 1.0 the differences are 3-4 SE, near the edge of chance. The verdict (AGREES) is unchanged; the card says what
kind of agreement it is.
