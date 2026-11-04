# DRAFT (not declared): a three-valued scan reading, DEAD / HEALTHY / UNCERTAIN by the shot noise of each site (workplace, 2026-11-04)

Status: a draft for home and the owner. The declared scan rule (a dead run is 3 or more consecutive sites with
a_j < 0.12; LISTED after two jobs agree; gray for the day) is unchanged by this draft. The counts in the last section
are after the fact on past scans, reference only.

**Why.** Each site's echo signal a_j is an estimate (four inputs x 1000 shots). Near the line its side is decided by
chance: in the separation note's coherent construction, three sites at a mean of 0.10 were read dead in 3 of 4 runs of
the same circuit. A binary reading forces a decision the data cannot support there.

## The reading

- SE_j = (1/4) sqrt(sum over the four inputs of (1 - m_i,j^2) / N_i), from the scan's own counts (0.0145-0.0157 at 1000
  shots for every site).
- **DEAD** if a_j + k SE_j < 0.12; **HEALTHY** if a_j - k SE_j >= 0.12; **UNCERTAIN** otherwise; k = 3 (a site whose
  true signal is at the line is read on the wrong certain side with probability about 0.13 %).
- A dead run (the declared rule) whose sites are all DEAD is a **certain** dead run; one with UNCERTAIN sites is an
  **uncertain** run.

## Proposed use (each item to be decided with the owner; none is in force)

1. **Registry:** a certain dead run is a black observation as today; an uncertain run enters as gray (that day only)
   instead of black, so a run decided by chance cannot become LISTED.
2. **Rescan:** an uncertain run triggers, budget permitting, a rescan of that ring at 4x the shots (SE halves); the
   rescan's reading replaces it.
3. **Reports:** each scan reports the three counts and the uncertain sites with a_j and SE_j.
4. **Sentinel:** the same three values for the sentinel's sites; WEAK/DEAD verdicts carry the count of uncertain sites.

## After the fact: past scans (`notes/uncertainty_2026-11-04/three_valued_scan.py` -> `out/three_valued_posthoc.json`)

Five scan jobs (kingston 31 Oct, 1 Nov, 2 Nov; fez and marrakesh 1 Nov), rings n = 20, 40, 72: 660 sites.

| | sites |
|---|---|
| DEAD (certain) | 178 |
| HEALTHY (certain) | 392 |
| UNCERTAIN | 90 (29 of the 207 sites in declared dead runs; 61 outside them) |

What this shows:
- **kingston's 18-site run is certain on all three days** (0 uncertain sites in it at n = 40): the defect behind Papers 5
  and 6 is not a chance reading.
- **Low-signal rings are often undecided.** fez n = 40: 23 of 40 sites UNCERTAIN (its healthy level sits near 0.16,
  within 3 SE of the line); marrakesh n = 20: 13 of 20, and its one dead run (26, 25, 37) is entirely UNCERTAIN: under
  item 1 it would have entered the registry as gray, not black.
- With the line at 0.12 and SE about 0.016, the band 0.073-0.167 is wide compared with fez's and marrakesh's healthy
  signal. The reading says honestly that 1000 shots do not settle those devices; item 2 (rescan at more shots) or a
  device-specific line (an owner's decision) would be needed there.
