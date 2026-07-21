# Proposal 01 — publication plan (2026-06-26)

## Results inventory
- **R1** Provenance-traced convergence dataset: 3,405 SCF runs (2,541 normal + 864 BdG), corrected
  BdG label rule (`USE_BDG ∧ AT_SCALE_BDG≠0 ∧ LAMBDA_BDG>0`), full RMS trajectories. ✅
- **R2 [SPINE]** Early convergence classifier (first 10 iters), chemistry-transfer LODO: AUC
  Fe 0.957 [.934,.978], V 0.964 [.927,.991]; failure-recall .94/.93; physics-driven (no leakage). ✅
- **R3 [NOVEL]** Cost-vs-outcome dissociation normal→BdG: cost transfers (MAE 36.8 [33.5,39.9]),
  outcome doesn't (AUC 0.68 vs within-BdG 0.93). ✅
- **R4** Iteration regression (LODO): significant Fe(+8.6%)/Mn(+45%)/Co(+51%), not V. ✅ (secondary)
- **R5** Label-hygiene cautionary tale: relabeling removed a false −18% Fe negative-transfer. ✅
- **R6** AiiDA-native `MLRestartProtocol` (17 provenance runs) — prototype, errors. ⚠️
- **R7 [PAYOFF]** Early-abort compute savings + T_obs robustness: **~36% of total SCF compute saved
  at ZERO false-aborts** (82% of doomed runs caught) after only 10 of ~100 iterations; 41% at thr=0.5.
  AUC flat from T_obs≈3 (fate decided immediately). ✅ done (`study_d_savings.py`).

Caveats to state plainly: Mn/Co underpowered (wide CIs); classifier is online (first-10-iters),
not a-priori; RandomForest baseline (LSTM comparison optional).

## Target venues (ranked)
1. **Machine Learning: Science and Technology (MLST, IOP)** — primary. Best fit, OA, welcomes nuanced
   results. Ready after R7.
2. **Digital Discovery (RSC)** — close alternative; emphasize the AiiDA workflow + reproducibility.
3. **Computer Physics Communications** — if we release `MLRestartProtocol` as a packaged tool.
4. **npj Computational Materials** — stretch; needs R7 + LSTM comparison + broader demonstration.
5. **PRB Computational / Electronic Structure** — if reframed around the BdG-mixing physics (R3).

## Path to submission
1. R7 compute-savings + T_obs robustness (now) → the acceleration payoff figure.
2. Optional strengthening: LSTM-vs-RF on corrected split; bootstrap already done.
3. Figures: (a) AUC + failure-recall per dopant w/ CIs; (b) early-abort savings vs false-abort curve;
   (c) AUC vs observation window; (d) feature-importance; (e) cost-vs-outcome dissociation; (f) the
   relabeling correction.
4. Draft around the spine (R2) + dissociation (R3) + savings (R7); position Mn/Co honestly.
5. Decide MLST vs Digital Discovery based on whether we add the tool release.

---

## If-compute-available roadmap (budget: 2 nodes on th1-2020-64)

### Key prerequisite finding (read-only diagnosis, 2026-06-26)
The 17 `MLRestartProtocol` + 14 `KkrWorkChainWithMLMixing` runs errored on **deployment bugs, not
physics** (`workspace/analysis/diagnose_mlrestart.py`):
- WorkChains defined in `__main__`/non-installed module → daemon `ModuleNotFoundError` /
  `module '__main__' has no attribute ...` on resume.
- Input wiring: passed `parameters` to a non-dynamic namespace; spec expected `wf_parameters`/the
  `kkr_scf` namespace.
⇒ The closed loop is blocked by bounded engineering, not by the science.

### Phase 0 — fix & deploy (needs authorization: writes to env + daemon)
1. Package the workchain via the existing `pyproject.toml` (`kkr-ml-workchains`); reference it by a
   proper module path (not `__main__`). `pip install -e .` into the **daemon's** env.
2. Fix the input wiring (`wf_parameters` / exposed `kkr_scf` namespace; pass `calc_parameters` right).
3. Restart the daemon (NOTE: `verdi daemon restart` is currently on the forbidden list → explicit OK).
4. Smoke-test ONE short run end-to-end.

### Resource configuration (2 nodes, th1-2020-64 = AMD EPYC 7742, 64c/128GB)
- BdG SCF: validated config 48 ranks/node × 2 = 96 ranks (~2.6 GB/rank, fits 128 GB); honor the
  energy-point rank cap (~18–24 for BdG contour). `OMP_NUM_THREADS=1`, `I_MPI_FABRICS=shm`, `srun`
  (not mpirun), `source compiler-select intel-fi`, `ulimit -s unlimited`, `OMP_STACKSIZE=2G`.
- Concurrency: ≤2 jobs. For throughput, run **two 1-node jobs** in parallel; for speed, one 2-node job.
- Cost: NbSe2 BdG SCF ≪ the 84-atom slab (~27 min/iter); est. ~5–10 min/iter, converged BdG ~59 iters
  → ~6–10 h/run; failures hit NSTEPS (longer) — which the ML abort cuts to ~10 iters (~1–2 h).

### Phase 1 — PROSPECTIVE locked-model test (~20–30 new runs; the key result)
Run new SCF (normal + BdG, incl. a few new Mn/Co concentrations) to completion under baseline.
Apply the FROZEN first-10-iter classifier prospectively (no peeking). Report prospective AUC +
would-be savings on genuinely new data. Answers the reviewer's "retrospective on your own data" critique.

### Phase 2 — live closed-loop (~10 runs; the tier-changer)
`MLRestartProtocol` acts live: abort/restart-with-tightened-mixing after the first ~10 iters.
Measure REAL CPU-hours saved vs baseline + any runs the restart policy rescues.

### Budget estimate
~30–40 runs total, 2 concurrent → ~1–2 weeks wall-clock (the ML abort policy shortens the campaign's
own failures). Some runs WILL fail — on-message (the model predicts exactly those).

### Metrics / figures added
Prospective confusion matrix + AUC; predicted-vs-realized savings; wall-clock saved (live); rescue cases.

### Venue effect
Phases 1–2 lift the paper from "convergence predictor" (MLST) to "deployed, provenance-native ML
accelerator with measured savings" → realistic **npj Computational Materials / Digital Discovery** tier.
