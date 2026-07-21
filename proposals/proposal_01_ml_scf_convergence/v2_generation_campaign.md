# v2 warm-start — data-generation campaign design

*2026-07-03. Goal: build the (structure × mixing) dataset v2 needs — many structures, each run over a
mixing grid with a spread of outcomes — so a model can learn `f(structure, mixing) → {converged?,
iterations}` and recommend good mixing for a NEW structure. The existing DB is ~1 mixing/structure
(86% of structures), so this must be generated.*

## 1. Structure set (12, from the 14 fresh iffslurm-submittable candidates)
Chosen for diversity in chemistry, size, and doping; each has a clean fresh (structure+voronoi)
template on iffslurm. **Every one is pre-flighted before launch** (codes / no dead remote / computer).

| # | structure | n_atoms | family | code | template pk | note |
|---|---|---:|---|---|---|---|
| 1 | Nb2Se4X2 | 8 | NbSe2 | AMD | 104832 | validated anchor |
| 2 | Nb2Se4X10 | 16 | NbSe2 | AMD | 275 | size diversity |
| 3 | Nb2Se4{Fe0.10X0.90}2 | 8 | NbSe2:Fe (CPA) | BdG-AMD | 15862 | dopant |
| 4 | Nb2Se4{Fe0.92X0.08}2 | 8 | NbSe2:Fe (CPA) | BdG-AMD | 15131 | concentration extreme |
| 5 | Nb (bulk) | 1 | metal | BdG-AMD | 100273 | simple-metal anchor |
| 6 | Bi4X4 | 8 | Bi | AMD | 26409 | Bi chemistry |
| 7 | Bi2X4 | 6 | Bi | AMD | 25033 | |
| 8 | Bi2X6 | 8 | Bi | AMD | 17338 | |
| 9 | Bi3X6 | 9 | Bi | AMD | 15375 | |
| 10 | Bi2 | 2 | Bi | AMD | 15474 | small |
| 11 | Bi2Te3 | 5 | topological insulator | **intel** | 15621 | distant chemistry* |
| 12 | Pb3Te4{Pb0.98Tl0.02} | 8 | PbTe:Tl (CPA) | **intel** | 12629 | genuinely distant* |

\* #11–12 use the **intel** binary, so they run on an intel partition, not th1-2020-64/AMD. They are
the most valuable for chemistry breadth. Options: (a) run them on the intel partition in parallel, or
(b) re-point to an AMD code if the potentials permit, or (c) drop for a clean AMD-only first pass and
add in a follow-up. Recommend keeping them (breadth is the whole point) but handling separately.

## 2. Mixing grid (per structure)
~8 settings spanning stall → converge → diverge (from the 24-run grid, the informative window):
`strmix ∈ {0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12}` at `brymix = 0.05`, plus one `brymix = 0.08`
point (strmix 0.03) to probe Broyden sensitivity → **8 runs/structure**. This locates each structure's
sweet spot AND its divergence boundary — the label v2 learns.

## 3. Scale and compute (12 nodes, th1-2020-64)
- **12 structures × 8 mixings = 96 runs** (10 AMD-clean; 2 intel handled separately).
- **CRITICAL walltime lesson:** set a **SHORT walltime (~3 h/segment, 10800 s)** and **`kkr_runmax=2–3`**.
  Converging 8-atom runs finish in <1.5 h; a NaN-hang then dies at 3 h instead of squatting a node for
  24 h (the zombie problem from the grid). This slashes the cost of the diverging half of the grid.
- Per-run avg ~2–4 h (fast converges + short-walltime failures; larger cells 2× ). At 12 concurrent
  with rolling backfill: **~1–1.5 days** wall-clock for the 96 AMD runs (add ~a day if intel runs
  serialize on a smaller partition).

## 4. Data schema (the v2 training table)
Per run, record:
- **structure features:** SOAP descriptor (existing pipeline), composition, dopant + concentration,
  n_atoms, cell.
- **mixing:** strmix, brymix, imix, nsimplemixfirst.
- **outcome (labels):** converged (final_rms < QBOUND), n_iterations_total, final_rms, rms trajectory.
- **provenance:** AiiDA UUIDs.
Target for v2: `f(SOAP + composition + mixing) → {P(converge), iterations}`; deploy by scanning
candidate mixings for a new structure and returning the argmin-iterations with high P(converge).

## 5. Execution plan (lessons applied)
1. **Pre-flight** each of the 12 templates (codes, remote, computer) — reject/replace any that fail.
2. Reuse the proven machinery: clone template → set queue th1-2020-64, **short walltime**, mixing;
   idempotent **rolling backfill** (≤12 concurrent); monitor + auto-extract.
3. Handle the 2 intel structures on their partition (or defer).
4. On completion: extract (SOAP + mixing → outcome) table, then train the v2 surrogate.

## 6. Efficiency upgrade (optional, after first pass)
**Active learning:** run a coarse grid first (say 4 structures × 8), train a preliminary v2, then let
it choose the most informative (structure, mixing) points to run next — reaches the same accuracy with
far fewer runs than the full fixed grid. Recommended once the fixed-grid pilot validates the pipeline.

## 7. Bottom line
~96 runs, ~1–1.5 days at 12 nodes with short walltimes, yields the first genuine (structure × mixing)
dataset — enough to train a v2 warm-start prototype and, as a bonus, to sharpen the cross-material
transfer claim (Bi2Te3/PbTe are far from NbSe2).
