# AiiDA KKR submission walkthrough (plain-text companion)

A readable version of `aiida_kkr_mlassist_submission_walkthrough.ipynb` for browsing on GitHub without opening
the notebook. For beginners (bachelor physics; minimal Python/Jupyter). **Nothing here submits by default.**

## ⚠️ Safety first
Three switches live near the top of the notebook and are all **off** by default:
```python
DRY_RUN = True                                        # prepare & print only
I_UNDERSTAND_THIS_WILL_SUBMIT_TO_HPC = False          # set True to actually submit
I_UNDERSTAND_ABORT_MODE_CAN_STOP_CALCULATIONS = False # abort mode needs this too (experts only)
```
You can run every cell top-to-bottom safely; it only *prepares* jobs and *prints plans*. The single submission
cell **refuses** unless `DRY_RUN = False` **and** `I_UNDERSTAND_THIS_WILL_SUBMIT_TO_HPC = True`.

## How to use Jupyter (60-second version)
- A notebook is a list of **cells** (boxes). Click a cell, press **Shift+Enter** to run it; output appears below.
- Run cells **in order**. Edit the one **configuration cell**. A red error is not dangerous — read the last
  line, fix the config, re-run.

## The steps
1. **Imports & safe mode.** Tries to import AiiDA; if unavailable, the read-only advisor parts still work and
   submission cells skip with a friendly message (they never crash).
2. **Configuration (edit this).** Set your AiiDA profile, KKR/Voronoi **code labels**
   (`kkrhost_3.5_intel@iffslurm`, `voronoi_3.5_intel@iffslurm`), partition (`th1`), ranks (`12` — divides the
   24/48-point energy contours), walltime, your `STRUCTURE_PK`, and an optional `DONOR_PK`.
3. **Load codes.** Loads the profile (read-only) and your two codes; if a label is wrong it tells you to run
   `verdi code list`.
4. **Pick a structure.** Loads your `StructureData` by pk, or lists a few recent ones so you can choose. A
   helper `describe_structure()` prints formula / sites / date.
5. **Advisor / PotentialBank (no AiiDA needed).** Loads the frozen v1 catalog (237 unique donors, 8 families,
   33 F2-eligible) and prints **optional** tips for MgO/NaCl/Si/Ge/TiSe₂/Fe and warnings for WSe₂/MoS₂.
6. **Cold builder.** Fills a `kkr.scf` builder from a fresh Voronoi start. Conservative defaults: normal-state,
   non-CPA, **no SOC** unless you opt in, `convergence_criterion=1e-5`, `coarse_preconvergence=True`.
7. **Warm-start builder.** Injects a **certified same-structure donor** potential via `startpot_overwrite`
   (with a SHA-256 print). Certification matters; the notebook does **not** certify new donors.
8. **Several jobs (plan table).** A list of dicts (rows = jobs) → built in a loop → a `will_submit=False` plan
   table (needs `pandas`, optional).
9. **`ml_assist` advisory (optional).** Builds an advisory-only run (`{"enabled": True, "mode": "advisory",
   "alpha": 0.10}`) that records signals but never aborts. Abort mode is gated behind **both** switches.
10. **Pre-flight checks.** PASS/FAIL table: profile, codes, structure, grid-valid ranks, donor exists, no SOC,
    `_EXCLUDE` labels, submit switch.
11. **Submission cell (disabled by default).** Only place that can submit; refuses unless both switches flipped.
12. **Monitor & read results.** `summarize_workchain(pk)` and `read_results(pk)` helpers (read-only; never kill
    jobs). Terminal equivalents: `verdi process list`, `verdi process status <pk>`.

## Claims & limitations (keep honest)
- Helps you **prepare real KKR jobs**; PotentialBank v1 = certified **same-structure** donor reuse.
- Advisor tips are **optional**. **No cross-material transfer.** **No guaranteed acceleration.** **CPA/BdG out
  of scope** for this tutorial.
- `ml_assist`: early-abort **mechanism validated live**, but **broad ML transfer not proven** — deploy
  per-campaign, advisory-first.
