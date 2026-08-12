# Advisor index v1 update — 2026-08-11

Updated the **local** KKR-convergence-advisor index to cover all 237 unique certified donors + all warm-start
evidence. **Nothing installed or restarted; no DB writes.** Artifacts: `workspace/synthesis_v1/
advisor_index_v1.json` (sha `c3a32ce0…`) + `advisor_example_tips_v1.json`.

## Index contents (local JSON)
- **35 materials** across 8 families, 237 unique donors, 42 compat classes; per material: donor sha256 list,
  compat class, NSPIN/SOC/LMAX, empty-sphere flag, F2-eligibility, and (where measured) warm-start cold/warm/
  saved/% + contour caveat.
- **33 F2-eligible materials** (≥2 unique donors) flagged; warm-start evidence attached for the 21 benchmarked
  expansion materials (E1 F2-eligibility is structural/manifest-derived, **not** re-benchmarked here — labelled
  as such).
- **9 parked-hard-case warnings** (MoS2, WSe2, NbS2, TaS2, TiAl, Bi2Te3, Bi2Se3, CaF2, LiF) with root causes.

## Example advisory tips (in `advisor_example_tips_v1.json`)
Every tip carries `tip_type, material, evidence_level, n_supporting_runs, confidence, recommendation, reason`.
1. **MgO** — donor_start, Level A, high: warm-start from `917b3bea`/`1858f32c`, Broyden target (6 vs 178 iters).
2. **NaCl** — donor_start, Level A, high: warm-start from `68ccf55e`/`cb742fd6` (2 vs 171 iters, Broyden).
3. **Si/Ge** — donor_start, Level A, high: warm-start from the empty-sphere donors (2–3 vs 117–119), ES explicit.
4. **TiSe2** — donor_start, Level A, **medium**: coarse-contour donor + single-segment gentle mixing (fine
   destabilizes the semimetal).
5. **Fe/Ni/Co** — donor_start, Level A, high: magnetic (NSPIN=2, LINIPOL) warm-start (5–6 vs ~131–136).
6. **Au/W/Pt/Sb/Pb** — donor_start, Level A, high: heavy-SOC warm-start with the certified recipe (NCHEB=12 +
   `<USE_CHEBYCHEV_SOLVER>`, R_LOG 0.6/0.8, voronoi Cheby-free); 2–3 vs 122–136.
7. **WSe2** — **unsafe_warning** (parked): no donor; SCF unstable (contour/EMIN) + ~70 min/iter; process paused.
8. **MoS2** — **unsafe_warning** (parked): MP0 rhombohedral AND conventional cells both NACLSD (1502/1615).

## Safety discipline (unchanged)
Advisory-by-default; donor tips only for **E1-CERTIFIED same-structure** donors (never a guessed/uncertified
donor, never CPA/BdG); parked materials emit warnings, never "safe" tips; no cross-material strong claims;
confidence scales with evidence level × #donors × warm-start measurement. **Not deployed** — the installed
daemon package is unchanged; this index is an offline artifact for a future gated install.
