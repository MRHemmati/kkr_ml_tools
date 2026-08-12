# Proposal 03 — An open, reproducible KKR-BdG SCF-convergence dataset and benchmark, with a failure-mode taxonomy

## Title
**A provenance-complete dataset and benchmark for self-consistent KKR / KKR-BdG convergence:
trajectories, failure modes, and baselines for convergence-prediction ML.**

## Short abstract
Progress on ML-accelerated electronic-structure convergence is held back by the absence of
standardized, provenance-tracked datasets of real SCF runs — including the *failures*. We curate and
release such a dataset from a multi-year AiiDA database of thousands of KKR / KKR-BdG Green-function
calculations on NbSe₂-based systems: input parameters, full RMS-error trajectories, convergence
labels, and a typed **failure-mode taxonomy** (Broyden oscillation, RMS plateau, late catastrophic
blow-up, Fermi-energy instability). We provide leave-one-dopant-out splits and baseline models
(KRR/XGBoost/LSTM) so future methods can be compared on equal footing.

## Scientific motivation
- Convergence-prediction and learned-mixer papers each invent their own ad-hoc data; there is no
  shared, provenance-complete benchmark for KKR-family SCF.
- The *failures* are the scientifically interesting and operationally valuable cases, and they are
  systematically present here (471 `KkrCalculation` exit-302, 202 exit-120, 187 killed, plus
  `kkr_bdg_wc` exit 301/302/303/304). A typed taxonomy turns them into labeled examples.
- A clean "data descriptor" is a publishable artifact in its own right and gives Proposals 01/02 a
  citable backbone.

## Existing data that supports this proposal — [FACT]
- Full AiiDA provenance: **7,668 CalcJobNodes / 6,416 WorkChainNodes**, 2021–2026.
- Already-extracted slices: `kkr_scf_metadata.csv` (705 wc), `rms_sequences_*.pkl`,
  `kkr_scf_full_dataset.pkl.gz`, census pickles, `lodo_indices.npy`, `kkr_scf_masks.pkl`.
- Rich, real exit-code spectrum across `KkrCalculation` / `KkrimpCalculation` / `kkr_bdg_wc`.

## Relevant AiiDA nodes / groups / workflows — [FACT]
- Everything reachable from `kkr_scf_wc`, `kkr_bdg_wc`, `kkrimp_BdG_wc`, `KkrCalculation`,
  `VoronoiCalculation`; exit-code distributions already censused in `workspace/analysis/`.
- Stable identifiers: export by **UUID** (PKs are not portable across DB exports — help0 §1).

## Question it answers
*What does real KKR-BdG SCF convergence look like at scale — how often and in what characteristic
ways does it fail — and what is a fair baseline for predicting it?*

## What is already done — [FACT]
- The census, the metadata table, the RMS trajectories, the LODO splits, and baseline LODO scores
  (Proposal 01) all exist. The failure modes are *described qualitatively* in help0/1/2 (§4–§5).

## What is missing — [OPEN]
- A **programmatic failure-mode classifier** (turn the qualitative taxonomy into per-run labels:
  plateau, oscillation, late blow-up, EF-instability, hard error by exit code).
- A clean, de-duplicated, **material-family-tagged** export (NbSe₂ vs Bi/NbBi vs other), with the
  `USE_BDG` flag re-derived.
- A documented data schema + license + DOI-ready package (Zenodo / Materials Cloud Archive).

## Additional calculations that may be needed later
- **None required** — this proposal is curation + analysis of existing provenance (its low-risk appeal).
  Optionally, regenerate a few canonical "textbook" failure trajectories for didactic figures.

## Possible figures
1. Distribution of SCF outcomes / exit codes across the DB (sunburst or stacked bar).
2. Archetypal RMS trajectories, one per failure class.
3. 2D map of convergence rate vs (IMIX, STRMIX) — the mixing-scheme landscape.
4. Baseline model leaderboard (KRR/XGB/LSTM, LODO).

## Possible tables
- Dataset schema (columns, units, provenance link).
- Failure-mode taxonomy with counts and exit-code mapping.
- Baseline results table (the benchmark numbers future work must beat).

## Possible paper outline
Intro (need for a shared benchmark) → Provenance & extraction → Data schema → Failure-mode taxonomy
→ Splits & baselines → Usage examples → Availability (DOI, license).

## Feasibility
**Medium-high.** Most pieces exist; the work is classification logic, de-confounding, packaging, and
writing. No new compute.

## Risk level
**Low.** Main risks are curation effort and ensuring no sensitive/other-project data leaks into the
public export (filter strictly to this project's groups/UUIDs).

## Publication potential
**Solid** as a data descriptor (*Scientific Data*, *npj Computational Materials* data paper,
*Materials Cloud Archive* + companion). High citation utility as the backbone for Proposal 01.

## Suggested next steps
1. Write a read-only failure-mode classifier over the RMS trajectories + exit codes.
2. Re-derive `USE_BDG` and `system_family`; de-duplicate; tag by group/UUID.
3. Draft the data schema and a minimal "load + reproduce a baseline" example notebook.
4. Decide on the public export scope (which groups/UUIDs) before any archive packaging.
