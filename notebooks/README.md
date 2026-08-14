# notebooks/

Two notebooks:
1. **`potentialbank_v1_walkthrough.ipynb`** — AiiDA-free tour of the frozen PotentialBank v1 artifact (below).
2. **`aiida_kkr_mlassist_submission_walkthrough.ipynb`** — beginner-friendly guide to *using* the package with
   AiiDA: load codes, pick a structure, read advisor tips, build cold/warm-start KKR jobs, and **optionally**
   submit. **Safe by default — nothing submits unless you explicitly flip a switch** (see its own section).

---

## `potentialbank_v1_walkthrough.ipynb`
An **AiiDA-free** walkthrough of the frozen **PotentialBank v1** artifact for reviewers/users. It reads only
the committed/packaged artifacts (manifest, coverage/warm-start tables, advisor index) — **no** AiiDA DB, HPC,
daemon, raw potential files, or Materials Project API. All numbers are loaded from the CSV/JSON artifacts (not
fabricated), and the frozen headline (237 unique / 238 nodes / 8 families / 33 F2-eligible) is asserted in code.

## How to run
Minimal dependencies — plain scientific Python (no AiiDA, no scikit-learn):
```bash
python -m venv .venv && source .venv/bin/activate      # or use an existing env
pip install pandas matplotlib jupyter                   # the only extras needed
```
These are **not** added to `pyproject.toml` (the package runtime is numpy-only by design); the notebook is a
standalone doc, so its deps are installed ad hoc.

Run either way — the notebook resolves the repo root automatically (walks up until it finds
`reports/potentialbank_v1/`), so it works from the **repo root** or from **`notebooks/`**:
```bash
# from the repo root
jupyter nbconvert --to notebook --execute --inplace notebooks/potentialbank_v1_walkthrough.ipynb
# or open interactively
jupyter lab notebooks/potentialbank_v1_walkthrough.ipynb
```

## What it covers
1. Purpose + frozen headline (verified from artifacts)
2. Loading the packaged artifacts
3. Manifest overview (counts, fields, duplicate-sha check)
4. Coverage by family and compatibility class (plots)
5. E1 certification rules + real example rows (MgO/NaCl/Si/Ge/TiSe₂)
6. Warm-start benchmark (per-family, warm-vs-cold + savings plots)
7. Advisor index — optional advisory tips
8. Deferred / parked hard cases
9. Claim ladder (allowed / disallowed)
10. Reproducibility (MANIFEST.sha256 checksum verify + VERSION)

**Scope:** certified same-structure donor reuse only — no cross-material transfer, no guaranteed acceleration;
CPA/BdG out of scope for PotentialBank v1.

`build_notebook.py` regenerates the notebook from the artifacts.

## `aiida_kkr_mlassist_submission_walkthrough.ipynb`
A **beginner-friendly** (bachelor physics, minimal Python/Jupyter) guide to preparing and optionally submitting
KKR jobs with this package. Structure: safety banner → how-to-use-Jupyter → imports/safe-mode → **config cell
you edit** → load codes → pick a structure → advisor tips → cold builder → warm-start builder → multi-job plan
table → optional `ml_assist` **advisory** builder → pre-flight PASS/FAIL → **gated submission cell** → monitor →
read results → claims/limits → checklist.

### Safety model (important)
Nothing submits unless **you** edit the switches near the top:
```python
DRY_RUN = True                                        # keep True to prepare-only
I_UNDERSTAND_THIS_WILL_SUBMIT_TO_HPC = False          # set True to submit
I_UNDERSTAND_ABORT_MODE_CAN_STOP_CALCULATIONS = False # abort mode needs THIS too (experts only)
```
The submission cell refuses while `DRY_RUN` is True or the submit switch is False. `ml_assist` defaults to
**advisory** (records signals, never aborts). Tutorial jobs are labelled `_EXCLUDE`.

### Requirements
- Read-only parts (advisor/PotentialBank) need **no AiiDA** — just `pandas` (optional) for the plan table.
- Submission parts need a working **AiiDA** profile with your KKR/Voronoi codes. Fill your real code labels and
  structure pk in the config cell.
- The notebook **auto-skips** AiiDA cells with a friendly message if AiiDA is not configured, so it never
  crashes. (Setting env `POTBANK_NB_NO_AIIDA=1` forces this offline mode — used for automated testing.)

### Companion
`AIIDA_SUBMISSION_WALKTHROUGH.md` is a plain-text version of the same guide for reading on GitHub without
opening the notebook.
