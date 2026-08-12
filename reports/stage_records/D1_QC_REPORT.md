# D1-QC — validation of the held-out replay result (offline, read-only) — 2026-07-21

**Offline / read-only.** No submissions, daemon/package changes, DB writes, labels/extras/groups, job
actions, or node modification. Inputs: the D1 cohort file (`workspace/models/d1_heldout_cohort.pkl`) +
frozen-model scores (`report/d1_scores.csv`), analysed in the venv (`workspace/analysis/d1_qc.py`).
Model weights UNCHANGED (frozen `mlassist_v1_normal_fixed10`, sha `cebe56b9…`). Artifacts:
`report/d1_qc_metrics.json`, `report/d1_figures/d1_qc_summary.pdf`.

## BOTTOM LINE — the D1 headline was directionally right but **overstated**; several of its numbers are artifacts.
QC finds three confounds that inflated the "trivial RMS baseline crushes ML" story, and one finding that
holds up. Net: **on the deployment-relevant cohort (cold-start, same convergence target) neither method is
strong, the two are competitive, and per-cohort conformal recalibration DOES restore false-abort control**
(the α=0.10 violation was a non-transported-seed artifact, not a fundamental failure). One genuine ML
weakness confirmed: a real cross-material transfer inversion on other-KKR.

---

## 1. Baseline fairness — CONFIRMED fair on the window; RMS@10 has a deployment-only earlier-decision edge
- **Same window:** the frozen model uses `rms[:10]`; RMS@10 = `rms[9]`; RMS-slope = slope of `log rms[:10]`.
  All three consume the **identical first-10-iter information**. The "≥12 iters" rule is only a *scoring
  gate* (all 336 pass), not extra signal. → retrospectively the comparison is fair.
- **Horizon recompute:** RMS@10 AUC **0.925**, RMS@12 **0.926**, RMS@20 **0.907** (n=252 reach iter 20).
  The frozen ML model is **fixed at T=10** and cannot be re-horizoned without retraining.
- **Earlier-decision advantage (real, deployment-side):** in production with `nsteps=10` segments, ML's
  first score lands at **cumulative iter 20** (needs ≥12 obs → 2 segments), whereas an RMS@10 rule could
  fire at **iter 10**. So RMS@10 additionally decides ~10 iters sooner live — a second advantage on top of
  the discrimination numbers. This should be stated whenever the two are compared.

## 2. Cohort sanity — **RMS@10's dominance is largely a warm/cold composition artifact** ⚠️
- **Warm vs cold split (proxy: first-iter RMS):** 105 runs start at rms₀<1e-2 (warm/restart-like), 231
  start cold (rms₀≥1e-2). Converged-rate: **warm 0.78 vs cold 0.05.** The starting RMS alone almost
  determines the outcome — the cohort is a *mixture of two populations*.
- **RMS@10 AUC decomposed:** pooled **0.925**, but **cold-only 0.559**, warm-only 0.826. → RMS@10's high
  pooled AUC mostly reflects that it can tell a warm run from a cold one (rms@10 ≈ rms₀ ranking), **not**
  that it predicts convergence within the population you actually deploy on. **On cold starts alone RMS@10
  is barely above chance.**
- **ML AUC decomposed:** cold-only 0.580, warm-only 0.537 — also weak within-population. → *Both methods
  are weak (~0.56–0.58) on a homogeneous cold-start cohort;* the large pooled gap between them shrinks once
  you stop rewarding warm/cold separation.
- **Stratified AUC (ML | RMS@10):** family NbSe₂ 0.86|0.97, Bi 0.88|1.0, unknown 0.82|0.83, other-KKR
  **0.19**|0.80; partition th1-2020-64 0.87|0.98, **th1-2020-32 0.49|0.82**; code kkrhost_3.5_AMD 0.88|0.96,
  **kkrhost_BdG_AMD 0.44|0.84** (BdG runs scored with the *normal* model — a model/regime mismatch, not a
  fair test). qbound=0.008 stratum (210 runs) has **0 "converged"** under the fixed label → AUC undefined,
  which is the label problem of §3 leaking into every pooled number.

## 3. Label sanity — **the fixed-1e-3 rule mislabels 57 runs and inflates the RMS@10 gap** ⚠️
- D1 labeled outcome by a **fixed** cut (CONVERGED if final rms<1e-3), but per-run **QBOUND varies**:
  0.008 (210 runs), 1e-5 (39), 1e-6 (33), 1e-8 (45), None (7). A NbSe₂ run reaching rms 0.0078 with its own
  QBOUND=0.008 **met its convergence criterion** yet was labeled STALL; conversely some rms 4e-5 runs with
  QBOUND=1e-6 were labeled CONVERGED though they missed their own target.
- **57 runs flip** converged/failed under per-run QBOUND vs fixed 1e-3; converged count **94 → 115**.
- **Effect on the headline:** under per-run QBOUND labels **RMS@10 AUC drops 0.925 → 0.844**, while
  **ML barely moves 0.760 → 0.777.** → roughly *half of RMS@10's apparent margin over ML was a label-rule
  artifact.*
- **Censored/ambiguous listed separately:** 15 runs have exit_status ∉ {0, None} (11×302, 4×120) — these
  are non-clean terminations that should not be scored as outcomes: pk 26, 17, 132, 462, 16082, 16256,
  16324, 16373, 16495, 16663, 16672, 16883, 16891, 25556, 25895. 130 runs sit within a factor 3 of their
  own QBOUND (borderline); 7 have QBOUND=None. **Recommendation: adopt per-run QBOUND labels, drop the 15
  censored, and treat the borderline band explicitly before any published number.**

## 4. Other-KKR anti-predictive audit — **REAL model transfer failure, not an artifact**
- Within other-KKR: **RMS@10 AUC = 0.80 (works)** but **ML AUC = 0.19 (inverted).** Since the *same early
  RMS* is predictive there (RMS@10 fine), the inversion is **specific to the ML model**, i.e. a genuine
  feature/dynamics mismatch — not a label or extraction bug.
- **Mechanism (representative rows):** other-KKR convergers start *high and descend slowly*
  (pk 99954: rms₀=0.47, rms@10=0.30 → converges to 8e-9, QBOUND=1e-8) but the model, trained on
  fast-converging NbSe₂, reads "high early RMS ⇒ won't converge" and scores them **low** (p=0.39). Diverging
  other-KKR runs that happen to start lower (pk 105850: rms@10=0.23 → diverges) get scored **high** (p=0.98).
  The model has the family backwards. → confirms **no cross-material transfer for the ML model**; the
  physics of "slow-but-successful" descent is outside its NbSe₂ training manifold.
- Caveat: part of the other-KKR / BdG-code bucket is BdG runs scored with the *normal* model (§2) — an
  additional, avoidable mismatch. The honest scope statement is **NbSe₂-family, normal-state**.

## 5. Risk-savings curves — operating-point dependent; ML is competitive/better at conservative α
Sweeping each score's threshold (abort horizon = deployment iter 20; saved = failed-run iters beyond 20):

| target false-abort | ML: FA / recall / saved | RMS@10: FA / recall / saved |
|---|---|---|
| ≤0.05 | 0.043 / **0.471** / 54% | 0.021 / 0.227 / 23% |
| ≤0.10 | 0.074 / 0.661 / 85% | 0.096 / **0.938** / 89% |
| ≤0.20 | 0.138 / 0.686 / 86% | 0.181 / **0.955** / 92% |

- **At the strict, deployment-realistic α≤0.05 the ML model has HIGHER failure-recall than RMS@10
  (0.47 vs 0.23)** and saves more (54% vs 23%). RMS@10 only overtakes at looser α≥0.10, where it recovers
  almost all doomed-run iterations. → the "baseline wins" claim is true only at permissive false-abort
  budgets; at the conservative budget you'd actually deploy, ML is the better operating point.

## 6. Recalibration simulation — **per-cohort recalibration RESTORES false-abort control** (weights frozen)
Nested split-conformal on THIS cohort (one-sided; calibrate τ on a held-out half of converged runs;
400 bootstrap splits; **model weights never touched**):

| α | ML: realized-FA (mean / p95) · recall · saved | RMS@10: realized-FA · recall · saved |
|---|---|---|
| 0.05 | 0.051 / 0.149 · **0.488** · 57% | 0.056 / 0.149 · 0.421 · 41% |
| 0.10 | 0.098 / 0.213 · 0.640 · 81% | 0.100 / 0.214 · **0.804** · 78% |
| 0.20 | 0.155 / 0.213 · 0.686 · 86% | 0.207 / 0.340 · **0.953** · 93% |

- **The D1 false-abort of 0.468 was a non-transported-seed artifact, not a fundamental failure.** Once the
  conformal threshold is re-derived from the deployment cohort, realized false-abort tracks the target
  (0.05→0.051, 0.10→0.098) for **both** policies. Conformal control is a *per-cohort calibration* property,
  exactly as the theory says — it does not transport a NbSe₂-seeded threshold, but it is recoverable.
- **After honest recalibration the two policies are competitive:** ML is **better at α=0.05** (recall 0.49
  vs 0.42), RMS@10 is better at α≥0.10. Neither is a clear universal winner.
- **Usable control + useful savings is achievable for both** — but only with per-cohort calibration and
  (from §2) only modest discrimination on cold starts. A simple, strong deployable candidate is **RMS@10 at
  a conformally-calibrated threshold**; the ML model earns its place mainly at conservative α on NbSe₂.

---

## Revised claim discipline (supersedes the sharper D1 phrasing where noted)
- **What HELD from D1:** the frozen NbSe₂-seeded conformal threshold does **not** transport (false-abort
  0.47 at the seeded α=0.10); the ML model does **not** transfer across materials (other-KKR AUC 0.19, now
  shown to be a real model inversion); late stalls remain the hard case. Deployment must be per-cohort and
  scope-limited.
- **What QC CORRECTED / SOFTENED:** the "RMS@10 (0.925) crushes ML (0.760)" gap is inflated by (i) a
  warm/cold *cohort-composition* artifact — cold-only both ≈0.56–0.58, and (ii) a *label-rule* artifact —
  correct per-QBOUND labels drop RMS@10 to 0.844 while ML rises to 0.777. On the deployment-relevant
  cold-start cohort **neither method is strong and the two are competitive**; **ML is actually the better
  operating point at conservative α=0.05**; and **per-cohort recalibration restores false-abort control**.
- **NOT CLAIMED:** no prospective claim; no assertion that ML beats RMS@10 in general (it doesn't, at loose
  α) nor that RMS@10 beats ML in general (it doesn't, at strict α); no cross-material claim.

## Recommendations for D2 (no action taken)
1. **Re-run D1 metrics on clean labels** (per-run QBOUND, drop the 15 censored, flag the borderline band) —
   the headline should be reported on the corrected labels.
2. **Report cold-start-only and per-QBOUND-stratum AUCs**, not just pooled — the pooled number conflates
   warm/cold populations and is not the deployment metric.
3. **Always calibrate conformal per-cohort;** benchmark the ML policy against a conformally-calibrated
   **RMS@10** rule at matched α — that is the real baseline to beat, and ML must justify itself at
   conservative α on NbSe₂.
4. **Scope the ML model to NbSe₂-family normal-state;** score BdG with the BdG model, never the normal one.
5. **Late-stall detection** (recall 0.36 in D1) remains the primary modeling gap for both methods.

## AUDIT LINE
D1-QC was **offline / read-only**: it re-used the existing cohort pickle + scores CSV and ran local venv
analysis. **No AiiDA queries, no submissions, no daemon/package changes, no DB writes, no labels/extras/
groups, no job actions, no node modification.** Stopped after this report + `report/d1_qc_metrics.json` +
`report/d1_figures/d1_qc_summary.pdf`. **No prospective submissions.**
