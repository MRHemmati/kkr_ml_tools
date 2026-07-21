# Pre-registration — Vehicle B (normal-state, throughput, L1+L2+L3)

DRAFT 2026-07-14. Reads with `PREREG_common.md`. Partition: **`th1`** (22×12c/24GB, Westmere-class) + viti (6×20c) — CHOSEN 2026-07-15 (conservative default; the paired campaign completes in ~4–6 h without oscar's +10 hardware-identical nodes, which remain available if Mohammad later opts for `th1-oscar` — only the node-hour line changes). **Launch order: Vehicle B FIRST.** Levers: **L1 abort + L2 probe-and-commit
mixing + L3 warm-start**. Goal: cut both total campaign compute and median iterations-to-converge across
a normal-state screening campaign.

## Model & scoring
- Frozen **`mlassist_v1_normal_fixed10`** (sha256 in common preamble; normal regime, fixed T_OBS=10).
- **α = 0.10 (throughput)** — from the Task-5 net-savings curve, α=0.10 maximises net under the
  reduced-mixing (warm-restart) cost model; false-abort held at 0.100, pool recovery 0.91.
- **Calibration seed = material-matched normal-state NbSe₂-family history** (OOF); refreshed online.
  Cold-start on the 2026 prospective grid gave realized false-abort 0.000 (material-matched seeding
  transports) — the pre-registered cold-start check.

## Campaign design — PAIRED within-system (reviewer Issue 3)
Compute is abundant (~30–90 node-h total), so **every system runs in BOTH arms** (stock and ml_assist on
the SAME structure) → **paired statistics** (Wilcoxon signed-rank on iterations-to-converge), far more
powerful than 8–12 independent systems/arm at a ≥25% target. Arms interleaved within partition.
- **16–24 systems** (NbSe₂-family dopant/CPA variants), each run both arms.
- **Racing (L2 probe-and-commit) — explicit k=4 ladder:** on the first 3–4 systems, race **k=4** mixing
  settings × ~10-iteration legs, grid-valid ranks (`ranks.best_rank`). **Ladder** (fixed at FINAL):
  {(strmix 0.02, brymix 0.05), (0.05,0.05), (0.03,0.08), (0.01,0.02)}. **Commit rule:** commit the leg
  with the lowest RMS at leg end that is on a decreasing trajectory; **all-legs-doomed fallback:** if all
  k legs are conformally-doomed at leg end, fall back to the conservative (0.01,0.02) setting cold and
  flag the system as hard.
- **L3 warm-start:** randomized warm/cold, cold fraction 40–50% early, decaying. Near-boundary systems
  DEFAULT COLD, stratified OUT of the L3 causal contrast. **Donor-selection rule:** warm start reuses the
  nearest converged potential of the SAME formula with **matching LMAX, radial mesh, and shape/site
  count** (reject incompatible donors → cold). **Paired warm-AND-cold SAFETY subset (≥5 systems):** run
  ≥5 systems BOTH warm and cold to convergence and compare their converged observables within the
  physics-equality tolerances — this tests L3 SAFETY (not just speed), the hole in a start-randomized-
  across-systems design.

## Accounting (reviewer Issue 3)
Racing/probe-and-commit iterations are CHARGED to the ml_assist arm's TOTAL_CAMPAIGN_ITER (they are part
of its cost). Instrumentation replicas (the warm-AND-cold safety subset, shadow scoring) are reported
SEPARATELY, not netted into either arm's headline. Conformal abort uses **Mondrian** per-stratum
thresholds (common preamble).

## Ranks / packing
Grid-valid ranks mandatory (`validate_chain_ranks` every step). Intel packing is core/grid-bound at the
light normal mesh (memory not binding); per-node rank quantized to the cell's divisor set. Westmere
1×12-rank/node, viti 2 jobs/node (packing doctrine v3).

## G3 gate (success criterion)
- **MEDIAN_ITER_TO_CONV ↓ ≥ 25%** (L2/L3 effect on converged systems), AND
- **TOTAL_CAMPAIGN_ITER ↓ ≥ 25%** (L1+L2+L3 combined; not bounded by the 28% L1 ceiling since L2/L3 act
  on the converged 72%), vs the interleaved stock arm.
- Wall-clock per-partition secondary; A/B never pooled cross-partition. A FAIL is reported as-is.

## Operational
Hygiene-cap walltime (~3 h normal); NaN watchdog; advisory-until-certifiable; probe-and-commit legs
short so a losing mixing setting is abandoned cheaply. Racing arms interleaved within the partition.

## Node-hour math (partition RESOLVED 2026-07-16)
Measured capacity (Δ2″): EPYC ~305 iter/h, viti ~415, Westmere-pool ~300 → Intel farms ~875 C1-iter/h.
16–24 systems × (racing legs + committed run + warm/cold replicas) → firm estimate: th1@85%≈18-19 nodes ×12c (doctrine default) or th1-oscar@85%≈27 nodes ×12c (+50% Westmere-class throughput), + viti 6×20c. oscar = same 12c/24GB Westmere class as th1.
