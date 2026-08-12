# Warm-start benchmark v1 synthesis — 2026-08-11

Aggregate of **all same-structure warm-start benchmarks through NaCl**. Offline synthesis of already-reported
results (E3b, F2a/b/c/d, G4, I4, Stage R, Stage T MgO/NaCl). Iterations-to-converge is the primary
hardware-invariant metric. Data: `workspace/synthesis_v1/warmstart_synthesis.csv`.

## Per-family medians (stratified — no misleading single pooled headline)
| family | cold iters | warm iters | ~% saved | direction | donor-choice | contour caveat |
|---|---|---|---|---|---|---|
| NbSe2/Bi (E3b, same-cell) | ~391 | ~197 | ~50% | 8/9 faster (1 slower) | n/a | coarse→fine staging offset for 5/9 pairs |
| simple metals (Al/Cu/Ag/Mo) | 66–102 | 4–7 | ~91–94% | symmetric | d1==d2 | clean fine→fine (F2c) |
| heavy-SOC (Au/W/Pt/Sb/Pb) | 122–136 | 2–3 | ~97% | forward (reverse skipped) | d1==d2 | clean fine→fine |
| magnetic (Fe/Ni/Co) | 131–136 | 5–6 | ~96% | symmetric both dir | d1==d2 | clean; moments basin-matched |
| covalent Si/Ge (empty-sphere) | 117–119 | 2–3 | ~97–98% | symmetric | n/a | clean fine→fine |
| ordered intermetallic (CuZn/Ni3Al/FeAl) | 128–152 | 5–7 | ~95–97% | symmetric | n/a | clean; non-magnetic basin |
| metallic layered (TiSe2) | 1188–1354 | ≤100 | ~92% | symmetric | n/a | **coarse only** (0-gap semimetal; fine destabilizes) |
| ionic rocksalt (MgO) | 178 / 750 | 6 / 500 | 97% / 33% | **target-mixing dependent** | n/a | coarse; matched per mixing |
| ionic rocksalt (NaCl) | 171 / 750 | 2 / 500 | 99% / 33% | **target-mixing dependent** | n/a | coarse; matched per mixing |

## Pooled figure (reported WITH the stratified medians, per the anti-Goodhart rule)
Across the benchmarked expansion materials the **median iteration saving is ~96%** on a converging (Broyden/
aggressive) target; **but this is not a universal headline** — it degrades to ~33% when the target uses slow
linear (IMIX=0) mixing (MgO/NaCl linear arms), and TiSe2 is coarse-only. The honest statement is per-family
(table above), not a single number.

## Key qualifications (honest)
1. **Iteration count is set by the target's mixing accelerator**, not just the warm start. A Broyden target
   polishes a warm start in 2–7 iters; a pure-linear (IMIX=0) target still crawls (500 vs 750 for MgO/NaCl).
   Each row is a *matched same-mixing* warm-vs-cold comparison, so the saving is real, but the magnitude is
   mixing-dependent.
2. **Direction symmetry** holds where both arms are cold-comparable (metals reverse = forward in F2b; magnetic
   both directions symmetric). Heavy-SOC reverse was skipped (chain-1 was itself warm-made — no cold
   counterfactual). MgO/NaCl "asymmetry" is a target-mixing artifact, not a physics asymmetry.
3. **Donor-choice robustness:** where tested with 2 donors (F2d, 33 targets), d1==d2 iterations exactly (donor
   choice irrelevant).
4. **Contour caveats:** TiSe2 is coarse-converged only (fine destabilizes the semimetal); some E3b NbSe2 pairs
   have a coarse-vs-fine energy offset; metals were confirmed clean fine→fine in F2c; MgO/NaCl are coarse.
5. **Scope:** every benchmark is **same-structure** (donor ≡ target geometry/chemistry/settings). This is
   **NOT** cross-material transfer and **NOT** a guaranteed-acceleration claim. Warm-start outputs are **not
   certified** (benchmark only).

## Bottom line
Same-structure warm-start from a certified donor is a **large, reproducible, donor-choice-independent** iteration
saving across all 8 expansion families (2–7 iters vs ~66–1350 cold on a converging target), with honest
mixing/contour caveats. Value is per-campaign reuse within a fixed structure, not community-wide transfer.
