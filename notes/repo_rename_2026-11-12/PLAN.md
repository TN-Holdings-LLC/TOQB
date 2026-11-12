# Renaming TOQB (owner 2026-11-12 15:31 JST: option 1; guide again at tonight's home work)

Decision: the repository TN-Holdings-LLC/TOQB is renamed to a research-records name; the readable-depth metric gets a
new repository of its own. The name "TOQB" is **never reused** for another repository: GitHub redirects the old URL
(and old clones' remotes) to the renamed repository only while no repository takes the old name, and papers 7 and 8
(Zenodo, doi:10.5281/zenodo.24046673 and 10.5281/zenodo.24136512) cite github.com/TN-Holdings-LLC/TOQB with commit
hashes. Commit hashes do not change with a rename.

## Name candidates (owner to choose)

Research records (the renamed TOQB):
1. `psf-os-research`: declared device tests, records and notes of psf-os (short, says what it is)
2. `readable-quantum-dynamics`: follows the title of paper 8
3. `psf-os-lab-notebook`

Metric (new repository):
1. `readable-depth`: how deep a circuit stays readable raw, per problem (spec, scorer, boundary table, ledger)
2. `raw-readability`

## Steps tonight (home, VPN ON; the owner's actions on GitHub)

1. GitHub: TN-Holdings-LLC/TOQB -> Settings -> General -> Repository name -> new name -> Rename.
2. Check: https://github.com/TN-Holdings-LLC/TOQB redirects to the new name (open it in a browser).
3. WSL: `cd ~/toqb_push_2026-10-15 && git remote set-url origin https://github.com/TN-Holdings-LLC/<new name>.git && git remote -v`
   (old remotes keep working through the redirect, but set it anyway).
4. GitHub: New repository under TN-Holdings-LLC, name = the metric name, empty (no README), public or private as the
   owner decides.
5. Home Claude then commits: the new README head of the research repository (below), the citation note, and the first
   commit of the metric repository as a bundle (spec, scorer copy, boundary table, ledger), pushed by the owner.

## README head for the renamed repository (draft)

    # <new name>: declared, raw device tests of psf-os on IBM Heron (formerly TOQB)

    This repository holds the declared device tests behind papers 7, 8 and 9 of TN Holdings: every test declared
    (prereg/) before its calibration was fetched, raw counts and scores committed, answers sealed until the verdicts,
    every result re-scorable without IBM (`python reproduce.py`). Until 2026-11-12 it was named TOQB (Task-Oriented
    Quantum Benchmark, a compiler benchmark, layers 1-3, standard runs 1-2: kept under results/ and toqb/); the old URL
    github.com/TN-Holdings-LLC/TOQB redirects here, and the papers' commit hashes are unchanged.
    The readable-depth metric now lives in TN-Holdings-LLC/<metric name>.

## Citations to update later (no change to published records)

- Papers 7 and 8 stay as published (the redirect keeps their links working).
- Paper 9 and later cite the new name, with "(formerly TOQB)" once.
- notes/paper8/ZENODO.md, notes/paper7/ZENODO.md: add a line with the new URL.
