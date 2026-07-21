# D1b — Clean held-out benchmark (corrected rules, per-cohort) — 2026-07-21

**Offline / read-only.** No submissions, daemon/package changes, DB writes, labels/extras/groups, job
actions, or node modification. Re-uses the D1 cohort pickle + frozen-model scores; analysis in the venv
(`workspace/analysis/d1b_benchmark.py`). Frozen model `mlassist_v1_normal_fixed10` sha `cebe56b9…`,
**weights UNCHANGED**. Artifacts: `report/d1b_metrics.json`, `report/d1b_scores.csv` (per-run corrected
labels), `report/d1_figures/d1b_percohort.pdf`.

## Corrected rules applied (vs D1)
1. **Labels = per-run QBOUND** (converged ⇔ final rms < that run's QBOUND), not a fixed 1e-3.
2. **15 censored/excepted runs dropped** from all denominators (exit_status ∉ {0, None}: 11×302, 4×120).
3. **Runs with QBOUND=None dropped** from labelled metrics (7 runs; listed in the CSV).
4. **Borderline runs** (final rms within a factor 3 of own QBOUND) **tracked separately**, with an
   include/exclude sensitivity per cohort.
5. **No single pooled headline** — every number below is per-cohort. Primary vs secondary kept distinct.
6. Comparators: frozen **ML** vs **RMS@10** vs **RMS-slope**, plus **per-cohort conformally-recalibrated**
   ML and RMS@10 at α ∈ {0.05, 0.10, 0.20}. Bootstrap 95% CIs (1000×) for AUC.

## Retrospective window vs deployment timing (read before the numbers)
- **Retrospective (the AUC/recall tables):** ML, RMS@10 and RMS-slope all consume the **same first-10-iter
  window** — a fair discrimination comparison.
- **Deployment timing:** with `nsteps=10` segments the ML wrapper's **first score is at cumulative iter 20**
  (needs ≥12 obs across 2 segments), whereas an RMS@10 rule can fire at **iter 10**. So in production RMS@10
  additionally decides ~10 iterations earlier. Savings numbers below charge the abort at iter 20 for both,
  which is conservative for RMS@10.

---

## PRIMARY COHORT — NbSe₂-family, normal-state (the deployment target)
Leakage-clean, non-censored, QBOUND-labelled. n=167 (converged 38), of which 128 cold / 39 warm; 56 borderline.

| sub-cohort | n | conv | ML AUC | RMS@10 AUC | RMS-slope AUC |
|---|---|---|---|---|---|
| **all** | 167 | 38 | 0.831 [0.77, 0.89] | **0.897 [0.85, 0.94]** | 0.740 [0.65, 0.83] |
| **cold** (deployment-realistic) | 128 | 12 | 0.785 [0.68, 0.88] | **0.901 [0.80, 0.97]** | 0.568 [0.43, 0.69] |
| warm | 39 | 26 | 0.430 [0.24, 0.63] | 0.414 [0.24, 0.60] | 0.467 [0.27, 0.65] |

**Headline (honest): on the primary cohort RMS@10 is the stronger predictor and the frozen ML model does
NOT beat it** — at all three α after per-cohort recalibration:

| α | ML: FA / recall / prec / saved | RMS@10: FA / recall / prec / saved |
|---|---|---|
| primary-all 0.05 | 0.036 / 0.53 / 0.99 / 0.54 | 0.039 / **0.64** / 0.99 / **0.61** |
| primary-all 0.10 | 0.096 / 0.62 / 0.98 / 0.62 | 0.100 / **0.78** / 0.98 / **0.73** |
| primary-all 0.20 | 0.196 / 0.71 / 0.96 / 0.69 | 0.186 / **0.86** / 0.97 / **0.81** |
| cold-only 0.10 | 0.086 / 0.58 / 0.99 / 0.60 | 0.090 / **0.69** / 1.00 / **0.68** |

- The pooled "ML better at α=0.05" from D1-QC was itself a *pooled-cohort artifact*; on the clean primary
  cohort **RMS@10 ≥ ML at every α** (higher recall and savings at matched false-abort).
- **Per-cohort recalibration controls false-abort** for both (realized FA ≈ target: 0.036/0.096/0.196 ML;
  0.039/0.100/0.186 RMS@10) — the D1 α-violation was a non-transported-seed artifact, and it is fixable.
- **Warm sub-cohort is near-chance for both** (few failures among warm/restart runs); recall collapses to
  ~0 — the early window cannot discriminate the rare warm failures. Warm runs should be handled by a
  different (or no) abort rule.
- **Borderline sensitivity (primary-all):** excluding the 56 borderline runs, ML AUC 0.831→0.847,
  RMS@10 0.897→0.913 — the ranking and gap are unchanged, so the conclusion is not driven by borderline
  cases (full excl-border AUCs in `d1b_metrics.json`).
- **Rare-positive caveat:** cold NbSe₂ converges at only 12/128 at these hard fixed settings; CIs are wide
  (ML cold [0.68,0.88]). The primary conclusion (RMS@10 ≥ ML) is directional but not razor-sharp on cold
  alone; it is firm on the 167-run primary-all.

---

## SECONDARY COHORTS (reported separately — NOT pooled into the primary)

| cohort | n | conv | ML AUC | RMS@10 AUC | reading |
|---|---|---|---|---|---|
| Bi/NbBi | 28 | 21 | 0.898 [0.75, 1.0] | 0.939 [0.84, 1.0] | both good; RMS@10 slightly ahead |
| **other-KKR** | 45 | 34 | **0.476 [0.29, 0.68]** | 0.904 [0.78, 1.0] | **ML ≈ chance/inverted — real cross-material transfer failure; RMS@10 fine** |
| BdG-misfit (normal model on BdG) | 78 | 41 | 0.581 [0.44, 0.70] | 0.813 [0.70, 0.91] | normal model mis-applied to BdG — weak; **score BdG with the BdG model, never this one** |
| unknown | 42 | 10 | 0.800 [0.65, 0.93] | 0.778 [0.55, 0.95] | one of the few cohorts where ML ≈ or > RMS@10 (small, noisy) |
| warm/restart-like (all fam) | 93 | 67 | 0.350 [0.24, 0.47] | 0.606 [0.49, 0.72] | **ML anti-predictive on warm runs**; RMS@10 modest |

Recalibrated operating points per secondary cohort are in `d1b_metrics.json`. Notable:
- **other-KKR:** recalibrated ML recall stays ≤0.18 at all α (ML cannot catch its failures) while RMS@10
  reaches recall 0.69 @α=0.10 — the transfer failure is a *model* property, not a data artifact (RMS@10
  works on the same runs).
- **unknown:** recalibrated ML recall 0.60–0.61 vs RMS@10 0.31–0.35 across α — the one cohort where the ML
  model adds value over RMS@10, but n=42/conv=10 is too small to lean on.
- **warm/restart & warm NbSe₂:** recall ≈ 0 for both methods — early-window abort is inapplicable to warm
  starts; they should be excluded from the abort policy or given their own rule.

---

## What this means (per-cohort, honest)
1. **On the deployment target (NbSe₂ normal-state, cold), the frozen ML model does not beat a
   conformally-calibrated RMS@10 rule** — RMS@10 has higher AUC and higher recall at matched false-abort at
   every α. The ML model is *usable* (per-cohort recalibrated, false-abort controlled, precision ≥0.98) but
   it is **not the best simple option** here.
2. **Conformal false-abort control is recoverable per-cohort** for both methods (the D1 0.468 violation was
   a seed-transport artifact). Any deployment MUST recalibrate on the target cohort.
3. **No cross-material transfer** for the ML model (other-KKR AUC 0.48; warm/restart 0.35) — confirmed on
   clean labels; scope any ML claim to NbSe₂-family normal-state.
4. **BdG runs must be scored with the BdG model**; the normal model on BdG (AUC 0.58) is a scope error.
5. **Warm/restart runs are outside the abort policy's competence** (both methods) — carve them out.
6. **The strongest honest deployable is RMS@10 + per-cohort conformal calibration;** the ML model earns a
   place only in narrow, well-calibrated NbSe₂ regimes, and even there must be justified against RMS@10.

## Claim discipline (three levels, unchanged in kind, corrected in magnitude)
- **Retrospective held-out (this benchmark):** per-cohort; **ML ≤ RMS@10 on the primary cohort**; ML
  transfer-fails on other-KKR/warm; conformal control recoverable per-cohort. Not a broad ML-superiority
  result.
- **Live Fe-only pilot (C1/C2):** the abort *mechanism* works end-to-end (S5 true abort). Machinery, not
  generalization.
- **Prospective:** NOT claimed; and this benchmark says any prospective deployment needs per-cohort
  calibration + an RMS@10 comparator.

## AUDIT LINE
D1b was **offline / read-only**: reused existing cohort pickle + scores CSV; local venv analysis only.
**No AiiDA queries, no submissions, no daemon/package changes, no DB writes, no labels/extras/groups, no
job actions, no node modification.** Stopped after this report + `report/d1b_metrics.json` +
`report/d1b_scores.csv` + `report/d1_figures/d1b_percohort.pdf`. **No prospective submissions.**
