# Proposal 02 — Magnetic pair-breaking and gap suppression in TM-doped NbSe₂: ordered (FM) vs disordered-local-moment (DLM) reference, and the critical concentration xc

## Title
**Finite-temperature magnetic disorder and superconducting pair-breaking in transition-metal-doped
2H-NbSe₂: a KKR-BdG study of FM vs DLM and the critical dopant concentration.**

## Short abstract
Magnetic impurities suppress superconductivity via pair-breaking; the suppression rate depends not
only on the moment but on its *ordering state*. Using KKR-BdG Green-function calculations with CPA
disorder, we compare the ordered ferromagnetic (FM) reference against the paramagnetic
disordered-local-moment (DLM) reference for V/Mn/Fe/Co on the Nb site of 2H-NbSe₂, and locate the
critical concentration `xc` at which the BdG gap `delta/delta0` collapses. DLM, modeling the system
above its magnetic ordering temperature, is expected to break pairs more strongly and collapse the
gap at a lower `xc` — a finite-temperature, disorder-resolved view that complements single-impurity
YSR spectroscopy.

## Scientific motivation
- The Abrikosov–Gor'kov picture of magnetic pair-breaking depends on the spin-disorder configuration;
  DLM is the standard first-principles way to represent the paramagnetic/finite-T state.
- Whether FM vs DLM produces a materially different `xc` in a real multiband superconductor (NbSe₂)
  is a concrete, quantitative, first-principles question.
- This is a **distinct angle** from the existing NbSe₂-BdG/YSR manuscript (which studies pristine
  multiband anisotropy and single-impurity YSR states for Mn/Co): here the payload is the
  *concentration-resolved, order-resolved* `xc`, not the single-impurity spectrum.

## Existing calculations that support this proposal — [FACT]
- **CPA-BdG (DLM) SCF: group `NbSe2_X2Fe_DLM:SOC:BdGscf_onlyNb` — 62 standalone `KkrCalculation`
  runs, ALL converged (exit 0), `<USE_BDG>=True`, λ_BdG=0.024** (verified 2026-06-26). This is the
  disordered/paramagnetic side of the FM-vs-DLM comparison.
- **Ordered (FM/supercell) BdG SCF**: groups `NbSe2_2X2Fe:SOC:BdGscf_Nb` (37/41 converged),
  `NbSe2_2X2Fe:SOC:BdGscf_onlyNb` (23/23), `NbSe2_X2V:SOC:BdGscf_onlyNb` (28/30) — the ordered side,
  same λ_BdG=0.024. **So both sides of the comparison already have converged BdG data.**
- Group **`NbSe2_X2Fe_DLM_host`**: **69 `kkr_scf_wc`, all finished exit 0** (clean DLM normal-state host),
  plus sibling groups `*_DLM_host_{soc,scnsoc,Renormnsoc,chesol,...}` and the ordered
  `NbSe2_2X2Fe`, `NbSe2_2X2V`, `NbSe2_X2V:*` families.
- BdG impurity campaigns: `BdG_imps_Mn` (401 nodes), `kkrimp_BdG_wc` (1,451 in DB),
  `kkr_bdg_wc` (84; 11 converged exit-0, recent Apr–Jun 2026).
- Pristine BdG host PK 27923 (λ_BdG=0.024 Ry), gap reference `delta0 = 1.144407e-5 Ry` (help1).

## Relevant AiiDA nodes / groups / workflows — [FACT]
- Groups listed above; WorkChains `kkr_scf_wc`, `kkrimp_BdG_wc`, `kkr_bdg_wc`, `kkr_imp_dos_wc`.
- The order parameter is printed per run as `l-independent delta` (Ry); convergence lives in
  `output_parameters['convergence_group']`.

## Physics question it answers
*By how much, and at what critical concentration, does each transition-metal dopant suppress
superconductivity in NbSe₂ — and how much stronger is the pair-breaking in the disordered (DLM)
paramagnetic state than in the ordered (FM) state?*

## What is already done — [FACT/INTERP]
- A clean, converged DLM Fe-on-NbSe₂ host dataset (69 runs) and ordered FM counterparts exist.
- BdG host + impurity machinery is established (delta0 known; Mn/Co/Fe impurity moments measured:
  Mn≈3.70, Fe≈2.91, Co≈1.27 μ_B per help0).

## What is missing — [OPEN]
- **The gap-vs-concentration table** `delta/delta0(x; dopant; FM/DLM)` is not assembled in this
  folder (help1 references `paper6/*delta*.json`, which was not found on disk). It must be extracted
  per converged BdG run, **filtering `final_rms < ~1e-6`** (poisoned-label caveat, help1 §5).
- Sufficient **concentration coverage near `xc`** for both FM and DLM, for each dopant.
- A consistency check that `delta` is mixing-independent at convergence (true collapse vs numerical).

## Additional calculations that may be needed later (needs approval — submits jobs)
- A focused CPA-BdG concentration scan around the expected `xc` for FM and DLM (and for the dopants
  with thin coverage). This is the main compute investment and is **out of scope for the current
  read-only task**.

## Possible figures
1. `delta/delta0` vs dopant concentration `x`, FM vs DLM, one panel per dopant (the headline).
2. `xc` (FM) vs `xc` (DLM) bar chart across V/Mn/Fe/Co, vs impurity moment.
3. Impurity DOS / in-gap (YSR-adjacent) spectral weight vs `x` (links to the physics paper without
   duplicating it).
4. Convergence-quality map (final RMS) over the (x, dopant, order) grid — demonstrates label hygiene.

## Possible tables
- Per dopant: moment, `xc(FM)`, `xc(DLM)`, initial suppression slope d(delta)/dx.
- Provenance table: representative converged BdG UUIDs per (dopant, x, order).

## Possible paper outline
Intro (pair-breaking, FM vs DLM) → Methods (KKR-BdG + CPA + DLM; convergence criteria) →
Gap suppression curves → `xc` for FM vs DLM → Comparison to AG theory and to single-impurity YSR
→ Discussion (finite-T implications) → Reproducibility.

## Feasibility
**Medium-high (upgraded 2026-06-26).** Converged BdG SCF data now confirmed on *both* the DLM
(62/62) and ordered Fe/V sides at a fixed λ_BdG, so the FM-vs-DLM gap comparison may be largely
extractable from existing runs. Remaining effort: extract `delta` per run, confirm concentration
coverage brackets `xc`, and (only if gaps remain) add a few targeted CPA-BdG points.

## Risk level
**Medium.** Risks: (i) overlap with the existing NbSe₂-BdG/YSR manuscript — must stay on the
concentration/`xc`/DLM axis; (ii) label hygiene — non-converged `delta` values are meaningless;
(iii) `xc` may need more compute than expected.

## Publication potential
**High scientific value** (a clean FM-vs-DLM `xc` result in a real multiband superconductor is a
solid PRB/PRMaterials-level physics paper) **but contingent** on delta-curve completeness and clear
separation from the existing manuscript.

## Suggested next steps
1. Locate/recover the `delta` data (search the physics repos; if absent, write a read-only extractor
   over converged BdG runs).
2. Build the (x, dopant, order, final_rms, delta) table; keep only `final_rms < 1e-6`.
3. Plot preliminary `delta/delta0(x)` for FM vs DLM to see if `xc` is already bracketed by existing runs.
4. Only then decide on a targeted `xc` compute scan (your approval required).
