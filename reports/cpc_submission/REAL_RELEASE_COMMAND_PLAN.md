# Real release command plan (DO NOT RUN until approved)

Exact commands for the future release of `MRHemmati/kkr_ml_tools`. **None are run in Stage Z3.** Prerequisites:
author metadata filled (`AUTHOR_METADATA_TODO.md`), PDF recompiled, tests green. Recommended tag: **`v1.0.0`**.

## 0. Pre-flight (read-only)
```bash
cd git/kkr_ml_tools
git status --short --branch              # expect clean (commit metadata fill-in first)
PYTHONPATH=src python tests/test_advisor.py    # 11/11
( cd reports/technical_report && pdflatex -interaction=nonstopmode main.tex >/dev/null && \
  pdflatex -interaction=nonstopmode main.tex >/dev/null )   # 0 undefined refs
```

## 1. Commit the metadata fill-in
```bash
git add reports/technical_report/main.tex reports/technical_report/main.pdf \
        reports/cpc_submission/ AUTHOR_METADATA_TODO.md LICENSE
git commit -m "CPC: fill author metadata; finalize release drafts"
```

## 2. (Optional) merge branch to main
Only if the release should live on `main`:
```bash
git checkout main && git merge --no-ff mlassist-current-report-d1b && git checkout mlassist-current-report-d1b
```
(Otherwise tag the current branch directly.)

## 3. Rebuild clean artifacts
```bash
python -m venv /tmp/relvenv && /tmp/relvenv/bin/pip install build
rm -rf dist && /tmp/relvenv/bin/python -m build --outdir dist .
sha256sum dist/*                          # record for Zenodo + release notes
```

## 4. Create + push an annotated tag
```bash
git tag -a v1.0.0 -m "aiida-kkr-mlassist + PotentialBank v1 + KKR Convergence Advisor (v1.0.0)"
git push origin v1.0.0
git push origin mlassist-current-report-d1b   # (or main)
```

## 5. Create the GitHub release
**With `gh` (GitHub CLI):**
```bash
gh release create v1.0.0 dist/*.whl dist/*.tar.gz \
  --repo MRHemmati/kkr_ml_tools \
  --title "v1.0.0 — aiida-kkr-mlassist + PotentialBank v1" \
  --notes-file reports/cpc_submission/GITHUB_RELEASE_NOTES_DRAFT.md
```
**Safe path (no `gh` / not GitHub CLI):** on github.com → *Releases* → *Draft a new release* → choose tag
`v1.0.0` → paste `GITHUB_RELEASE_NOTES_DRAFT.md` → attach the two `dist/` files → *Publish release*.

## 6. Archive with Zenodo (DOI)
- One-time: enable the **GitHub ↔ Zenodo** integration for the repo (zenodo.org → GitHub → toggle the repo ON)
  **before** creating the release; publishing the release then auto-creates a Zenodo deposit.
- If already released, use zenodo.org → *New upload*, attach the same `dist/` files, and paste
  `ZENODO_METADATA_DRAFT.md`. Reserve/mint the DOI.
- **Safe path:** the Zenodo web UI (no CLI needed).

## 7. Insert the DOI into the manuscript
```bash
# edit reports/technical_report/main.tex:
#   - Software & data availability section: add "archived at Zenodo, DOI: 10.5281/zenodo.XXXXXXX"
#   - Program Summary "CPC library link / repository" line: add the DOI
( cd reports/technical_report && pdflatex -interaction=nonstopmode main.tex >/dev/null && \
  pdflatex -interaction=nonstopmode main.tex >/dev/null )
```

## 8. Commit the DOI update
```bash
git add reports/technical_report/main.tex reports/technical_report/main.pdf
git commit -m "Record Zenodo DOI in manuscript"
git push origin mlassist-current-report-d1b
```

## 9. Submit to CPC
Upload the manuscript PDF + highlights + keywords + Program Summary + cover letter + declarations through the
Elsevier editorial system (`Computer Programs in Physics` article type). Not a git action.

---
**Order note:** do steps 1–4 (commit + tag + build), then **enable Zenodo before publishing the GitHub release**
(step 6 before/at step 5) so the DOI is minted automatically; otherwise use the Zenodo UI after the release.
