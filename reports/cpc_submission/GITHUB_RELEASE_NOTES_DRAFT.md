# GitHub release notes (draft) — `v1.0.0`

*(Draft for the release that would be created **at real release time**. No tag/release is created here.
**Recommended tag: `v1.0.0`** — a single citable label over the package (`0.1.1`) and the PotentialBank v1 data
release. Author: Mohammad Hemmati (Forschungszentrum Jülich / RWTH Aachen).)*

---

## v1.0.0 — aiida-kkr-mlassist + PotentialBank v1 + KKR Convergence Advisor

**Provenance-certified KKR convergence assistance and same-structure warm-start reuse.**

This release accompanies the Computer Physics Communications software/method manuscript. It packages three
complementary pieces:

- **`ml_assist`** — an AiiDA-native, opt-in early-abort convergence controller (pure-`numpy` scorer + RMS@10
  baseline under a per-cohort conformal policy). The abort *mechanism* is validated live; broad ML transfer is
  **not** claimed (it does not beat RMS@10 out-of-sample and needs per-cohort recalibration).
- **PotentialBank v1** — a certified catalog of single-structure converged KKR potentials for reproducible
  **same-structure** warm starts. Frozen at **237 unique certified donors (238 nodes), 8 families, 33
  F2-eligible materials**. AiiDA-KKR already provides the restart / `potential_overwrite` primitives; this adds
  the **certification/retrieval layer** (byte-exact SHA-256 integrity, exact Z-sequence/NATYP compatibility,
  non-CPA/non-BdG scope, no guessed mapping).
- **KKR Convergence Advisor** — an offline, advisory-only helper exposing optional donor-start tips and parked
  hard-case warnings.

### What's included
- Installable package (`pip install aiida-kkr-mlassist`; numpy-only runtime core), with entry points
  `kkr.mlassist` and `kkr.bdg`.
- Frozen model artifacts (`.npz`) with SHA-256 manifests and a model card.
- The PotentialBank v1 manifest, coverage/warm-start tables, and figures.
- The advisor index (`advisor_index_v1.json`) + example tips, shipped as package data.
- Unit tests, and two walkthrough notebooks (an AiiDA-free tour and a safe-by-default submission tutorial).
- The technical report (PDF + LaTeX).

### Scope and limitations (please read)
- **Same-structure reuse only** — **no cross-material transfer, no guaranteed acceleration.**
- **CPA / disordered / BdG are out of scope** for PotentialBank v1.
- **Raw KKR potential files are not redistributed** — the bank references them by SHA-256 and AiiDA provenance;
  reproducing live runs requires the JuKKR codes and the author's AiiDA database + cluster access.

### Install
```bash
pip install aiida-kkr-mlassist            # numpy-only core
pip install "aiida-kkr-mlassist[aiida]"   # + aiida-core / aiida-kkr, to submit
```

### Artifacts (dry-run build; recompute at real release)
- `aiida_kkr_mlassist-0.1.1-py3-none-any.whl` — sha256 `dcb88719…a176b7`
- `aiida_kkr_mlassist-0.1.1.tar.gz` — sha256 `c2feb730…2b279b`

### Citation
Cite the CPC manuscript (DOI on acceptance) and this release's Zenodo DOI (minted at release time).
