# Stage D1 — Held-out replay benchmark (offline, read-only) — 2026-07-21

**Offline / read-only.** No submissions, daemon/package changes, DB writes, labels/extras, or job actions.
Inputs: read-only AiiDA extraction (`d1_extract_cohort.py`) → local cohort file; scoring in the venv
(`d1_replay.py`). Frozen model **`mlassist_v1_normal_fixed10`**, sha256 `cebe56b9f35e49…` — **NO refit,
recalibration, threshold tuning, or α change** (α=0.10, seeded NbSe₂ Mondrian thresholds flat 0.432 /
other 0.825). Artifacts: `report/d1_scores.csv`, `report/d1_metrics.json`, `report/d1_figures/*.pdf`.

## ⚠️ HEADLINE (honest, deflationary): on the held-out cohort the frozen model does NOT beat a trivial RMS baseline, and the conformal false-abort does NOT transport.
This is exactly what evidence expansion is for. The N=5 Fe pilot and the in-distribution AUC 0.944 were
narrow; the n=336 out-of-sample benchmark is much weaker and qualifies the ML value claim.

## 1. Cohort manifest (336 leakage-clean held-out iffslurm runs)
Full per-run manifest in `report/d1_scores.csv` (pk, uuid via cohort pkl, family, outcome, partition, code,
parent wc, n_iters, final rms/chneut, in_training=False). Summary:
- **n = 336**, all with ≥12-iter trajectories, **all pk ∉ training (leakage-clean, verified)**.
- Family: NbSe₂-family 210 · other-KKR 51 · unknown 45 · Bi/NbBi 30.
- Outcome: CONVERGED 94 · STALL 132 · DIVERGE 110 (failed = 242).
- Partition: th1-2020-64 217 · th1-2020-32 97 · oscar 14 · th1 6 · viti 2. BdG: 8.

## 2. Frozen-model replay (exact contract, no tuning)
Features = first-10-iter window (log-RMS stats/slope, charge-neutrality, mixing+missing-flags); score
requires ≥12 observations (first score at cumulative iter 20 under the nsteps=10 framing). Positive class =
converge. Thresholds are the frozen seeded α=0.10 Mondrian values (unchanged).

## 3. Metrics (held-out, bootstrap 95% CIs)
| metric | value |
|---|---|
| **AUC** (P(converge) vs converged) | **0.760** [0.71, 0.81] |
| PR-AUC | 0.442 |
| failed-recall @α=0.10 | 0.463 [0.40, 0.53] |
| **false-abort rate @α=0.10** (converged wrongly aborted) | **0.468** [0.36, 0.56] ⚠️ |
| abort precision | 0.718 |
| early-abort savings (of aborted failed) | 13,505 / 23,917 failed-run iters (56%) |

**The false-abort rate is 0.468, not ≤0.10** — the seeded conformal threshold does NOT provide its α
guarantee on this cohort (exchangeability with the NbSe₂ calibration set is violated). At this operating
point the policy aborts ~47% of runs that would actually converge — unusable as-is on this population.

## 4. Baselines — a simple RMS rule BEATS the ML model out-of-sample
| method | AUC |
|---|---|
| **RMS at window end (rms@iter 10)** | **0.925** |
| RMS log-slope over first 10 | 0.875 |
| frozen ML model | 0.760 |
| last-2-iteration improvement | 0.343 |
| always-continue | recall 0, false-abort 0 |
| always-abort-failed (oracle) | recall 1.0 (upper bound) |
RMS@10 separates outcomes cleanly (converged median 2.3e-4 · stall 3.5e-2 · diverge 2.6e-1), so a trivial
threshold outperforms the frozen model by a wide margin here. **The ML model's value over simple RMS rules
is NOT established out-of-sample on this cohort — it is negative.** (The earlier in-distribution "physics
heuristic 0.55" baseline was a weak strawman; RMS@10 is the strong simple baseline and it wins.)

## 5. Stratification
- **AUC by family:** NbSe₂ **0.86** (210) · Bi/NbBi 0.88 (30) · unknown 0.82 (45) · **other-KKR 0.19 (51)**.
  → On NbSe₂/Bi the model is respectable (though still < RMS@10); on **other-KKR (Nb bulk, Pb₃Te₄:Tl) it is
  ANTI-predictive (AUC 0.19 < 0.5)** — actively wrong, confirming no cross-material transfer.
- **AUC by partition:** th1-2020-64 0.87 (217) · **th1-2020-32 0.49 (~chance, 97)** · oscar 0.67 · th1 0.78.
- **Early-diverge vs late-stall recall (failed runs):** early-diverge recall **0.875** (n=48) vs late-stall
  recall **0.361** (n=194). → Confirms the pilot S3 finding at scale: the model catches early divergence but
  **misses ~64% of late stalls** — the dominant failure mode here.

## 6. Figures / tables (in `report/d1_figures/`)
`d1_roc.pdf` (ROC, AUC 0.76) · `d1_pr.pdf` (PR) · `d1_confusion.pdf` (confusion @α=0.10) · `d1_savings.pdf`
(savings distribution) · `d1_calibration.pdf` (reliability) · family-stratified table (§5). CSV/JSON for
figure regeneration in `report/d1_scores.csv` / `d1_metrics.json`.

## 7. Claim discipline — three distinct evidence levels
- **Retrospective held-out validation (THIS report, n=336):** out-of-sample AUC **0.760**; the model does
  **not** beat a trivial RMS@10 baseline (0.925) and is anti-predictive on other-KKR; the seeded conformal
  false-abort does **not** transport (0.47 vs 0.10 target); late stalls are largely missed (recall 0.36).
  → **The broad out-of-sample value of the ML model over simple RMS rules is NOT supported; deployment as-is
  is not justified by this evidence.**
- **Live Fe-only pilot validation (C1/C2, N=5):** the *mechanism* works live end-to-end (S5 true abort,
  ~130 iters saved); S1 confirmed the false-abort risk; safe under conservative counterfactual gating.
  Descriptive, NbSe₂/Fe-only. → Validates that the *machinery* runs correctly, **not** that the model
  generalizes.
- **Prospective deployment claims:** **NOT MADE.** This held-out evidence argues against a broad prospective
  claim; any future prospective test must (a) benchmark against RMS@10, (b) re-derive per-cohort conformal
  thresholds, and (c) address the late-stall miss.

## Implications / recommendations (for D2 discussion, no action taken)
1. **Benchmark the ML model against RMS@10 everywhere** — it is the real baseline to beat, and currently
   the model does not.
2. **Conformal thresholds must be re-calibrated per deployment cohort** (the NbSe₂ seed does not transport);
   consider whether a well-chosen RMS@10 threshold with a conformal wrapper is a simpler, stronger deployable.
3. **Restrict scope to NbSe₂-family** where the model is at least respectable (0.86) — but even there justify
   it over RMS@10.
4. **Late-stall detection** remains the key modeling gap (recall 0.36).
5. This is a genuine negative result and a contribution: rigorous out-of-sample evaluation deflated an
   in-distribution number, and the honest baseline comparison changes the deployment recommendation.

## AUDIT LINE
D1 was **offline / read-only**: one read-only AiiDA extraction pass + local venv scoring. **No submissions,
no daemon/package changes, no DB writes, no labels/extras/groups, no job actions, no node modification.**
Stopped after the report + CSV/JSON/figure artifacts. **No prospective submissions.**
