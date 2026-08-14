# Zenodo metadata (draft)

*(Draft for the archival deposit that would be created **at real release time**. Nothing is uploaded here; no
DOI is minted. Placeholders in [brackets] are author-supplied.)*

- **Title:** aiida-kkr-mlassist / KKR Convergence Advisor / PotentialBank v1 — provenance-certified KKR
  convergence assistance and same-structure warm-start reuse
- **Upload type:** Software
- **Version:** package `0.1.1`; data release `PotentialBank v1` (versioned independently — see the manuscript).
  **Recommended release/tag label: `v1.0.0`** (unifies package + data release under one citable version).
- **Authors / creators:**
  - Mohammad Hemmati — Peter Grünberg Institut and Institute for Advanced Simulation, Forschungszentrum Jülich
    and JARA, D-52425 Jülich, Germany; RWTH Aachen University, D-52062 Aachen, Germany. ORCID: 0009-0006-4205-5706.
  - *(Sole author — no co-authors for this deposit.)*
- **License:** MIT (open source; `LICENSE` at repo root).
- **Related identifiers:**
  - *is supplement to* — the CPC manuscript (DOI assigned by the journal on acceptance).
  - *is derived from* — aiida-kkr / JuKKR (Rüßmann, Bertoldo & Blügel, *npj Comput. Mater.* **7**, 13, 2021,
    DOI 10.1038/s41524-020-00482-5).
  - *is identical to* — the GitHub release tag on `https://github.com/MRHemmati/kkr_ml_tools`.
- **Keywords:** KKR Green-function DFT; SCF convergence; AiiDA provenance; potential reuse / warm start;
  conformal prediction; reproducible workflows; certified donor potentials.
- **Description (abstract):**
  > An AiiDA-native, opt-in convergence-control framework (`ml_assist`) plus **PotentialBank v1**, a
  > provenance-certified catalog of single-structure converged KKR potentials for reproducible same-structure
  > warm starts. AiiDA-KKR already provides the restart / `potential_overwrite` primitives; the contribution is
  > the certification and retrieval layer above them — byte-exact SHA-256 integrity, exact Z-sequence / NATYP
  > compatibility, non-CPA / non-BdG scope control, and no guessed mapping — with an optional convergence
  > advisor whose limits are explicitly benchmarked. PotentialBank v1 is frozen at 237 unique certified donors
  > (238 nodes) across 8 material families and 33 F2-eligible materials. Scope: certified same-structure reuse —
  > no cross-material transfer and no guaranteed acceleration; CPA/BdG out of scope. Raw potential data are not
  > redistributed; they are referenced by SHA-256 and AiiDA provenance.
- **Notes:** the archive contains the software package (wheel + sdist), tests, frozen model artifacts with
  SHA-256 manifests, the PotentialBank v1 manifest / tables / figures, the advisor index, notebooks, and the
  technical report. **Raw KKR potential files are intentionally excluded** (referenced by hash/provenance).
- **Funding:** Bavarian Ministry of Economic Affairs, Regional Development and Energy — High-Tech Agenda Project
  "Bausteine für das Quantencomputing…"; and DFG under Germany's Excellence Strategy — Cluster of Excellence
  Matter and Light for Quantum Computing (ML4Q) EXC 2004/1 – 390534769. *(Computing-time allocation: TODO — this
  work used iffslurm at Forschungszentrum Jülich; insert the correct allocation once known.)*
- **Language:** English. **Programming language:** Python.

## Build artifacts to attach (this dry run)
| file | size | sha256 |
|---|---|---|
| `aiida_kkr_mlassist-0.1.1-py3-none-any.whl` | 1.36 MB | `dcb88719b507aef905f75fcbe103ebb7735ee510078101acebdd4d3190a176b7` |
| `aiida_kkr_mlassist-0.1.1.tar.gz` (sdist) | 1.33 MB | `c2feb7306a0ba548bf636ba6caa24d2eae31aa3a499bd01f35b9cd5c192b279b` |

*(Checksums are from the Stage-Z2 dry-run build; rebuild and recompute at real release time, after front-matter
and any version reconciliation.)*
