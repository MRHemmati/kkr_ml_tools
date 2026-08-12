# `ml_assist` — MVP design for an ML-enabled KKR SCF workflow

*Design sketch, 2026-06-30. Productizes Proposal 01. Grounded in the validated results
(retrospective LODO AUC ~0.96, prospective AUC 0.967, cross-material transfer AUC 0.942) and the
known limitations (staged-mixing blind spot; per-material threshold; mock-prototype + env lessons).*

## 1. Goal and guiding principles
A frictionless, opt-in trigger on the standard `kkr_scf_wc` that fuses **prior** knowledge (a model
trained on the whole body of past KKR runs) with the **online** signal of the specific job, to give
users an enhanced, compute-saving SCF experience.

Principles:
- **First, do no harm.** `enabled=False` ⇒ byte-identical to vanilla `kkr_scf_wc`. On any ML error or
  low confidence ⇒ silently fall back to vanilla behavior. Never worse than not using it.
- **Earn trust before acting.** Default mode is *advisory* (predict + annotate, never act). Aborting is
  opt-in and conservative.
- **Provenance-native + reproducible.** The model is a versioned `SinglefileData` node; predictions are
  `@calcfunction`s so every decision is in the graph with the model UUID recorded.

## 2. Scope — MVP vs later (be honest about what's solved)
| Capability | Status | Phase |
|---|---|---|
| Advisory convergence prediction (annotate P(converge)) | validated, deployable | **MVP** |
| Conservative early-abort of high-confidence failures | validated (≈0% false-abort at thr 0.3) | **MVP (opt-in)** |
| Schedule-aware observation window (staged mixing) | designed below | **MVP** |
| OOD guard → advisory fallback for distant systems | designed below | **MVP** |
| Warm-start mixing from structure descriptors (prior → good strmix) | partial (sweet spot known for NbSe2) | v2 |
| Online per-material threshold calibration | identified need (rates differ, ranking transfers) | v2 |
| Auto-**retune** mixing to *rescue* a run (closed loop) | NOT solved (mock prototype; staged blind spot) | v3 (research) |
| BdG support | blocked (plugin/env) | later |

## 3. API
A thin wrapper `MLAssistedKkrScfWorkChain` exposing all `kkr_scf_wc` inputs plus an `ml_assist`
namespace:
```
ml_assist:
  enabled:         Bool   (default False)        # the trigger
  model:           SinglefileData                # versioned, pinned classifier bundle
  mode:            Str    ∈ {advisory, abort}    # default advisory
  abort_threshold: Float  (default 0.10)         # abort only if P(converge) < this (conservative)
  observe_iters:   Int    (default 10)           # window length AFTER the warmup phase
  ood_action:      Str    ∈ {advisory, off}      # what to do when out-of-distribution
```

## 4. Control flow (outline)
```python
class MLAssistedKkrScfWorkChain(WorkChain):
    # exposes kkr_scf_wc inputs + ml_assist namespace; importable PACKAGE module
    # (NOT __main__ — the lesson from the excepted prototype runs)
    outline(
        cls.setup,
        if_(cls.ml_disabled)(
            cls.run_vanilla_scf,                 # zero overhead, identical to kkr_scf_wc
        ).else_(
            cls.run_until_observable,            # SCF until warmup done + observe_iters past switch
            cls.predict,                         # @calcfunction: features -> P(converge) (+OOD score)
            cls.decide,                          # advisory: annotate & continue | abort: maybe stop
            cls.finish_scf,                      # continue to completion if not aborted
        ),
        cls.results,                             # SCF outputs + ml_prediction annotation
    )
```

Key steps:
- **`run_until_observable`** — the staged-mixing fix. Do NOT predict at a fixed iteration 10. Wait
  until (a) the straight-mixing warmup is over (Broyden engaged; from `NSIMPLEMIXFIRST`/the workchain's
  switch, or detected as the slope kink) AND (b) `observe_iters` iterations of the *aggressive* phase
  have elapsed. This ensures the observation window reflects the dynamics that decide convergence,
  closing the blind spot we quantified (~15% flat-but-recovers trap).
- **`predict`** — `@calcfunction` (provenance-preserving, like `aiida_predict.py`): load the model
  bundle, build the first-`observe_iters` features from the live `output_parameters.convergence_group`,
  return `{P_converge, ood_score, model_uuid, window}`.
- **`decide`**:
  - *advisory*: attach `ml_prediction` as output/extra; always continue.
  - *abort*: if `not OOD` and `P_converge < abort_threshold` ⇒ stop with a clear exit code
    (`ERROR_ML_PREDICTED_NONCONVERGENCE`) and the prediction; else continue.
  - if `OOD` ⇒ downgrade to advisory (per `ood_action`).

## 5. Design decisions tied to our findings
- **Conservative threshold (0.10, not 0.50).** Our data: at the conservative operating point, ~0%
  false-abort while still catching ~82% of failures (36% compute saved). Protects user trust; most
  uncertain runs simply continue.
- **OOD guard.** Cross-material transfer is good (NbSe2→Bi AUC 0.942) but NOT proven universal. A
  simple OOD score (distance of the early-trajectory features / structure descriptors from the training
  distribution) gates confident action; distant systems get advisory-only.
- **Ranking transfers, threshold doesn't.** Absolute convergence rates differ by material; for MVP we
  use a fixed conservative threshold (safe), and flag per-material *calibration* as v2 (the natural job
  of the "online" half).
- **Reproducibility.** Pin the model node UUID; record it on every decision; never silently swap models.

## 6. Engineering requirements (from lessons learned)
- **Importable package**, not `__main__` (the prototype excepted with `ModuleNotFoundError` /
  `__main__:...` — daemon couldn't re-import). Ship as `kkr-ml-workchains` with a proper entry point.
- **Inference must run in the daemon's env.** sklearn is absent from `/opt/aiida-kernel`; either add it
  to the daemon env or export the model to a dependency-light format (e.g., a small pure-numpy decision
  rule / ONNX). Decide before deployment.
- **Correct input wiring** (`calc_parameters`/`wf_parameters` namespaces — the other prototype bug).

## 7. Rollout & validation (build trust + the data flywheel)
1. **Shadow/advisory mode** — predict and annotate on real user runs, never act. Measures live
   prediction-vs-outcome agreement (extends the prospective AUC) and collects labelled trajectories
   ⇒ the flywheel. Zero risk.
2. **Enable conservative abort** once shadow mode confirms low false-abort in production.
3. **v2** — warm-start mixing + online threshold calibration. **v3** — schedule-aware auto-retune (the
   research piece).

## 8. Minimal build checklist (MVP)
- [ ] Package `MLAssistedKkrScfWorkChain` (importable; exposes kkr_scf_wc + ml_assist).
- [ ] `predict` `@calcfunction` reusing the validated feature extractor + frozen model bundle (as a
      stored, versioned `SinglefileData`).
- [ ] Schedule-aware `run_until_observable` (detect warmup end / Broyden switch).
- [ ] Conservative `decide` (advisory default; opt-in abort; OOD fallback).
- [ ] Daemon-env inference path sorted (sklearn or exported model).
- [ ] Shadow-mode deployment + a small live validation (like the grid campaign).
