# CPC Program Summary

*(Draft for a Computer Programs in Physics / software-method submission to Computer Physics Communications.
CPC requires a Program Summary immediately after the abstract — a LaTeX version is embedded in
`reports/technical_report/main.tex`.)*

**Program title:** `aiida-kkr-mlassist` / KKR Convergence Advisor / PotentialBank v1

**CPC Library link to program files:** *TODO (assigned by CPC on acceptance).*

**Developer's repository link:** https://github.com/MRHemmati/kkr_ml_tools

**Code Ocean capsule:** *TODO (optional; not created — no compute/upload performed).*

**Licensing provisions:** MIT. A top-level `LICENSE` file (MIT, "Copyright (c) 2026 Mohammad Hemmati") is present
in the repository and consistent with `pyproject.toml`, satisfying CPC's approved-open-source-license requirement.

**Programming language:** Python (pure-`numpy` runtime core; AiiDA/`aiida-kkr` used only inside the daemon for
submission; LaTeX for the report).

**Supplementary material:** frozen model artifacts (`.npz` + JSON manifests + model card), the PotentialBank v1
manifest/tables/figures, the advisor index, unit tests, and two walkthrough notebooks.

**Nature of problem:** Self-consistent-field (SCF) convergence is the practical bottleneck of KKR / KKR-BdG
Green-function DFT campaigns: many runs stall, diverge, or converge slowly, wasting HPC time. Restarting from a
previously converged potential is a standard remedy and AiiDA-KKR already provides the primitives
(`parent_folder`, `potential_overwrite`), but choosing a *valid* donor is error-prone — an incompatible or
mis-mapped potential silently corrupts a run. There is no provenance-safe, auditable way to discover and reuse
compatible donor potentials, nor a calibrated way to decide early that a run should be aborted.

**Solution method:** An AiiDA-native, opt-in `ml_assist` workchain wrapper scores the first ten SCF iterations
(pure-`numpy` frozen model + a simple RMS@10 baseline) under a per-cohort conformal early-abort policy with
Mondrian per-stratum thresholds. **PotentialBank v1** builds a certified donor catalog by mining the AiiDA
provenance graph and admitting a potential only under strict *E1 certification*: byte-exact integrity (three-way
SHA-256 match), exact per-type $Z$-sequence and NATYP compatibility with the structure, non-CPA / non-BdG scope
control, and no guessed mapping. A retrieval-based advisor exposes optional same-structure warm-start tips; the
warm start injects a certified donor through the existing Voronoi `potential_overwrite` primitive.

**Restrictions:** PotentialBank v1 covers **normal-state, non-CPA** potentials only; **CPA, disordered, BdG, and
cross-material prediction are not supported**. Warm-start reuse is **same-structure only** (donor $\equiv$ target
geometry, chemistry, and settings); there is **no guaranteed acceleration** — savings depend on structure,
mixing, and energy contour. Raw potential bytes remain in the AiiDA repository and are **not** bundled in git;
the bank references them by SHA-256 and provenance. Live submission requires the author's AiiDA database and
cluster access.

**Unusual features:** strict provenance certification with byte-exact hashing and exact structural compatibility;
a "no guessed mapping" rejection rule; same-structure warm-start benchmarks reported per family with mixing /
contour caveats; a documented catalog of nine root-caused hard cases (honest negative results); and a
mechanism-validated but explicitly-not-transferable ML early-abort layer (does not beat an RMS@10 baseline
out-of-sample; requires per-cohort recalibration).

**Additional comments:** PotentialBank v1 is frozen at **237 unique certified donors (238 nodes; one recorded
byte-duplicate)** across **8 material families** (NbSe$_2$/Bi, simple metals, heavy-SOC, magnetic, ordered
intermetallics, covalent empty-sphere Si/Ge, metallic layered TiSe$_2$, ionic rocksalt MgO/NaCl) with **33
F2-eligible materials** (≥2 independent certified donors). Three frozen `ml_assist` scorers ship with SHA-256
manifests; the held-out replay uses 336 leakage-clean runs.

**References:** the aiida-kkr plugin [Rüßmann, Bertoldo & Blügel, *npj Comput. Mater.* **7**, 13 (2021)] and the
related-work bibliography of the accompanying technical report (`reports/technical_report/main.tex`).
