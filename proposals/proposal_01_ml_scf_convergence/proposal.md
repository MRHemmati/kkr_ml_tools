# Proposal 01 — ML-accelerated SCF convergence for KKR-BdG, with an AiiDA-native ML-in-the-loop restart protocol

## Title
**Learning to converge: data-driven prediction and acceleration of self-consistent
KKR-BdG Green-function calculations across impurity chemistries.**

## Short abstract
Self-consistent-field (SCF) convergence of all-electron KKR / KKR-BdG Green-function
calculations is expensive (hours–days on many cores) and fragile (mixing-dependent
oscillation, Broyden poisoning, late blow-ups). Using a provenance-complete AiiDA database of
hundreds of NbSe₂-based SCF runs, we build static (KRR/XGBoost) and sequential (LSTM) models
that predict, from the early RMS-error trajectory and input parameters, how many further
iterations a run needs — and we embed the best predictor as an AiiDA `@calcfunction` inside a
closed-loop `MLRestartProtocol` workflow that adapts the mixing scheme on the fly. We report
honest **leave-one-dopant-out (LODO)** transferability (strong for Mn/Co/V, failing for Fe) and
demonstrate a provenance-recorded ML-in-the-loop prototype.

## Scientific motivation
- KKR-BdG SCF is the rate-limiting step in high-throughput superconductor screening; per-iteration
  cost for large slabs is ~tens of minutes (help2: ~27 min/iter for an 84-atom NbBi slab).
- Convergence outcome is dominated by *controllable* knobs (`IMIX`, `STRMIX`/`BRYMIX`,
  `NSIMPLEMIXFIRST`, `MIXFAC_BDG`) and by start-potential quality — exactly the features a model
  can see *before/early* in a run. Predicting "will this converge / how many more iterations"
  enables early stopping and adaptive restart, saving large amounts of compute.
- ML-for-convergence is an active niche (active learning, surrogate SCF mixers); doing it on a
  **fully provenance-tracked** dataset with a **deployable AiiDA workflow** is a distinguishing angle.

## Dataset — corrected two-study design (verified 2026-06-26) — [FACT]
A run is labeled BdG only if `<USE_BDG>=True` AND `<AT_SCALE_BDG>` has a nonzero entry AND
`<LAMBDA_BDG>>0` (the flag alone mislabels ~273 of 1,603 `KkrCalculation`s). Re-deriving on the
sequence reservoir (3,405 SCF runs with RMS trajectories) corrected ~330 labels — including **206
genuine BdG runs that were hidden in the "normal" bucket** and 124 false-BdG. Corrected split:

| | Study A — normal KKR | Study B — KKR-BdG |
|---|---:|---:|
| runs | **2,541** | **864** |
| converged (final_rms<1e-6) | 1,782 | 745 |
| median iters (converged) | 93 | 59 |
| key feature spread | mixing/k-mesh/T | λ_BdG 1e-4→0.3 (peak 0.024/0.032/0.039), MIXFAC_BDG, AT_SCALE pattern |

Three modeling tracks: (A) normal-state predictor, (B) BdG predictor, (C) **cross-regime transfer**
(train normal → test BdG). Plus LODO chemistry transfer within each. *The pre-2026-06 LSTM/KRR LODO
numbers below were computed on the OLD (contaminated) split and must be recomputed on the corrected one.*

## Existing calculations that support this proposal — [FACT]
- **Dataset:** `kkr_scf_metadata.csv` (705 workchains, 382 converged / 323 not),
  `rms_sequences_*.pkl`, `kkr_scf_full_dataset.pkl.gz`, precomputed `X_soap/X_pot/X_full_krr.npy`,
  targets `y_iters/y_log.npy`, splits `lodo_indices.npy`, masks `kkr_scf_masks.pkl`.
- **Models already trained:** KRR/XGBoost LODO (`krr_lodo_results*.pkl`, `xgb_*`), LSTM with
  per-dopant folds (`lstm_fold_{V,Mn,Fe,Co}.pt`, `lstm_*`), diagnostics (`eda_*.png`,
  `xgb_shap_summary.png`, `potential_sanity_check.png`).
- **Deployment code:** `aiida_predict.py` (`@calcfunction` LSTM predictor),
  `workchains/ml_restart_protocol.py` (`MLRestartProtocol` WorkChain).

## Relevant AiiDA nodes / groups / workflows / calcjobs — [FACT]
- WorkChains: `kkr_scf_wc` (780 in DB), `MLRestartProtocol` (17 runs, 2026-05),
  `KkrWorkChainWithMLMixing` (14 runs). CalcJobs: `KkrCalculation` (5,646; rich exit-code spectrum:
  4,538 exit-0, 471 exit-302, 202 exit-120, 187 killed).
- Model artifact in DB: PK 103667 (`NbBi_kkr35_linear_capture50`).
- The 705-row CSV is a 1:1 census of `kkr_scf_wc`; full provenance UUIDs are recoverable.

## Physics/CS question it answers
*Can the convergence cost and outcome of a KKR-BdG SCF run be predicted from cheap, a-priori-
or-early-available information, well enough to drive an adaptive restart policy — and does such a
predictor transfer across impurity chemistries it never saw in training?*

## What is already done — [FACT]
- End-to-end dataset extraction, feature engineering (SOAP + potential + tabular kkrparams),
  static and sequential models, LODO evaluation, SHAP analysis.
- LSTM LODO results (predict remaining iterations from early RMS window):
  **MAE Mn 49.8 / Co 57.5 / V 79.4 / Fe 97.6 iters** vs naive ~167 → **+54% / +21% / +7% / −18%**.
- Observation-window sweep (best at 5 steps ≈ +8% mean) → early prediction is feasible.

**Corrected Study A results (2026-06-26, RandomForest, first-10-iters features, LODO):**
- **Convergence classifier (will-it-converge): AUC 0.956/0.965/1.00/0.896 for held-out Fe/V/Mn/Co**
  (accuracy 0.88/0.93/0.93/0.86 vs base 0.57/0.52/0.86/0.81) — strong transfer to all four chemistries.
- Iterations-to-converge regression: improvement over naive +8.6/+3.3/+44.5/+50.8% (Fe/V/Mn/Co);
  **Fe is now positive (+8.6%)** — the prior −18% was a contaminated-split artifact.
- Files: `workspace/analysis/study_a_train.py`, `…/study_data/study_a_results.md`.

**PROSPECTIVE VALIDATION (live cluster, 2026-06-29) — the key result:** 24 NEW kkr_scf_wc runs
submitted to th1-2020-64 *after* the model was frozen (structure A = Nb2Se4X2, 24 mixing settings,
12-node rolling backfill); 22 reached a clean outcome (2 highest-strmix runs NaN-diverged and
zombie-hung to the 24h walltime → killed; their early iters would have been flagged by the model —
a textbook early-abort case worth ~48 wasted node-hours). On the 22: **prospective AUC = 0.967**
(balanced 11 conv / 11 non-conv), confusion @0.5 TP=11/TN=10/FP=1/FN=0 → failure recall 0.91,
precision 1.00; only miss = a too-conservative strmix=0.01 run. **Early-abort would have recovered
61.7% of the grid's SCF iterations.** The prospective AUC matches the retrospective ~0.96 → the model
generalizes to new runs, and reproduced the physical convergence window (strmix≈0.015–0.04) unseen.
Files: `workspace/submit/{submit_grid_wave,backfill_grid}.py`, `workspace/analysis/{extract_grid_runs,predict_grid}.py`,
`study_data/prospective_grid_results.md`. CAVEAT: single structure (probes the mixing→convergence axis;
multi-structure/doped follow-up needed for breadth).

**VALIDATION (2026-06-26) — leakage check + bootstrap CIs:**
- *No leakage* (`study_c`): impurity + permutation importance both rank early-trajectory features
  (log-RMS min/last/mean, charge-neutrality) on top; missing-data flags rank last; trajectory-only
  LODO AUC ≈ all-features AUC. The classifier is physics-driven.
- *Bootstrap 95% CIs* (`study_b`, 1000 resamples): classifier AUC **Fe 0.957 [0.934,0.978]**,
  **V 0.964 [0.927,0.991]** (tight; failure-class recall 0.94 / 0.93) — robust on the large classes.
  Mn/Co wide CIs (Co [0.69,1.00]) — underpowered, report-don't-headline. Iteration-regression
  improvement significant only for Fe +8.6% [3.8,14.0], Mn +45% [29,63], Co +51% [30,71]; V not
  significant (+2.9% [-12.5,17.1]). Cross-regime: classifier AUC 0.679 [0.619,0.738], iteration MAE
  36.8 [33.5,39.9]. → **publishable core confirmed** (chemistry-transfer classifier on Fe/V + the
  cost-vs-outcome dissociation).

**Cross-regime transfer (normal → BdG) — the novel headline (2026-06-26):** a clean dissociation —
convergence **cost transfers** (train-normal→test-BdG iteration MAE 36.9, beats BdG's own median 42.2),
but convergence **outcome does NOT** (cross-regime AUC 0.68 vs within-BdG 0.93; cross-regime accuracy
0.83 < base rate 0.87). ⇒ a shared cost model but regime-specific outcome models; physically, BdG
pairing-channel instabilities are absent from normal-state training. Files:
`workspace/analysis/cross_regime_transfer.py`, `…/study_data/cross_regime_results.md`.
- The predictor was wrapped as a provenance-preserving `@calcfunction` and embedded in a WorkChain
  that actually executed in AiiDA (17 runs).

## What is missing — [OPEN]
- The closed-loop `MLRestartProtocol` **does not yet succeed** (10/17 excepted, 5 exit-401). Needs
  debugging (read `verdi process report` first; root-cause the SCF-failed / exception path).
- `USE_BDG` is null for most CSV rows and the dataset mixes material families → re-derive BdG flag
  and add `system_family`; recompute NbSe₂-only LODO to remove confounds.
- Calibrated uncertainty on predictions (the restart policy uses a hard threshold) and a clean
  ablation (static vs sequential vs hybrid).

## Additional calculations that may be needed later
- **(needs approval — submits jobs)** Debug and re-run ~10 `MLRestartProtocol` loops to obtain a
  handful of clean closed-loop successes (turns a "prototype" into a "working accelerator").
- Optionally a small held-out validation campaign on a *new* dopant to test true extrapolation.

## Possible figures
1. LODO MAE vs naive baseline, per held-out dopant (bar chart; the Fe failure is the honest highlight).
2. RMS-trajectory gallery, colored by outcome class (converged / plateau / Broyden-oscillation /
   late blow-up).
3. Accuracy vs observation-window length.
4. SHAP feature-importance summary (IMIX, STRMIX/BRYMIX, MIXFAC_BDG, start-potential quality).
5. Schematic + real provenance graph of the `MLRestartProtocol` closed loop.

## Possible tables
- Dataset composition (per dopant / per system-family / converged vs not).
- Model comparison: KRR vs XGBoost vs LSTM, per-dopant LODO MAE/RMSE + uncertainty.
- Closed-loop prototype outcomes (status of the 17 runs, before/after debugging).

## Possible paper outline
Intro → Dataset & LODO protocol → Static vs sequential models → Transferability results (incl. Fe
failure) → Early-prediction window study → ML-in-the-loop workflow (prototype) → Reproducibility
(released dataset, code, UUIDs) → Discussion.

## Feasibility
**High.** ~70% complete from existing artifacts; the remaining work is analysis, de-confounding,
figures, and (optionally) debugging the loop. No new compute strictly required for a first submission.

## Risk level
**Low–Medium.** Main risk is that headline numbers shift after de-confounding (NbSe₂-only) — but a
slightly smaller, cleaner claim is still publishable. The closed-loop debugging is the only
compute-dependent piece and can be framed as a prototype if not finished.

## Publication potential
**Strong** for an ML-for-materials / computational-methods venue
(e.g. *npj Computational Materials*, *Machine Learning: Sci. & Technol.*, *Computer Physics
Communications*, *J. Chem. Theory Comput.*). The novelty is the **provenance-native ML-in-the-loop
SCF accelerator**, not just an offline predictor.

## Suggested next steps
1. Read `phase3.ipynb` / `Phase 4.ipynb` to reproduce the current numbers.
2. Re-derive `USE_BDG` + `system_family`; rerun NbSe₂-only LODO (read-only scripts in `workspace/`).
3. `verdi process report` on excepted `MLRestartProtocol` PKs (100992–101281) to diagnose the loop.
4. Produce the five figures from existing data.
5. Decide whether to invest in debugging + re-running the closed loop (requires job submission, your call).
