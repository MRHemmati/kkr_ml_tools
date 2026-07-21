# Pre-registration — Vehicle A (BdG, L1-only, conservative)

DRAFT 2026-07-14. Reads with `PREREG_common.md`. Partition: **th1-2020-64** (EPYC 7742, 2-node quota).
Lever: **L1 early-abort only** (no L2/L3). Goal: recover the pairing-channel's own wasted compute on a
BdG screening chain without ever discarding a converging run.

## Model & scoring
- **rms+Δ BdG model — FROZEN 2026-07-14:** `mlassist_v1_bdg_rmsdelta` (22 feat = 15 `features.py` + 7
  `bdg_parser.delta_features`), sha256 `fd67c9a35b1928df…`, 5-fold OOF AUC 0.957, golden parity 2.8e-17,
  packaged. Fallback model `mlassist_v1_bdg_rms` (15 feat), sha256 `b73c14534c169ff8…`, OOF AUC 0.946.
  (Verify the artifact timestamps precede any Vehicle-A submission at launch.)
- **Dual-scoring telemetry (Rider 1):** every run logs BOTH `p_rms_only` and `p_rms_plus_delta`;
  post-campaign paired prospective Δ-lift test on instability-rich data (the pre-registered test of the
  "understated lift" claim — historical corpus had `delta_grew` importance ≈ 0).
- **Missing-Δ fallback (Rider 2) — TWO independent thresholds:** the deployed decision uses the rms+Δ
  policy (threshold calibrated on rms+Δ scores); on missing Δ it falls back to the rms-only policy with
  its OWN threshold calibrated on rms-only scores (never compare an rms-only score to an rms+Δ threshold).
  `decision.score_bdg_dual` carries both `policy_full` and `policy_rms`, each certifiable independently;
  both are **Mondrian** (per-stratum) per the common preamble.

## Conformal calibration
- **α = 0.05 (conservative)** — from the Task-5 net-savings curve, α=0.05 is the conservative profile
  (false-abort held at 0.049; net-positive under all three retry-cost models).
- **Calibration seed = the 641 Δ-parseable within-BdG runs** (OOF scores). Exchangeability caveat:
  these are historical completed runs; the seed is refreshed online as campaign labels arrive, and the
  abort mode is gated on certifiability (≥19 points at α=0.05, satisfied by the seed).
- Cross-material transfer NOT assumed; this is an NbSe₂-family BdG campaign calibrated on NbSe₂-family BdG.

## Per-cell pre-flight (MANDATORY, before packing)
Run ONE `NSTEPS=1` BdG-init at the PRODUCTION mesh + one grid-valid rank; read peak GB/rank from the
poller (BdG-init memory ≡ BdG-SCF memory, verified §4.2c). Packing via the replication model:
`ranks/node = min(cores, floor((node_RAM − 3.3 GB) / m))`, quantized to the valid-rank set. The measured
`m` (GB/rank at the production mesh) is inserted here before FINAL. Working prior: normal ≈ 2.6 GB/rank →
BdG ≈ 2.6 × 2.32 ≈ 6 GB/rank → ~20 ranks / 128 GB → **2 × 8-rank chains/node = 4 concurrent on 2 nodes**.

## Ranks
Per-step ranks (kkr_bdg_wc v0.2.4 target: each CalcJob its own grid-valid count) OR the common-divisor
fallback validated by `ranks.validate_chain_ranks` (footgun #1 guard). Normal step 24-pt, semi-circle/BdG
32-pt → common {1,2,4,8}; per-step allows normal@12/24, BdG@16/32.

## Chain options (Mohammad selects one; node-hours firm up after the pre-flight)
1. **Near-critical CPA-BdG audit** — a handful of Fe/Mn/V/Co CPA-BdG cells near the pairing boundary
   (where Δ instabilities — and thus L1's value — concentrate). Est. **~200–500 node-h** (2-node quota,
   ~8-rank chains, 34–60 BdG iters/run) pending pre-flight s/iter.
2. **Downward-continuation λ-chain** — one cell, decreasing pairing strength through the transition,
   warm-chained. Est. **~120–300 node-h**; fewer cells, more segments/cell.
3. **Pristine + light-doping baseline** — cheapest, low instability density (weak L1 test). Est. **~80–150 node-h**.
**SELECTED (Mohammad, 2026-07-15): Option 1** — the near-critical CPA-BdG audit, the regime where the Δ
channel and L1 both pay off and which exercises the CPA path Vehicle A is for. Launches AFTER the
mandatory production-mesh NSTEPS=1 BdG-init pre-flight, and after Vehicle B.

## G2 reachability (reviewer Issue 2 — the safety rule vs the gate)
Near-critical cells default to advisory (correct physics), but Option 1 is COMPOSED of near-critical
audits — if most cells are advisory-only, L1 recovers little BY DESIGN and G2 can fail even when the tool
works. Pre-registered controls:
- **Numeric near-criticality criterion:** a cell is "near-critical" (→ advisory) iff its dopant
  concentration is within ±X% of the historical critical-concentration estimate for that dopant, OR its
  early Δ-trajectory slope exceeds a growth threshold (`logdelta_slope` > s*). X and s* fixed at FINAL
  from the historical BdG set.
- **Expected abort-enabled fraction** of the chosen chain is stated at FINAL; **if it lands below ~50%,
  BLEND IN cells away from the boundary** until abort-enabled fraction ≥ 50%.
- **`continue_would_abort` shadow-recovery** is a PRE-REGISTERED SECONDARY metric: on advisory cells the
  telemetry records the counterfactual abort, so shadow-recovered iterations are credited even where
  abort is disabled (measures the tool's value on the exact cells G2's live number cannot).

## Shared physics protocol (both arms)
Warm-chaining (λ-continuation / restart lineage) is part of the SHARED physics protocol in BOTH arms —
stock and ml_assist run the identical chain; **the ml_assist arm differs ONLY in the abort/advisory
decision.** No warm-start difference confounds the A/B contrast.

## G2 gate (success criterion)
- **Recover ≥ 50% of the STOCK arms' own wasted iterations** (self-normalizing; TOTAL_CAMPAIGN_ITER
  reduction is the headline; abort-enabled cells only), AND
- **zero conformal violations** (per-stratum trip-wire, common preamble), AND
- **physics-equality PASS** (converged observables agree within the empirical tolerances).
Shadow-recovery on advisory cells reported as the secondary. A FAIL is reported as-is.

## Operational
12–24 h segment sanction (near-critical CPA-BdG only) with the NaN/hang watchdog; advisory-mode until the
seeded policy is certifiable on-campaign; short walltime elsewhere so error-zombies die fast.
Cold-start default NEAR CRITICALITY = advisory (defer aborts where the physics is most uncertain).
