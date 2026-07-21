# Pre-registration — shared preamble (ml_assist Phase 3 vehicles)

DRAFT 2026-07-14. NOT FINAL until the reviewer clears the two review-debt items (Δ3-drop rationale
`study_data/phase1_aligned_results.md`; Task-5 G1 report `study_data/phase1_g1_results.md`). Applies to
both Vehicle A (BdG) and Vehicle B (normal-state). Guardrails 1–6 + Δ9 in force.

## Frozen model artifact
- **Normal-state (Vehicle B):** `mlassist_v1_normal_fixed10`, sha256
  `cebe56b9f35e4931069142f8a735ae291eab15796446fc5c3b1f94f6e327f549`, created **2026-07-12T22:24:17**
  (timestamp MUST precede any Phase-3 submission — verify at freeze). RF 400 trees, fixed T_OBS=10
  window, 5-fold OOF AUC 0.944 (n=1830). Pure-numpy artifact + golden parity 0.0 vs sklearn.
- **BdG (Vehicle A):** rms+Δ model frozen at Vehicle-A build with the identical export/parity/manifest
  discipline; calibration seed = the 641 Δ-parseable within-BdG runs (below). sha256 recorded then.

## Δ10 — the Replay-OOF Invariant (standing rule)
Any replay/preview/deployment-simulation number is **out-of-sample or prospective by construction**,
never in-sample (the 3rd leakage-class artifact after segment-inflation and hard-failure censoring). The
model that scores a run never trained on it (verified by pk). All reported estimates obey this.

## Estimands (defined once)
- **TOTAL_CAMPAIGN_ITER** — Σ SCF iterations over ALL segments and runs, converged + aborted
  (equivalently within-partition node-seconds). Where L1 (early-abort) shows up.
- **MEDIAN_ITER_TO_CONV** — median iterations-to-converge over converged systems. Where L2/L3 show up.
- Accounting unit = SCF iterations (hardware-invariant primary); node-seconds ∝ iters×ranks reported
  per-partition secondary. The ~28% completed-run waste ceiling caps L1 ONLY. **F2 companion:** G1 recovery is also reported in rank-seconds (unit-invariant fraction 0.69/0.91; absolute ~3,600 rank-h retrospective); pre-registered amendment: if node-second and iteration recovery fractions diverge >5%, iterations stands as primary and both are reported (see phase1_g1_results.md).

## A/B assignment & fairness
Arms (ml_assist vs stock) interleaved WITHIN a partition. Primary metric hardware-invariant
(iterations); wall-clock secondary, reported per-partition, **never pooled across partitions**.

## Conformal / abort discipline — MONDRIAN (group-conditional)
One-sided split-conformal, false-abort rate ≤ α. **The split-conformal guarantee is MARGINAL, not
conditional** — a single threshold under-protects strata whose converging runs sit near the boundary.
Verified (`phase1_conditional_fa.py`): with a marginal threshold the flat-starter stratum has false-abort
**0.086 at α=0.05** (1.7× budget). FIX (adopted): **Mondrian per-stratum thresholds**
(`MondrianConformalAbortPolicy`, stratum = flat-starter vs other, feature-derived) restore conditional
control to 0.047. Certifiability needs ~19 calib points at α=0.05 (~9 at α=0.10) PER STRATUM →
material-matched historical seeding, refreshed online. Advisory-by-default; abort only when enabled AND
every deployed stratum threshold is certifiable.

## Reporting both denominators (anti denominator-selection)
Recovery is always reported against BOTH denominators: as a fraction of the frozen addressable pool
(diverge+stall) AND of ALL wasted iterations including the near-miss hard tail. (Task-5: 0.69 vs 0.65 at
α=0.05.) The gate is stated on the frozen pool; the all-waste number is reported alongside so the gate
cannot be accused of denominator selection.

## Stopping rules
- Campaign runs to its pre-set system budget; no data-peeking to stop early for a favorable result.
- NaN/hang watchdog: a run producing no parseable output within its walltime is scancel'd (hygiene),
  counted as censored (not a model decision).
- **Conformal-violation trip-wire (numeric):** over a rolling window of ≥30 abort-eligible converged
  runs PER STRATUM, if the realized false-abort rate exceeds α by more than the one-sided 95% binomial
  margin (equivalently: observed false-abort > α + 1.645·√(α(1−α)/30) ≈ α + 0.064 at α=0.05), abort-mode
  halts for that stratum → advisory until re-review.

## Negative results
A FAIL against the gate is reported AS-IS. Negative/ null results (including "no net savings",
"Δ adds nothing prospectively", "transfer fails") are publishable and pre-committed to publication.

## Telemetry schema (node extras, every ml_assist decision)
`ml_assist.{version, decision, model_id, mode, alpha, t_obs, p_converge, conformal_threshold,
certifiable, n_calib_pos, features}`; Vehicle A adds `{p_rms_only, p_rms_plus_delta, delta_available}`
(dual-scoring, Rider 1). Provenance: the git commit + sha256 of any modified workflow recorded per run.

## Physics-equality tolerances (empirical, not arbitrary)
Set as a small multiple (×3) of the natural rerun-to-rerun scatter of converged observables measured
from historical duplicate/restart runs (`phase1_physics_scatter.py`): total-energy/atom, magnetic
moment, and (BdG) the Δ amplitude. MEASURED (v3, `phase1_physics_scatter_v3.py`, 4784 converged host calcs):
- **PLATEAU NOISE (the reliable, matching-free reproducibility floor):** per-run std of total energy over
  the last 5 converged iterations / atom — median **1.6e-7 Ry/atom**, p90 **9.7e-6** (n=2833).
- **Matched-settings rerun scatter is UNUSABLE:** grouping by (formula + LMAX + BZDIVIDE + contour) still
  conflates dopant configurations / magnetic states (median 10 Ry/atom) — formula-level matching cannot
  isolate physics-identical reruns without exact site-occupation matching (impractical). We therefore do
  NOT use rerun scatter.
- **ADOPTED total-energy tolerance = 3 × plateau p90 ≈ 3e-5 Ry/atom** (from plateau noise at a robust
  percentile: avoids both the contaminated rerun number AND the pathological tightness of 3×median 1.6e-7).
- **moment tolerance = 3 × plateau p90 = 1.2e-4 μB** (`phase1_scatter_moment_delta.py`, n=2773; plateau
  median 7.5e-7, p90 3.9e-5).
- **BdG Δ tolerance = 3 × plateau p90 = 3.2e-7** (n=666; plateau median 4.4e-11, p90 1.1e-7).
All three physics-equality observables (energy, moment, Δ) now measured by the plateau-noise method.

## Decisions (Mohammad, 2026-07-15/16) — RESOLVED
- **Partition:** Vehicle B = **th1** (22×12c/24GB, Westmere-class) + viti (6×20c); conservative default
  (oscar's +10 hardware-identical nodes available if chosen — only the node-hour line changes).
- **Vehicle A chain = Option 1** (near-critical CPA-BdG audit), with the drafted numeric near-criticality
  criterion + abort-enabled-fraction rule.
- **Launch order: Vehicle B first** (model frozen, seed ready, farm idle); Vehicle A after its mandatory
  production-mesh NSTEPS=1 BdG-init pre-flight.
- **Hardware:** th1-2020-64 = single-socket 64-core EPYC 7742, SMT-2 (128 logical); **MPI ranks cap at 64
  physical cores/node** (confirmed via `scontrol`, 2026-07-16).
