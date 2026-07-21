# `My_ML_cc` — Project reconstruction and publication proposals

*Generated 2026-06-26 by a read-only inspection of the project directory and the local
AiiDA database (profile `default`, AiiDA v2.7.1). No AiiDA node was created, modified, or
deleted; no calculation was submitted. All analysis scripts live in `workspace/analysis/`.*

Throughout, claims are tagged:
**[FACT]** = directly read from a file or the AiiDA DB · **[INTERP]** = reasonable
interpretation · **[OPEN]** = open question / needs verification · **[NEXT]** = suggested action.

---

## 1. What this project appears to be about

**[FACT]** `My_ML_cc/` is the **machine-learning companion** to a large, multi-year
computational-superconductivity effort. The underlying physics is **all-electron, fully
relativistic KKR (Korringa–Kohn–Rostoker) Green-function DFT** run with the **JuKKR** code
via the **aiida-kkr** plugin, extended to **Bogoliubov–de Gennes (BdG)** superconductivity.

**[FACT]** The materials are layered superconductors — primarily **2H-NbSe₂** with single
transition-metal dopants **V, Mn, Fe, Co** (Z = 23, 25, 26, 27) substituting on the Nb site,
and a secondary **Bi / Nb–Bi** slab family (Fermi-surface / interface work). Disorder is
treated with **CPA**, magnetism with ordered **FM** and paramagnetic **DLM** (disordered
local moment) references.

**[FACT]** The ML goals stated in `help0/1/2.md` are two-fold:
1. **Predict and accelerate SCF convergence** — number of iterations to converge, final RMS,
   and the full RMS-vs-iteration trajectory → an **ML-guided "restart protocol."**
2. A **surrogate for the superconducting gap** `delta/delta0(x, dopant, order)` to interpolate
   the critical concentration `xc` without running every point.

**[INTERP]** The distinctive, *novel* contribution of `My_ML_cc` is the **methodology**:
ML-accelerated convergence and AiiDA-native ML-in-the-loop workflows. The *physics* of
NbSe₂-BdG and impurity Yu–Shiba–Rusinov (YSR) states is **already being written up separately**
(`…/BdG/workflow/papers/arxiv_prep/main.tex`, "pristine multiband anisotropic superconductivity
in bulk 2H-NbSe₂ and impurity-specific YSR states for Mn and Co"). The proposals below are
deliberately steered to **complement, not duplicate**, that physics manuscript.

---

## 2. Reconstruction of what was already done

### 2.1 The compute campaign (AiiDA DB) — [FACT]
The local DB holds **7,668 CalcJobNodes** and **6,416 WorkChainNodes** spanning **2021-04 → 2026-06**.

CalcJob mix:

| CalcJob | count | exit 0 (finished) |
|---|---:|---:|
| `KkrCalculation` (host SCF) | 5,646 | 4,538 |
| `VoronoiCalculation` (startpot) | 1,006 | 851 |
| `KkrimpCalculation` (impurity) | 954 | 779 |
| `FleurinputgenCalculation` / `FleurCalculation` | 33 / 29 | 28 / 22 |

WorkChain mix (top): `kkrimp_BdG_wc` 1,451 · `kkr_imp_dos_wc` 1,336 · `kkr_imp_sub_wc` 939 ·
`kkr_scf_wc` 780 · `kkr_startpot_wc` 745 · `kkr_flex_wc` 331 · `kkr_bs_wc` 283 · `kkr_dos_wc` 206 ·
`kkr_bdg_wc` 84 · `kkr_jij_wc` 57 · **`MLRestartProtocol` 17** · **`KkrWorkChainWithMLMixing` 14** ·
`kkrhost_BdG_wc` 13.

**[FACT]** Organized **groups** record the campaigns, e.g. `NbSe2_2X2Fe(:SOC/:BdGscf_*)`,
`NbSe2_2X2V`, `NbSe2_X2Fe_DLM_host(:SOC/:scnsoc/...)`, `NbSe2_2imp`, `BdG_imps_Mn` (401 nodes),
`Nb110_Bi_FS_matching*`. The DLM host group **`NbSe2_X2Fe_DLM_host` contains 69 `kkr_scf_wc`,
all finished exit 0** (clean, converged) — the FM-vs-DLM data is in good shape.

### 2.1b SCF calculation taxonomy (verified 2026-06-26) — [FACT]
The host SCF runs fall into the expected four buckets. BdG is encoded as input param
`<USE_BDG>=True` (λ_BdG=0.024); CPA/DLM is encoded in the **StructureData** as alloy/weighted
kinds (NOT in the parameters — `NATYP`/`CPAINFO` are null there). **Much of the BdG SCF was run
as standalone `KkrCalculation` calcjobs organized by groups, NOT as workchains** — so the
workchain-only view undercounts BdG badly.

| Type | locus | count | converged (exit 0) |
|---|---|---:|---:|
| Normal SCF | `kkr_scf_wc` | 352 | 86 |
| Normal **CPA/DLM** SCF | `kkr_scf_wc` | 385 | **358** |
| **BdG** SCF (pristine/supercell) | `kkr_bdg_wc`+`kkrhost_BdG_wc` (97) + standalone calcjobs (2×2 Fe 41+23, V 30) | ~190 | ~11 (wc) + **88** (calcjobs) |
| **CPA-BdG** SCF (DLM+BdG) | standalone calcjobs, group `NbSe2_X2Fe_DLM:SOC:BdGscf_onlyNb` | 62 | **62/62** |

Implication: the FM-vs-DLM gap comparison (Proposal 02) has converged BdG data on **both** sides
already — DLM via the 62 CPA-BdG runs, ordered via the supercell-BdG Fe/V runs.

### 2.2 The ML pipeline (this folder) — [FACT]
A complete, runnable ML pipeline already exists:

- **Dataset:** `kkr_scf_metadata.csv` (705 workchains × 42 cols), `kkr_scf_full_dataset.pkl.gz`
  (325 MB), `rms_sequences_*.pkl`, census pickles, `X_soap.npy` / `X_pot.npy` / `X_full_krr.npy`,
  targets `y_iters.npy` / `y_log.npy`, masks `kkr_scf_masks.pkl`, `lodo_indices.npy`.
- **Static models:** KRR and XGBoost with **LODO (Leave-One-Dopant-Out)** CV
  (`krr_lodo_results*.pkl`, `xgb_*`), SHAP/residual diagnostics (`eda_*.png`, `potential_sanity_check.png`).
- **Sequential model:** an **LSTM** on the RMS trajectory predicting *remaining iterations*
  (`lstm_inference.py`, per-dopant folds `lstm_fold_{V,Mn,Fe,Co}.pt`, `lstm_*` artifacts).
- **AiiDA-native deployment:** `aiida_predict.py` (a `@calcfunction` wrapping the LSTM so
  predictions live in provenance) and `workchains/ml_restart_protocol.py`
  (`MLRestartProtocol` WorkChain that runs `kkr_scf` in a loop, predicts remaining iters mid-run,
  and tightens mixing on restart).
- **Notebooks:** `phase3.ipynb`, `Phase 4.ipynb`, `ML_saveData.ipynb`; provenance graph
  `100670.dot.pdf`; a packaged install `pyproject.toml` (`kkr-ml-workchains`).

### 2.3 Did the ML-in-the-loop actually run? — [FACT, important]
Yes, but it is a **proof-of-concept that mostly errored**:
- `MLRestartProtocol`: 17 runs (2026-05-26/27) → **10 excepted, 5 finished with exit 401
  (`ERROR_SCF_FAILED`), 1 killed, 1 excepted-exit-0**. Essentially **0 clean successes**.
- `KkrWorkChainWithMLMixing`: 14 runs → **12 excepted, 1 finished exit 0, 1 excepted-exit-0**.

**[INTERP]** The ML predictor and the workflow scaffolding exist and were wired into AiiDA, but
the closed-loop deployment was not yet debugged to a reliable success. This is the single biggest
gap between "we have a model" and "we have a working ML-accelerated workflow."

---

## 3. Most important AiiDA calculations and nodes

| Role | Identifier | Note |
|---|---|---|
| Pristine BdG SCF host (NbSe₂) | **PK 27923** (`d51dc213`) | λ_BdG=0.024 Ry; finished exit 0 [FACT verified] |
| Fe impurity SCF (m≈2.91 μ_B) | **PK 97088** | `KkrimpCalculation`, finished exit 0 [FACT] |
| Mn / Co / Fe impurity DOS wc | PK 27885 / 27604 / 97199 | `kkr_imp_dos_wc`, finished exit 0 [FACT] |
| Clean FM-vs-DLM Fe host campaign | group **`NbSe2_X2Fe_DLM_host`** | 69 converged `kkr_scf_wc` [FACT] |
| Mn BdG impurity campaign | group **`BdG_imps_Mn`** (401 nodes) | [FACT] |
| ML-in-the-loop runs | `MLRestartProtocol` ×17, `KkrWorkChainWithMLMixing` ×14 | mostly errored [FACT] |
| ML model artifact (in DB) | model_node example PK 103667 | `NbBi_kkr35_linear_capture50`, state=waiting [FACT] |

**[FACT]** Registered codes include `kkrhost_3.5_AMD/intel`, `kkrhost_BdG_AMD`,
`voronoi_3.5_AMD/intel`, `kkrimp_3.5_AMD`, `GPUkkrhost_Nvidia`, and a FLEUR family
(`fleur_MaXR4/5/6`, `inpgen_*`). Cluster: `iffslurm`, user `hemmati`.

---

## 4. Useful existing results (already in hand)

1. **[FACT] A curated SCF-convergence ML dataset** of 705 workchains with input parameters,
   convergence outcome, and full RMS trajectories — 382 converged / 323 not.
2. **[FACT] LODO transferability numbers for the LSTM** (predict remaining iterations from an
   early RMS window):

   | Held-out dopant | n_test | LSTM MAE (iters) | naive MAE | % improvement |
   |---|---:|---:|---:|---:|
   | Mn | 33 | 49.8 | 166.7 | **+54%** |
   | Co | 32 | 57.5 | 166.6 | **+21%** |
   | V  | 157 | 79.4 | 165.8 | **+7%** |
   | Fe | 343 | 97.6 | 168.3 | **−18% (fails)** |

   **[INTERP]** The model beats the naive baseline on 3/4 held-out chemistries but **fails to
   transfer to Fe** (the largest, hardest class) — an honest, publishable mixed result.
3. **[FACT] Observation-window sweep**: shortest window (5 steps) gives the best mean improvement
   (~8%), i.e. **early prediction is feasible** and adding more steps did not help in this setup.
4. **[FACT] Static KRR baseline** (predict *total* iterations from input features): Fe MAE≈226,
   RMSE≈512 over a 5–1068 iteration range — static prediction of total cost is hard; the
   sequential model is the stronger track.
5. **[FACT] A clean FM-vs-DLM Fe-on-NbSe₂ host dataset** (69 converged SCF) ready for a
   pair-breaking / `xc` physics analysis.
6. **[FACT] A real, provenance-recorded ML-in-the-loop workflow** (`MLRestartProtocol`,
   `@calcfunction` predictor) — novel as *infrastructure*, even though the closed loop is not yet
   reliable.

---

## 5. Missing information / gaps

- **[OPEN]** `USE_BDG` is null for 688/705 rows in the CSV (only `LAMBDA_BDG_parsed` is populated,
  376 rows). The BdG-vs-normal split needs to be re-derived from the input parameters before any
  BdG-specific ML claim. **[NEXT]** re-extract `USE_BDG`/`LAMBDA_BDG` from each workchain's input Dict.
- **[OPEN]** The CSV mixes ≥2 physical systems (NbSe₂ *and* Bi/NbBi slabs; formulas `Bi4X12`,
  `Nb2Se4X2`, `Fe48`, …). Convergence behaviour is system-dependent; models trained across all of
  them may be confounded. **[NEXT]** add a `system_family` column and stratify.
- **[OPEN]** The **gap data** `delta/delta0(x)` is *not* in this folder; help files point to
  `paper6/*delta*.json` in the physics repo, which I did **not** find on disk (only
  `bdg_gap_convergence.png`). **[NEXT]** locate or re-extract `delta` per converged BdG run
  (filter `final_rms < 1e-6`) before any `xc` surrogate.
- **[OPEN]** Why the `MLRestartProtocol` runs excepted (exit 401 / exceptions) is not yet diagnosed.
  **[NEXT]** read `verdi process report` on a few of PKs 100992–101281 (read-only) to find the failure cause.
- **[OPEN]** `kkr_jij_wc` (exchange interactions): 57 runs but **only 4 finished exit 0** (28
  excepted, 13/12 exit 163/162). The Jij dataset is currently too thin to support a paper.

---

## 6. Possible research directions (only those supported by the data)

| # | Direction | Type | Evidence in DB | Verdict |
|---|---|---|---|---|
| **A** | **ML-accelerated SCF convergence + ML-in-the-loop restart for KKR(-BdG)** | Methods / ML4Science | 705-wc dataset, LSTM LODO, `MLRestartProtocol`×17 | **Strongest, most novel, self-contained** |
| **B** | **Magnetic pair-breaking & gap suppression in TM-doped NbSe₂: FM vs DLM, critical xc** | Physics | DLM host (69 converged), BdG imp campaigns | Promising but **overlaps the existing YSR paper**; needs delta extraction |
| **C** | **Open reproducible KKR-BdG convergence dataset + benchmark / failure-mode taxonomy** | Data / benchmark | full 7,668-calc provenance, rich exit-code spectrum | Low-risk companion; needs packaging |
| D | Exchange interactions (Jij) trends across dopants | Physics | `kkr_jij_wc` only 4 converged | **Too thin — not yet** |
| E | SOC / anisotropy effects on YSR | Physics | SOC groups exist | **Belongs to the existing physics paper** |

---

## 7. Most promising for a publishable PhD project

**Primary recommendation: Direction A** (Proposal 01) — *ML-accelerated SCF convergence for
KKR-BdG Green-function calculations, with an AiiDA-native ML-in-the-loop restart protocol.*
It is (i) the genuinely novel contribution of this folder, (ii) ~70% already done, (iii)
self-contained and not in conflict with the existing physics manuscript, and (iv) a natural fit
for a strong ML-for-materials venue.

**Strong companion: Direction C** (Proposal 03) — a curated, openly released convergence dataset
+ benchmark is low-risk, leverages the full provenance DB, and gives Proposal 01 a citable
data backbone (and is itself a publishable "data descriptor").

**Higher-value but higher-effort: Direction B** (Proposal 02) — the FM-vs-DLM `xc` physics is
scientifically richer, but must be carved out so it does not collide with the YSR manuscript and
needs additional converged BdG points near `xc`.

---

## 8. Risks, uncertainties, missing calculations

- **Overlap risk (B/E):** the NbSe₂-BdG/YSR physics is already in an arXiv-prep manuscript;
  Proposal 02 must claim a *distinct* angle (finite-T DLM disorder + `xc`), not the single-impurity
  YSR spectroscopy.
- **Label hygiene (all):** `delta` is only trustworthy at `final_rms < ~1e-6`; many runs plateau at
  ~1e-2 with poisoned labels (per help1 §5). Any gap-based claim must filter on convergence first.
- **Dataset confounds (A/C):** mixed material families and a null `USE_BDG` column must be fixed
  before headline ML numbers.
- **Deployment gap (A):** the closed-loop `MLRestartProtocol` does not yet succeed; the paper can
  honestly present it as a prototype + diagnosis, but a few clean successful loops would
  dramatically strengthen it. **[NEXT-CALC]** re-run a handful of `MLRestartProtocol` jobs after
  debugging (this *does* submit jobs — requires your go-ahead; out of scope for this read-only task).
- **`xc` coverage (B):** locating `xc` for FM vs DLM may need extra concentration points
  (new CPA-BdG runs) — a later, optional compute campaign.

---

## 9. Concrete next-step plan (ranked)

1. **Read first:** `help0/1/2.md` (done), then `phase3.ipynb` and `Phase 4.ipynb` to see exactly
   how the current LSTM/KRR numbers were produced.
2. **Verify first (read-only, no submits):**
   - Re-derive `USE_BDG` / `LAMBDA_BDG` and a `system_family` label from each workchain's input Dict.
   - Run `verdi process report` on 3–4 excepted `MLRestartProtocol` PKs to diagnose the loop failure.
   - Recompute LSTM/KRR LODO restricted to **NbSe₂-only** rows to remove the cross-material confound.
3. **Turn into figures (no new compute):** LODO MAE-vs-naive bar chart; RMS-trajectory gallery with
   convergence/failure classes; observation-window vs accuracy curve; SHAP feature importance;
   a provenance-graph schematic of the ML-in-the-loop workflow.
4. **Later calculations (needs your approval — submits jobs):** debug + re-run ~10 `MLRestartProtocol`
   loops to obtain clean successes; (optional, Proposal 02) a small CPA-BdG `xc` scan for FM vs DLM.
5. **Could become a paper:** Proposal 01 first (most complete), with Proposal 03 as a companion data
   descriptor; Proposal 02 as a follow-on physics paper.

---

## 10. Suggested paper structure (for the lead paper, Proposal 01)

1. **Intro** — KKR-BdG SCF convergence is expensive and fragile; motivate ML acceleration; relate
   to active-learning / surrogate trends in computational materials.
2. **Data** — the AiiDA provenance dataset; features (input kkrparams + start-potential + SOAP) vs
   targets (iterations, final RMS, RMS trajectory); LODO protocol; label hygiene.
3. **Methods** — static (KRR/XGBoost) vs sequential (LSTM) predictors; the AiiDA `@calcfunction`
   predictor; the `MLRestartProtocol` closed loop.
4. **Results** — LODO transferability (incl. the Fe failure), early-prediction window study, feature
   importance, and the prototype closed-loop runs (honest status).
5. **Discussion** — what transfers across chemistries and what doesn't; reliability of KKR-BdG SCF;
   implications for high-throughput superconductor screening.
6. **Reproducibility** — released dataset/benchmark (Proposal 03), code, provenance UUIDs.

See `proposal_01_ml_scf_convergence/`, `proposal_02_dlm_pairbreaking_nbse2/`, and
`proposal_03_kkr_bdg_dataset_benchmark/` for the full per-proposal write-ups.
