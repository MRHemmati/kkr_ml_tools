# Release checklist (pre-CPC-submission)

Ordered steps to turn the current branch into a citable release. **None of these are performed in this stage**
(no build, no tag, no upload, no commit) — this is the checklist to execute later, with approval.

| # | step | status now | note |
|---|---|---|---|
| 0 | **Fill author/affiliation/CRediT/acknowledgments** | ⚠️ TODO (author) | `main.tex` has placeholders (`\author{...\thanks{TODO}}`, CRediT section, Acknowledgments). Fill name/affiliation/email/ORCID/CRediT/funding before submission. |
| 1 | **Choose/verify license** | ✅ **DONE (Z1)** | `LICENSE` (MIT, "Copyright (c) 2026 M. R. Hemmati") added at repo root; matches `pyproject.toml`. |
| 2 | **Run tests** | ✅ offline tests pass | `PYTHONPATH=src python tests/*.py` (advisor 11/11 + 6 more PASS; `test_mondrian` needs `[aiida]` extra). |
| 3 | **Build wheel/sdist** | ☐ not built here | `python -m build` → `dist/*.whl`, `dist/*.tar.gz`. (A prior wheel `aiida_kkr_mlassist-0.1.1` exists from earlier; rebuild before release.) |
| 4 | **Version wording** | ✅ **RESOLVED (Z1)** | Not a bug: package `aiida-kkr-mlassist` `0.1.1` and the data release *PotentialBank v1* are versioned independently. Stated explicitly in `main.tex` (availability §) so reviewers do not read it as an inconsistency. Bump only if desired. |
| 5 | **Create GitHub release/tag** | ☐ not done | e.g. tag on `MRHemmati/kkr_ml_tools`; not performed (no release action authorized). |
| 6 | **Archive on Zenodo (or equiv.)** | ☐ not done | enable the GitHub–Zenodo hook; the release mints a DOI. |
| 7 | **Record DOI in manuscript** | ☐ TODO | insert the Zenodo DOI into the Software Availability section + Program Summary. |
| 8 | **Verify no secrets/API keys** | ✅ verified | repo grep for api_key/secret/password/PEM/MP_API_KEY → none. |
| 9 | **Verify no raw potential files** | ✅ verified | no `out_potential`/`*.pot`/`potential` blobs tracked; bank references SHA/provenance only. |
| 10 | **Verify notebooks open** | ✅ verified | both notebooks execute to exit 0 (submission one via `POTBANK_NB_NO_AIIDA=1`). |
| 11 | **Verify PDF compiles** | ✅ verified | `pdflatex ×2` → 18 pp, 0 undefined refs/citations. |
| 12 | **Verify `git status`** | ✅ **RESOLVED (Z1)** | stray `reports/technical_report.tar` moved to `workspace/temporary_not_for_git/` (out of repo tree); `*.tar` added to `.gitignore`; `notebooks/.ipynb_checkpoints/` already ignored. |
| 13 | **Exclude build artifacts** | ✅ | `dist/`, `*.tar`, `__pycache__`, `.ipynb_checkpoints/` all ignored. |

## Final steps for actual CPC submission (in order)
1. **Fill author/affiliation/acknowledgment** front matter (placeholders in `main.tex`): full name(s),
   affiliation, email, ORCID, CRediT roles, funding/allocations.
2. **Run tests** (`PYTHONPATH=src python tests/*.py`) and recompile the PDF.
3. **Build wheel/sdist** (`python -m build`).
4. **Create a GitHub release tag** on `MRHemmati/kkr_ml_tools`.
5. **Archive the release on Zenodo** (or equivalent) to mint a DOI.
6. **Insert the DOI** into the manuscript (availability § + Program Summary).
7. **Submit the CPC CPiP package** (manuscript PDF, highlights, keywords, Program Summary, cover letter,
   declarations) through the Elsevier editorial system.

**Remaining blockers (author-supplied):** front-matter author/CRediT/acknowledgment content, and the Zenodo DOI.
License, version wording, and the stray tarball are resolved (Z1).
