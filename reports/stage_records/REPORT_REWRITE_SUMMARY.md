# REPORT_REWRITE_SUMMARY.md — report/main.tex rewrite after D1/D1-QC/D1b — 2026-07-21

Documentation/report task. **No AiiDA, no submissions, no daemon/package/DB changes, no compute campaign.**
Only `report/main.tex` + a local figure script edited; figures regenerated from existing D1b/D1-QC
artifacts; PDF compiled.

## Files changed
| file | action |
|---|---|
| `report/main.tex.bak.20260721-154938` | **timestamped backup** of the pre-rewrite tex (bit-for-bit revert anchor) |
| `report/main.tex` | rewritten (title, abstract, tooling, classifier, **new held-out §**, conformal transport §, deployment §, **new live-pilot §**, BdG scope, 4 tables, roadmap, provenance) |
| `report/make_figures_d1b.py` | **new** local figure script (venv matplotlib; reads `d1b_metrics.json` + `d1_qc_metrics.json`) |
| `report/figures/figD1_percohort.pdf` | **new** — per-cohort ML vs RMS@10 AUC (held-out, CIs) |
| `report/figures/figD2_calibrated_savings.pdf` | **new** — calibrated recall & savings vs α, primary cohort |
| `report/figures/figD3_transport_recal.pdf` | **new** — seeded-threshold 0.47 vs per-cohort recalibrated ≈ α |
| `report/figures/figD4_pilot.pdf` | **new** — live pilot S5 true abort / S1 withheld (schematic of recorded runs) |
| `report/main.pdf` | recompiled (14 pp) |

Retired (no longer referenced; files left in place, not deleted): `fig3_prospective_coldstart.pdf`,
`fig4_recovery_vs_alpha.pdf`.

## Stale claims removed / scoped (rewrite rules 1–9)
- **"The model beats all baselines" — REMOVED** (was classifier §). Replaced by the honest held-out
  statement (RMS@10 ≥ ML on the primary cohort). Verified absent from the tex.
- **AUC 0.944 demoted to in-distribution 5-fold — never the headline.** Every occurrence now explicitly
  labelled in-distribution (classifier §, Table `permaterial` + footnote 3, Table `baselines` shown beside
  held-out 0.831, provenance Table footnote 4).
- **Leads with the held-out per-cohort result** (new §"The held-out benchmark", Table `percohort`,
  Fig `percohort`): primary NbSe₂-normal ML 0.83 [0.77,0.89] (cold 0.79); RMS@10 0.90 [0.85,0.94]; RMS@10
  beats ML at matched calibrated α (Table `g1`, Fig `savings`).
- **Conformal stated carefully** (new transport paragraph + Fig `transport`): seeded thresholds do NOT
  transport (realized false-abort 0.47); per-cohort recalibration restores realized ≈ α; the guarantee
  depends on calibration/test exchangeability. The old **"transports prospectively" claim removed**
  (verified absent).
- **Prospective false-abort 0.000 reframed narrow**: now "single-material, in-distribution," explicitly
  paired with the 0.47 counter-number; no longer implies broad safety.
- **Live pilot kept & scoped** (new §"Live pilot"): S5 true abort ~130 iters saved; S1 would-be false abort
  correctly withheld; S3 honest late-stall miss; N=5 descriptive, not powered.
- **Cross-material transfer explicitly disallowed** (held-out §: other-KKR 0.48, warm/restart 0.35; RMS@10
  still works there → real model transfer failure).
- **Warm/restart runs declared outside the abort policy** (both methods ≈ chance) — held-out § scope note.
- **BdG must be scored with the BdG model** (held-out § + BdG §: normal-model-on-BdG AUC 0.58).

## New figures / tables (rewrite rule 10)
- **Table `tab:percohort`** — held-out per-cohort ML vs RMS@10 vs RMS-slope (no pooled headline row).
- **Fig `figD1`** — per-cohort AUC bars with CIs.
- **Fig `figD2`** — calibrated risk-savings (recall + saved iters vs α), primary cohort.
- **Fig `figD3`** — conformal transport (0.47) vs per-cohort recalibration (≈ α).
- **Fig `figD4`** — live pilot S5/S1 exemplars.
- **Table `tab:g1`** — replaced the old pooled G1 table with the calibrated per-cohort ML-vs-RMS@10 table.
- **Table `tab:baselines`** — added a held-out (primary cohort) column showing RMS@10 0.897 > ML 0.831.
- Kept (unchanged): Fig 1 archetypes, Fig 2 (relabelled in-distribution-only), Fig 5 Mondrian, Fig 6 BdG
  memory, Table `permaterial` (relabelled in-distribution), Table `mondrian`.

## Compile status
`pdflatex` ×2 — **exit 0, 14 pages, no errors, no undefined references/citations.** One transient error
(a stray `\\[4pt]` after the `\title{}` box) was fixed. Verification greps: no "beats all baselines", no
"transports prospectively"; all 0.944 in-distribution-scoped; 0.000 scoped narrow + paired with 0.47.

## Remaining caveats
1. **Figures figD1–figD4 are the report's own honest artifacts.** figD4 (pilot) is a *schematic* of the
   recorded S5/S1 trajectories (illustrative shapes; the numbers — P=0.297/0.262, ~130 iters, exit 701 —
   are the real recorded values). figD1–figD3 are computed directly from `d1b_metrics.json` /
   `d1_qc_metrics.json`.
2. **Cold-start primary cohort is rare-positive** (12/128 converged): the RMS@10 ≥ ML conclusion is firm on
   the 167-run primary-all and directional (wide CIs) on cold-only alone — stated in the tex.
3. **Retired figures** (fig3/fig4) remain on disk but unreferenced; the abstract/prose no longer depend on
   them. They can be deleted in a later pass if desired (not done here — task said no deletions weren't
   required, and they harm nothing).
4. **Sections not restructured into E/S/P/N strands** — that four-strand split is the *paper* outline
   (`REVISED_PAPER_OUTLINE_AFTER_D1b.md`); this technical report keeps its section structure and only
   re-scopes claims per the rewrite rules. If an E/S/P/N contribution list is wanted in the report too, that
   is a further edit (not requested here).
5. **BdG-misfit cohort naming:** the held-out table lists it to justify the "score BdG with the BdG model"
   rule; it is a scope-error demonstration, not a claim about the BdG model itself (which is evaluated
   in-distribution in the BdG §).

## AUDIT LINE
Report/documentation task only. **No AiiDA, no submissions, no daemon/package/DB changes, no
labels/extras/groups, no job actions, no new compute.** Backup taken before editing; PDF compiled;
this summary produced. Stop here.
