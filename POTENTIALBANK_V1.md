# PotentialBank v1

A provenance-clean catalog of **certified single-structure converged KKR potentials** for **same-structure SCF
warm-start reuse** (the L3 acceleration lever of this project). Frozen 2026-08-11.

> **Scope in one line.** PotentialBank v1 accelerates *re-running the same structure* by starting SCF from a
> certified converged potential instead of a cold Voronoi start. It is **not** a cross-material transfer method
> and makes **no guaranteed-acceleration** claim. CPA/doped/disordered and BdG potentials are **out of scope**.

## Contents
- **238 certified donor nodes = 237 unique-SHA donors** (one recorded byte-duplicate: E1 Bi₂X₄ pk 24009≡24011).
- **8 families, 35 materials, 42 compatibility classes, 33 F2-eligible materials** (≥2 independent donors).

| family | donors | materials | F2-eligible | empty-sphere |
|---|---|---|---|---|
| NbSe₂/Bi (E1 historical) | 160 | 14 | 12 | no |
| simple metals (Nb/Al/Cu/Ag/Mo) | 24 | 5 | 5 | no |
| heavy-SOC (Au/W/Pt/Sb/Pb) | 24 | 5 | 5 | no |
| magnetic (Fe/Ni/Co) | 13 | 3 | 3 | no |
| ordered intermetallic (CuZn/Ni₃Al/FeAl) | 6 | 3 | 3 | no |
| covalent empty-sphere (Si/Ge) | 4 | 2 | 2 | **yes** |
| metallic layered chalcogenide (TiSe₂) | 2 | 1 | 1 | no |
| ionic rocksalt (MgO/NaCl) | 4 | 2 | 2 | no |

Manifest: `reports/potentialbank_v1/potentialbank_v1_manifest.csv` (sha256 `4186813d…`). Tables and figures
under `reports/potentialbank_v1/`.

## Certification rules (E1, verbatim)
A potential is admitted as a donor only if **all** hold:
1. parser succeeds and **byte-exactly round-trips**;
2. per-type **Z-sequence matches the structure site order** (empty spheres encoded as Z=0);
3. **NATYP == number of sites**;
4. **non-CPA and non-BdG**;
5. NSPIN / SOC / LMAX / radial mesh parse;
6. **no guessed mapping** (unsafe → rejected, never inferred);
7. **3-way SHA-256 match**: AiiDA-retrieved == staged == manifest.

CPA/disordered and BdG are excluded by construction. Each family also required a certified **settings recipe**
(RCLUSTZ screening cluster; Chebyshev `NCHEB` + `<USE_CHEBYCHEV_SOLVER>` with a cell-appropriate log panel
`R_LOG`/`NPAN_*`, voronoi kept Chebyshev-free; BZ mesh; explicit empty-sphere mapping for Si/Ge; and a
mixing-path variation — linear vs Broyden — to obtain **independent** F2 pairs for deterministic insulator SCF).

## Warm-start benchmark (same-structure)
Injecting a certified donor as `startpot_overwrite` cuts iterations-to-converge by large, reproducible margins,
**donor-choice-independent** (33/33 targets: identical iterations from either donor) and direction-symmetric
where cold-comparable:

| family | cold iters | warm iters | % saved |
|---|---|---|---|
| simple metals | 66–102 | 4–7 | 91–94% |
| heavy-SOC | 122–136 | 2–3 | ~97% |
| magnetic | 131–136 | 5–6 | ~96% |
| covalent Si/Ge | 117–119 | 2–3 | 97–98% |
| intermetallics | 128–152 | 5–7 | 95–97% |
| TiSe₂ (layered) | 1188–1354 | ≤100 | ~92% (coarse only) |
| ionic MgO/NaCl | 171–750 | 2–500 | 33–99% |

**Honest qualifications:** the saving magnitude is set by the *target's mixing accelerator* (a Broyden target
converges a warm start in a few iterations; a pure-linear target still crawls, e.g. 500 vs 750 for MgO/NaCl) —
so each row is a *matched same-mixing* comparison and we report per-family, never a single pooled headline.
TiSe₂ is coarse-converged only (fine contour destabilizes the zero-gap semimetal). Warm-start outputs are
benchmarks and are **not** themselves certified as donors. Full detail: `WARMSTART_BENCHMARK_V1_REPORT.md`.

## ml_assist scope (for context)
`ml_assist` (this repo's L1 lever) is an opt-in early-abort convergence controller with a per-cohort conformal
policy. Its **mechanism is validated end-to-end** (a live true early abort saved ~130 iterations), but the
learned model **does not beat a simple RMS@10 baseline** out-of-sample on the primary cohort and **does not
transfer across materials** — deploy per-cohort with recalibration. See the technical report and README.
PotentialBank v1 (L3) is a separate, complementary lever: certified same-structure reuse.

## Advisor index
`src/kkr_convergence_advisor/data/advisor_index_v1.json` (+ `advisor_example_tips_v1.json`) exposes the bank as
optional advisory tips (donor-start suggestions for F2-eligible materials with measured savings; unsafe
warnings for parked cases). Advisory-by-default; never suggests a guessed/uncertified/CPA/BdG donor; not
installed into the daemon. See `ADVISOR_INDEX_V1_UPDATE_REPORT.md`.

## Limitations and parked hard cases
Same-structure reuse only; no cross-material transfer; no guaranteed acceleration; CPA/BdG not covered. Nine
root-caused parked cases (`reports/potentialbank_v1/tables/deferred_parked.csv`): **MoS₂** (NACLSD, primitive
and conventional cells), **WSe₂** (SOC contour/EMIN instability + ~70 min/iter), **NbS₂** (NACLSD solved but
non-converging/expensive), **TaS₂** (SOC-NaN-prone), **TiAl** (VERTEX3D tetragonal shapefun), **Bi₂Te₃/Bi₂Se₃**
(hard-convergence), **CaF₂** (needs octahedral empty sphere), **LiF** (Z=3 light). Claim boundaries:
`PAPER_CLAIM_LADDER_AFTER_POTBANK_V1.md`.
