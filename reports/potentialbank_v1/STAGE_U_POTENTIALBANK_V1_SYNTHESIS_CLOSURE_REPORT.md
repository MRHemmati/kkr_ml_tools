# Stage U — PotentialBank v1 synthesis — closure — 2026-08-11

**Complete.** Froze the post-Stage-T state into a clean, auditable v1 evidence package. **Offline/synthesis
only — no submissions, no process-control, no daemon/pkg/env changes, no AiiDA DB writes, no MP API, no new
certification.** Read-only AiiDA was not even needed (all from existing manifests). WSe2 122051 untouched.

## Final donor count
**238 certified donor nodes → 237 unique-sha donors** (1 recorded duplicate-sha exclusion: E1 Bi2X4 pk
24009≡24011, sha `0fe18594`). v1 manifest sha256 `4186813d…`.

## Family coverage (unique donors / materials / F2-eligible)
| family | donors | materials | F2-eligible | empty-sphere |
|---|---|---|---|---|
| NbSe2/Bi (E1) | 160 | 14 | 12 | no |
| simple metals (Nb/Al/Cu/Ag/Mo) | 24 | 5 | 5 | no |
| heavy-SOC (Au/W/Pt/Sb/Pb) | 24 | 5 | 5 | no |
| magnetic (Fe/Ni/Co) | 13 | 3 | 3 | no |
| ordered intermetallic (CuZn/Ni3Al/FeAl) | 6 | 3 | 3 | no |
| covalent empty-sphere (Si/Ge) | 4 | 2 | 2 | **yes** |
| metallic layered chalcogenide (TiSe2) | 2 | 1 | 1 | no |
| ionic rocksalt (MgO/NaCl) | 4 | 2 | 2 | no |
| **total** | **237** | **35** | **33** | — |
42 compatibility classes.

## F2-eligible roster (33 materials)
21 benchmarked expansion materials — Nb, Al, Cu, Ag, Mo, Au, W, Pt, Sb, Pb, Fe, Ni, Co, Si, Ge, CuZn, Ni3Al,
FeAl, TiSe2, MgO, NaCl — plus 12 E1 NbSe2/Bi formulas (structural, not re-benchmarked here).

## Warm-start evidence summary
Same-structure warm-start: 2–7 iters vs ~66–1350 cold on a converging target across all 8 expansion families;
donor-choice-independent (33/33), direction-symmetric where cold-comparable. Mixing-dependent magnitude
(Broyden ~96–99% / linear ~33%) and contour-qualified (TiSe2 coarse-only) — reported per-family, no misleading
pooled headline. Not certified (benchmark). Full table: `WARMSTART_BENCHMARK_V1_REPORT.md`.

## Hard-case map (9 parked/deferred, root-caused)
MoS2 (NACLSD, primitive+conventional), WSe2 (SOC contour/EMIN instability + ~70 min/iter, paused 122051), NbS2
(NACLSD-solved but non-converging/expensive), TaS2 (SOC-NaN-prone), TiAl (VERTEX3D), Bi2Te3/Bi2Se3
(hard-convergence), CaF2 (octahedral empty sphere), LiF (Z=3 light). Details: `workspace/synthesis_v1/
deferred_parked.csv`.

## Artifacts produced (all under repo; no DB)
- **Reports:** POTENTIALBANK_V1_MANIFEST_REPORT, WARMSTART_BENCHMARK_V1_REPORT, ADVISOR_INDEX_V1_UPDATE_REPORT,
  PAPER_CLAIM_LADDER_AFTER_POTBANK_V1, this closure.
- **`workspace/synthesis_v1/`:** `potentialbank_v1_manifest.csv` (+summary.json), `coverage_by_family.csv`,
  `coverage_by_compat.csv`, `f2_eligible.csv`, `deferred_parked.csv`, `warmstart_synthesis.csv`,
  `advisor_index_v1.json` (sha c3a32ce0), `advisor_example_tips_v1.json`, build scripts
  (build_potbank_v1/build_tables/make_figures_v1/build_advisor_v1.py).
- **`workspace/synthesis_v1/figures/`:** fig1 coverage-by-family, fig2 F2-eligible-by-family, fig3
  warm-vs-cold-by-family, fig4 savings-distribution, fig5 deferred-hardcase-map, fig6 workflow/provenance (6 PDFs).

## Audit line
Stage U = offline synthesis only. **Zero** submissions, process-control, kills, daemon/pkg/env changes, AiiDA
DB writes/labels/extras/groups, MP-API calls, or new certifications. Read-only inputs = existing per-stage
manifest CSVs (+ curated warm-start numbers from the stage records). WSe2 122051 and NaCl (already retrieved)
untouched. All outputs are local workspace artifacts. Count reconciled honestly (238 nodes / 237 unique, 1 E1
byte-dup recorded). Claims tiered in `PAPER_CLAIM_LADDER_AFTER_POTBANK_V1.md`: same-structure reuse strongly
supported; **no cross-material transfer, no guaranteed acceleration**; ml_assist mechanism validated but not a
broad-transfer claim; hard cases documented. **Stage U complete; PotentialBank v1 frozen at 237 unique donors.**
