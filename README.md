# kkr_ml_tools — Calibrated convergence control for KKR / BdG Green's-function DFT

An AiiDA-native framework (`ml_assist`) that scores the first ten SCF iterations of a KKR / BdG
Green's-function DFT run and can **abort doomed runs early**, under a **per-cohort conformal** early-abort
policy. It ships a frozen pure-`numpy` scorer (the AiiDA daemon has no scikit-learn), a simple
**RMS-at-iteration-10 baseline**, and per-stratum (Mondrian) thresholds. The design is opt-in with a
zero-risk default: absent an `ml_assist` input the workchain behaves identically to stock `kkr_scf_wc`.

> **Honest headline (see the technical report).** On a 336-run leakage-clean held-out benchmark with
> per-run `QBOUND` labels, the learned model does **not** beat the simple RMS@10 baseline on the primary
> NbSe₂-normal cohort (held-out AUC 0.83 vs 0.90), does **not** transfer across materials, and a
> NbSe₂-seeded conformal threshold does not transport (realized false-abort 0.47) — though **per-cohort
> recalibration restores** false-abort control. Deployment therefore requires **per-cohort calibration**
> and a **strong RMS baseline comparator**; the contribution is the calibrated, provenance-tracked
> framework and the honest benchmark, not model superiority. A live Fe-only pilot validated the abort
> *machinery* end-to-end (one true early abort saved ~130 SCF iterations; a would-be false abort correctly
> withheld; N=5, descriptive).

## Repository layout
```
src/aiida_kkr_mlassist/   installable package (src-layout); pure-numpy core + AiiDA workchain
                          entry points: kkr.mlassist, kkr.bdg; ships frozen models in models/
tests/                    unit tests (feature parity, golden parity, ranks, conformal, Mondrian,
                          cumulative trajectory, BdG dual-scoring, wrapper pipeline)
models/                   frozen-model manifests, MODEL_CARD.md, model_node_uuids.json, MODEL_HASHES.txt
                          (the .npz binaries themselves ship inside the package under src/.../models/)
reports/
  technical_report/       the accepted technical report: main.tex + main.pdf + make_figures_d1b.py
                          + D1b metrics/scores (JSON/CSV) + figures/
  stage_records/          key stage reports: final freeze, pilot closure, D0 inventory, D1 held-out
                          replay, D1-QC, D1b clean benchmark, report-rewrite summary
  potentialbank_v1/       PotentialBank v1 (L3): manifest + tables + figures + synthesis/claim-ladder reports
src/kkr_convergence_advisor/   offline retrieval-based advisor; data/ = advisor_index_v1.json + example tips
preregistrations/         PREREG_common + Vehicle A/B (historical; superseded — see the report)
proposals/                project proposals (proposal_01 = ML-accelerated SCF convergence)
legacy/lstm_restart/      the previous LSTM SCF-restart tool (preserved, superseded by this project)
```

## PotentialBank v1 (L3 warm-start)
Separate, complementary to `ml_assist` (L1): a **certified catalog of single-structure converged KKR
potentials** for **same-structure SCF warm-start reuse** — **237 unique donors** (238 nodes) across **8
families / 35 materials**, **33 F2-eligible**. Injecting a certified donor as the start potential cuts
iterations-to-converge by ~91–99% on a converging target (per-family, mixing/contour-qualified;
donor-choice-independent). Admission is byte-exact E1 certification (Z-sequence, NATYP, non-CPA/BdG, 3-way
SHA). **Same-structure reuse only — no cross-material transfer, no guaranteed acceleration; CPA/BdG out of
scope.** See [`POTENTIALBANK_V1.md`](POTENTIALBANK_V1.md) and `reports/potentialbank_v1/`.

## Install (development)
```bash
pip install -e .              # numpy-only runtime; [aiida]/[dev] extras for the workchain + tests
```
The runtime inference core (`features`, `infer`, `conformal`, `ranks`, `decision`) imports **without**
AiiDA or scikit-learn; the workchain (`workchain.py`) imports `aiida_kkr` only inside the daemon.

## Frozen models
| model | role | in-dist. AUC | sha256 (see `models/MODEL_HASHES.txt`) |
|---|---|---|---|
| `mlassist_v1_normal_fixed10` | normal-state scorer | 0.944 (in-dist; 0.83 held-out primary) | `cebe56b9…` |
| `mlassist_v1_bdg_rmsdelta` | BdG primary (rms+Δ) | 0.957 | `fd67c9a3…` |
| `mlassist_v1_bdg_rms` | BdG missing-Δ fallback | 0.946 | `b73c1453…` |
Weights are frozen and were unchanged through all held-out and pilot evaluations. **BdG runs must be
scored with the BdG model**, never the normal one.

## Scope & limits
- Deploy **per-system / per-cohort**; recalibrate the conformal threshold on each campaign's own converged
  runs and benchmark model vs. RMS@10 before enabling abort.
- **No cross-material transfer** is claimed. Warm/restart runs are **outside** the current abort policy.
- Dataset scope: completed runs (crashes/NaN-kills are censored and handled by a watchdog, not the model).
- Late-stall detection is the open modeling gap.

## Provenance
See `reports/technical_report/main.pdf` for the full account (data audit, classifier, conformal policy,
held-out benchmark, live pilot, BdG workflow hardening + memory number, package, pre-registration). The
prior LSTM restart tool is retained under `legacy/lstm_restart/` and tagged by branch
`legacy-lstm-restart-20260721`.
