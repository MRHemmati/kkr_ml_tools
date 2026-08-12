# Stage D0 — Evidence Expansion: READ-ONLY AiiDA inventory + Stage-D1 design (2026-07-21)

**READ-ONLY. No submissions, daemon/package changes, DB writes, labels/extras/groups, or job actions.**
All figures from read-only QueryBuilder passes (`workspace/analysis/d0_*.py`).

## 1. Database landscape (KKR-relevant)
| node type | count |
|---|---|
| KkrCalculation | 6,092 |
| VoronoiCalculation | 1,128 |
| KkrimpCalculation | 954 |
| kkr_scf_wc (workchain) | 857 |
| kkr_bdg_wc | 98 |
| MLAssistKkrScfWorkChain (our own) | 24 |
| kkrimp_BdG_wc / kkr_imp_sub_wc | 1,451 / 939 |

**KkrCalculation by computer:** Jureca-new 3,105 · claixsshtunnel 1,352 · **iffslurm 1,197** · JURECA-DC 258 · …
→ **most KKR history is on remote clusters (Jureca/CLAIX); only 1,197 KkrCalculations are on iffslurm** (the
only cluster we can run on). CLAIX/Jureca runs are inventory-only (not launchable here).

## 2. iffslurm KkrCalculation deep inventory (1,197)
- **Regime:** normal 980 · BdG 217.
- **exit_status:** 0 → 932 · None(running/old) → 159 · 302 → 95 · 301 → 7 · 120 → 4.
- **Convergence (by final rms vs ~1e-3; exit0 ≠ converged):** CONVERGED 279 · STALL 306 · DIVERGE 278 ·
  no-trajectory 250 · excepted/censored 84.
- **Trajectory replay-usable (≥12 iters):** **516**.
- **Have a `kkr_scf_wc` parent (cloneable / stock-context):** 591.
- **Partition (where queue recorded):** th1-2020-64 **317** · th1-2020-32 **168** · oscar 19 · th1 10 · viti 2.
  → **Historical iffslurm KKR ran on the EPYC/AMD partitions, NOT Westmere th1/viti** (which have ~12 total).

## 3. Training / frozen-seed OVERLAP (leakage control)
Training/seed source = `dedup_records.pkl` (2,710 runs; frozen model + calibration seed). Of the **516
replay-usable iffslurm runs, 180 are IN training → 336 are HELD-OUT (leakage-clean).** This 336-run
held-out pool is the core asset D1 exploits — an out-of-sample benchmark ~67× the N=5 pilot, requiring
**zero new submissions**.

## 4. Held-out benchmark pool by family (via `kkr_scf_wc` parents, formula-known, iffslurm)
| family | #kkr_scf_wc | held-out usable calcs | conv | stall | div |
|---|---|---|---|---|---|
| **NbSe₂-family** | 70 | **198** | 47 | 87 | 79 |
| other-KKR (Nb bulk, Pb₃Te₄:Tl) | 20 | 43 | 20 | 37 | 4 |
| Bi/NbBi (Bi₄X₄, Bi₂X₄, Bi₂Te₃…) | 17 | 30 | 13 | 27 | 4 |
NbSe₂ formulas: Nb₂Se₄X₂ (pristine, 57 wc) · Nb₂Se₄X₁₀ (5) · Fe-doped 1/10/92% (matched the pilot).
**Outcome mix is balanced** (converged/stall/diverge all well-represented) — unlike the N=5 pilot.

## 5. Per-candidate fields (representative held-out NbSe₂; full list producible on request)
The requested per-candidate fields (pk/uuid, computer/partition/code, structure, parent wc, ctime/mtime,
SCF settings nsteps/kkr_runmax/strmix/brymix/qbound/grid/ranks, final rms/chneut/iters, verdict, trajectory
availability, regime, training overlap, suitability) are all queryable; a full CSV can be produced read-only.
Representative rows (held-out, NOT in training):
- **CONVERGED (retro-validation + warm-donor):** calc 132 (wc 240, Nb₂Se₄X₂, 54 it, rms 1e-4) · calc 26
  (wc 245, 48 it, rms→0) · calc 49 (wc 245, 25 it).
- **STALL (retro-validation + L2 racing target):** calc 853 (wc 240, 12 it, rms 8e-3) · calc 360 (wc 275,
  Nb₂Se₄X₁₀, 128 it, rms 8e-3) · calc 779 (wc 582, 200 it, rms 2.2e-3).
- **DIVERGE (retro-validation + L2 racing target):** calc 792/791/386/120 (wc 875, Nb₂Se₄X₂, 200 it,
  rms 0.318).

## 6. Suitability classification (categories 1–4)
1. **Retrospective validation (offline, NO submission, leakage-clean):** the **336 held-out iffslurm runs
   with ≥12-iter trajectories** (198 NbSe₂ + 43 other + 30 Bi + BdG subset). This is the primary D1 asset —
   a real out-of-sample AUC / recall / early-abort-savings benchmark on ~336 runs, replayed from stored
   `convergence_group` trajectories. No cluster time, no leakage.
2. **Prospective templates (cloneable):** 70 NbSe₂ + 20 other + 17 Bi `kkr_scf_wc` with iffslurm structure
   (converged ones give clean cold-start templates). NOTE: prospective = new submissions (out of D0 scope);
   and these historically ran on th1-2020-64/32 (AMD), not th1/viti.
3. **Warm-start donors (L3):** the converged runs (47 NbSe₂ + 20 other + 13 Bi) provide same-formula
   converged potentials. (Caveat: the L3 wiring debt from C2b — `remote_data`+`voronoi` — must be fixed first.)
4. **L2 racing candidates:** the stall/diverge runs (87+79 NbSe₂) are cells where a mixing search is
   meaningful — the population where L2 pays off.

## 7. BdG subset (Vehicle-A relevance)
217 iffslurm BdG KkrCalculations; ~37 with usable trajectories. A modest but real BdG replay set (the
frozen BdG rms+Δ model + Δ-parser exist). Most BdG history, however, is on Jureca/CLAIX (inventory-only).

---

# Proposed Stage D1 — benchmark design (for review; NO submissions in D1 unless separately approved)

## D1 primary = RETROSPECTIVE, fully offline (recommended first)
- **Cohort:** the 336 held-out iffslurm runs with ≥12-iter trajectories (leakage verified by pk ∉ dedup).
- **Method:** replay each run's stored trajectory → frozen model scores its first-10 window → compute
  **held-out AUC, failure-recall, and early-abort iteration-savings** (abort iter vs actual terminal iters),
  stratified by family (NbSe₂ / Bi / other) and outcome (converge/stall/diverge), with bootstrap CIs.
  This turns the N=5 descriptive pilot into an **n≈336 out-of-sample benchmark with ZERO new compute and
  zero leakage** — directly upgrading the statistical-power gap flagged at pilot closure.
- **Deliverables:** held-out AUC + CI, recall, savings ceiling, per-family/per-outcome breakdown, and an
  honest late-stall analysis (does the model still miss late stalls like S3 at scale?).
- **Gating:** read-only — needs only approval to run the analysis scripts (no cluster/DB writes).

## D1 secondary (OPTIONAL, gated, needs submissions) — prospective/L2/L3 on the richer cohort
- Prospective: clone converged NbSe₂ templates (cat 2) for new ml_assist runs — but partition reality
  (history is AMD; Vehicle-B is th1/viti) means either accept EPYC for the benchmark or run a th1/viti
  pre-flight first.
- L2 racing on the stall/diverge cells (cat 4), matched-counterfactual per the C2b protocol.
- L3 warm-start once the wiring debt is fixed (cat 3 donors).
These require separate explicit approval (submissions); NOT part of D0/D1-primary.

## Open items carried in
- L3 warm-start wiring debt (C2b); late-stall detection; N-power (now addressable retrospectively via the
  336-run pool); BdG/Vehicle-A still unstarted (37 iffslurm BdG replay candidates + Jureca/CLAIX inventory-only).

## AUDIT LINE
D0 was **read-only**: QueryBuilder inventory passes only. **No submissions, no daemon/package changes, no
DB writes, no labels/extras/groups, no job actions.** Stop here per instruction.
