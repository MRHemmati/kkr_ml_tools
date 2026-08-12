# Paper claim ladder after PotentialBank v1 — 2026-08-11

The claims the evidence supports, tiered. Written to keep the paper honest: same-structure reuse is strong; ML
transfer and cross-material claims are not made. Derived from the audited record (D1b audit + Stages E–T).

## 1. VALIDATED (measured, reproducible, provenance-backed)
- **PotentialBank v1 = 237 unique certified donors** (238 nodes, 1 E1 byte-dup) across **8 families / 35
  materials**, each with a byte-exact E1 fingerprint (Z-sequence, NATYP, non-CPA/BdG, 3-way sha, no guessed
  mapping). 33 materials are F2-eligible (≥2 unique donors).
- **Same-structure warm-start gives large, reproducible iteration savings** on a converging target: 2–7 iters
  vs ~66–1350 cold across all 8 expansion families; **donor-choice-independent** (F2d 33/33 d1==d2);
  **direction-symmetric** where cold-comparable.
- **The certification/settings machinery is validated end-to-end**: per-material footgun recipes (RCLUSTZ,
  R_LOG/NPAN, BZDIVIDE, NCHEB+Chebyshev routing, empty-sphere mapping, mixing-path for F2 pairs) each
  demonstrated on real converged donors.
- **ml_assist mechanism validated live** (Stage-C2b): a frozen numpy classifier fired a true early abort on a
  genuinely-doomed run (exit 701), with Mondrian conformal abstain and telemetry — the *mechanism* works.
- **Hard cases are root-caused** (MoS2 NACLSD, WSe2 contour/EMIN+speed, NbS2/TaS2, TiAl VERTEX3D, Bi2Te3/Bi2Se3
  hard-convergence): honest negatives, each with a diagnosis.

## 2. SUPPORTED BUT SCOPED (true within a stated boundary)
- Warm-start value is **per-campaign reuse within a fixed structure** (donor ≡ target geometry/chemistry/
  settings) — a real workflow accelerator inside a screening campaign.
- ml_assist early-convergence prediction works **per-system** (in-distribution NbSe2 AUC ~0.94; prospective
  0.967 on a single-material grid) — deploy **per-campaign**, not community-wide.
- Iteration savings magnitude is **mixing-dependent** (Broyden target ~96–99%; pure-linear target ~33%) and
  **contour-qualified** (TiSe2 coarse-only). Report per-family, not one pooled number.
- Conformal false-abort control holds **after per-cohort calibration** under exchangeability (a seeded threshold
  does not transport in general).

## 3. SUGGESTIVE (motivating, not proven)
- Warm-start could seed an ML-in-the-loop restart protocol (the closed loop was prototype-validated, not
  production-run).
- Δ-channel (BdG pairing) features add a small within-BdG AUC lift (+0.011, borderline) — payoff expected mainly
  for near-critical CPA-BdG campaigns (untested at scale).
- The advisor could become a per-campaign flywheel (index update per run) — designed, not deployed.

## 4. DISALLOWED (evidence does NOT support)
- **No cross-material transfer** — warm-start and the abort classifier do **not** transfer across materials
  (D1b: NbSe2→Bi AUC ≈ chance; warm-start is same-structure by construction). Leave-formula-out savings = 0.
- **No guaranteed acceleration** — savings depend on structure/mixing/contour; some cases park entirely.
- **No broad layered / ionic / intermetallic "coverage"** — TiSe2 is the only certified layered chalcogenide;
  MgO+NaCl the only ionic; CuZn/Ni3Al/FeAl the only intermetallics. Do not generalize beyond tested materials.
- **No CPA/doped/disordered or BdG donor claims** — excluded by construction from the certified bank.
- **No "ML beats all baselines"** and **no 0.944 as a headline** — RMS@10 is a strong baseline; per-cohort
  calibration is required; lead with the honest held-out per-cohort numbers.
- **MoS2/WSe2 "recovered"** — both parked (0 donors); only diagnoses/designs exist.

## Thesis (one line)
*An AiiDA-native, provenance-clean PotentialBank of certified single-structure KKR donors that delivers large,
reproducible same-structure SCF warm-start savings across 8 material families — with an honest boundary: no
cross-material transfer, no guaranteed acceleration, and documented hard cases — plus a validated (but
per-campaign, not universal) ml_assist convergence-control mechanism.*
