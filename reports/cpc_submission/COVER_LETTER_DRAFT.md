# Cover letter (draft)

*(Draft — sole author Mohammad Hemmati; not sent. Fill the journal-specific date/editor salutation at
submission.)*

To the Editors, Computer Physics Communications

Dear Editors,

We submit our manuscript, **"Provenance-Certified KKR Convergence Assistance: `ml_assist`, PotentialBank v1, and
Same-Structure Warm Starts,"** for consideration as a **Computer Programs in Physics / software-method paper**.

Self-consistent-field convergence is a practical bottleneck in KKR and KKR-BdG Green-function DFT campaigns.
Restarting from a converged potential is a standard remedy, and **AiiDA-KKR already provides the underlying
restart primitives** (`parent_folder`, Voronoi `potential_overwrite`). We do **not** claim to have invented KKR
restart or potential reuse. Our contribution is the **layer above** those primitives:

- **PotentialBank v1**, a provenance-certified donor catalog in which a potential is admitted only under strict,
  auditable rules — byte-exact SHA-256 integrity, exact Z-sequence / NATYP compatibility, non-CPA / non-BdG scope
  control, and no guessed mapping;
- a **retrieval-based convergence advisor** exposing optional same-structure warm-start tips with explicitly
  benchmarked limits;
- an opt-in **`ml_assist`** early-abort wrapper whose mechanism is validated live, with an honest held-out
  benchmark showing it does not beat a simple RMS@10 baseline out-of-sample and requires per-cohort
  recalibration.

We are explicit about scope: **PotentialBank v1 is same-structure certified reuse, not cross-material potential
prediction**, and we claim no guaranteed acceleration. Nine hard cases are documented with root causes as honest
negative results.

The software is open source (MIT). **Raw potential data are not bundled**; they remain in the AiiDA provenance
store and are referenced by SHA-256 and provenance handles, so the manuscript and repository are reproducible
without shipping large binary blobs. The repository includes the installable package, unit tests that run
without HPC, a frozen model set with manifests, the PotentialBank v1 manifest/tables/figures, an advisor index,
and two walkthrough notebooks (one AiiDA-free; one submission tutorial that is safe-by-default and submits
nothing unless the reader explicitly opts in).

This work has not been published elsewhere and is not under consideration by another journal. The author
declares no competing interests. I suggest reviewers with expertise in KKR/Green-function DFT, AiiDA workflow
engineering, and machine learning for electronic structure.

Thank you for your consideration.

Sincerely,
Mohammad Hemmati\
Peter Grünberg Institut and Institute for Advanced Simulation, Forschungszentrum Jülich and JARA, D-52425
Jülich, Germany; RWTH Aachen University, D-52062 Aachen, Germany\
mohammad.hemmati@rwth-aachen.de · ORCID 0009-0006-4205-5706
