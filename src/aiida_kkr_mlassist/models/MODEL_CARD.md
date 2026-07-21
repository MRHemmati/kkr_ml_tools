# Model card — `mlassist_v1_normal_fixed10`

ml_assist v1 SCF-convergence classifier (normal regime). Predicts P(converge) from a fixed early
window of the SCF trajectory; drives the per-campaign conformal abort policy (L1).

## Provenance
- Estimator: RandomForestClassifier, 400 trees, `class_weight='balanced'`, seed 0 (sklearn 1.9.0).
- Training data: `study_data/dedup_records.pkl`, regime==normal, n_iters ≥ T_OBS+2 → n=1830, conv 90%.
- Features (15): `features.py` FEATURE_NAMES — log-RMS window stats + slope, charge-neutrality, mixing
  params + missing-flags. Fixed first-`T_OBS`=10 window (Δ3 aligned window dropped for v1).
- Artifact: `mlassist_v1_normal_fixed10.npz` (flattened forest) + sha256 in `.manifest.json`.
- Inference: pure numpy (`mlassist_infer.py`); golden-parity vs sklearn = 0.0, verified in the daemon env.
- Honest generalization: 5-fold OOF AUC = 0.944.

## STANDING RULE — the Replay-OOF Invariant (adopted 2026-07-13)
**Any replay, preview, or "deployment simulation" number is out-of-sample or prospective BY
CONSTRUCTION — never in-sample.** This is the third leakage-class artifact the project has caught
(1: segment inflation; 2: hard-failure censoring; 3: in-sample shadow-replay that faked recall=1.000).
Operationally: shadow-replays use OOF scores; prospective checks use runs absent from training
(verified by pk); the model that scores a run must never have trained on it. Goes in the paper's audit
section alongside the segment/censoring corrections.

## Intended use / limits
- **Per-system / per-campaign** deployment. Cross-MATERIAL transfer is NOT claimed (NbSe2→Bi ≈ chance);
  ranking transfers within a methodology but absolute rates need per-material calibration.
- Scope: COMPLETED runs (crashes/NaN-kills censored). Opt-in; advisory by default; abort only when the
  conformal policy is certifiable (needs ~19 calib points at α=0.05, ~9 at α=0.10 → material-matched seeding).
- float32 tree gotcha: inference MUST compare in float32 (sklearn does); guarded by embedded golden vectors.
