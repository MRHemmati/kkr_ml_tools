# ml_assist — Vehicle-B iffslurm Fe-only PILOT — FINAL CLOSURE REPORT (2026-07-21)

**The staged Fe-only iffslurm pilot is COMPLETE. No further action.** This is a summary only; nothing was
submitted, no daemon/package/DB changes, no labels/extras on pre-existing nodes, no job actions.

Stages executed and accepted: Gate 0 (scope) → Stage A (read-only pre-flight + offline policy refinement)
→ Stage B (advisory smokes; surfaced the cumulative-trajectory bug) → source fix (0.1.1) → Stage C1
(gated reinstall + live validation of the fix) → Stage C2a (5 stock baselines) → Stage C2b (ml_assist
arm). Scope throughout: **N=5, Fe-only, iffslurm-only, completed-runs — a descriptive pilot.**

## Matched outcomes — C2a (stock) vs C2b (ml_assist), one row per system
Counterfactual key: structure + cold start + strmix 0.03/brymix 0.05 + nsteps=10 + partition.

| id | system | part | C2a stock outcome (iters) | C2b mode | C2b decision (p, thr 0.432) | C2b outcome (iters) | classification |
|---|---|---|---|---|---|---|---|
| S1 | Nb₂Se₄X₂ pristine | th1 | CONVERGED (145) | advisory | continue\_would\_abort (0.262) | CONVERGED (145) | **would-abort but converges → advisory correct** |
| S2 | Nb₂Se₄X₁₀ | viti | DIVERGE (150) | advisory | continue (0.732) | DIVERGE (150) | advisory miss (scored high, diverged) |
| S3 | Fe 1% CPA | th1 | STALL (150) | abort | continue / MISS (0.570) | STALL (150) | **miss — late stall, no savings** |
| S4 | Fe 10% CPA | viti | CONVERGED (146) | advisory | continue (0.743) | CONVERGED (146) | advisory, correct |
| S5 | Fe 92% CPA | th1 | DIVERGE (150) | **abort** | **ABORT (0.297) @iter 20** | aborted (20) | **TRUE abort, ~130 iters saved** |

Every C2b run reproduced its C2a outcome; the only divergence is S5's intended early abort.

## Claim ladder
**VALIDATED (live, end-to-end):**
- L1 early-abort **mechanism** works live in the daemon: S5 aborted at cumulative iter 20 (p=0.297 <
  flat threshold 0.432); matched stock counterfactual diverged at 150 iters; **≈130 SCF iterations saved**.
- The **cumulative-trajectory fix (0.1.1)** works live (C1: wait at iter 10, real score at iter 20).
- **Per-stratum Mondrian + telemetry** (`stratum_advisory_only`) live and complete.
- **Safety of advisory-only for S1** is necessary and correct: S1 scored p=0.262 (would-abort) yet the
  matched stock run converged → abort-enabling S1 would have been a **false abort**.
- **L2 racing machinery** executes and produces useful mixing discrimination (commits highest-p decreasing
  leg; low-strmix legs win for hard cells).
- **No conformal safety violation** in the pilot (zero false aborts observed).

**SUGGESTIVE (not proof):**
- Early L1 concentrates its value on cells that fail *early* (diverge): S5 caught, ~130 iters saved.
- Better mixing raises predicted convergence (racing p-scores) — a hint the L2 selection is meaningful.
- Per-system iteration deltas (mostly ~0; S5 −130) are directional, **descriptive only at N=5**.

**NOT CLAIMED:**
- No powered Wilcoxon / statistically-significant savings claim (N=5, underpowered).
- No dopant-breadth claim (Fe-only; Mn/V/Co on CLAIX, out of scope).
- **Zero-false-abort is due to conservative counterfactual gating, NOT conformal-calibration validation.**
- No cross-material / cross-cluster transfer claim.
- Early L1 does **not** catch all doomed runs — S3 is an honest miss (its stall emerges late).

## Accounting totals (SCF iterations; matched systems)
| quantity | value |
|---|---|
| C2a stock TOTAL\_CAMPAIGN\_ITER (5 systems) | **741** |
| C2b Group-A ml\_assist TOTAL\_CAMPAIGN\_ITER (5 systems) | **611** |
| — of which saved by the S5 true abort | **130** (S5: 20 vs 150; S1/S2/S3/S4 delta ≈ 0) |
| Group-B racing iterations — **charged to ml\_assist**, reported separately | **240** (12 advisory legs) |
| Group-C warm-start — **instrumentation, separate** | **0** (excepted, see debt) |
| Censored (NaN/hang/walltime) | **NONE** |
Note: iterations are the hardware-invariant primary; th1 and viti are never pooled. The 741→611 (Group-A)
reduction is entirely the single S5 abort; it is a **descriptive** per-system result, not a powered claim.

## Open technical debt
1. **L3 warm-start wiring (BLOCKER for L3):** `kkr_scf_wc.run_voronoi` requires the `voronoi` input even
   when `remote_data` is supplied → the warm-start run (108374) excepted. **This is technical debt, NOT a
   failed donor-selection result** (donor 108008 was compatible). Fix: supply `remote_data` + `voronoi`,
   or use a `startpot_overwrite` path; then re-attempt L3 in a future stage.
2. **Late-stall detection (L1 limitation):** S3-type runs decrease early then stall — invisible to the
   first-window score. A schedule-aligned / later re-score (the deprioritized Δ3) or a stall-specific
   feature could help; deferred for v1.
3. **High-accuracy final segment cost:** the converging cells' final high-accuracy pass is very slow
   (~1 h+/segment on th1) — a walltime/scheduling consideration for any larger campaign.
4. **Statistical power:** N=5 Fe-only is descriptive; a powered test needs more systems (Mn/V/Co require
   CLAIX access, currently closed) and/or matched replicates.
5. **BdG / Vehicle A:** unstarted; the frozen BdG models + Δ-parser exist but no live BdG pilot was run.

## FINAL AUDIT LINE
Across the entire pilot the only cluster/DB actions were: the **authorized submissions** (Stage B 2 smokes;
C1 1 validation; C2a 5 stock; C2b 18 = 5 Group-A + 12 racing + 1 warm), the **C1 gated 0.1.1 install +
daemon restart**, and the **C1 model-node/provenance writes** — each under explicit approval and reported.
**No further action was taken to close the pilot: no submissions, no daemon/package changes, no DB writes,
no labels/extras/groups on pre-existing nodes, no job kills/scancel. All post-run analysis was read-only.**

**Pilot CLOSED.**
