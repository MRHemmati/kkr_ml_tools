"""ml_assist v1 — CANONICAL feature extraction (single source of truth).
Must byte-for-byte match what the frozen model (mlassist_v1_normal_fixed10) was trained on. Used by
BOTH training (from dedup records) and live inference (from a running calc's trajectory), so the two
can never drift. If this changes, retrain + re-export + bump the model id.

Fixed early-window features (Δ3 aligned-window dropped for v1):
  log-RMS window stats + slope, charge-neutrality window stats, mixing params with missing-flags.
"""
import numpy as np

T_OBS = 10
FEATURE_NAMES = ["logrms_0", "logrms_last", "logrms_mean", "logrms_std", "logrms_min", "logrms_drop",
                 "logrms_slope", "logchneut_last", "logchneut_mean",
                 "tempr", "tempr_missing", "brymix", "brymix_missing", "strmix", "strmix_missing"]
_MIX_DEFAULTS = [("tempr", 600.0), ("brymix", 0.05), ("strmix", 0.05)]


def enough_iters(rms, T=T_OBS):
    """the model needs at least T+2 RMS iterations to form the early window (matches training filter)."""
    return len(np.asarray(rms)) >= T + 2


def extract_features(rms, chneut=None, params=None, T=T_OBS):
    """Build the 15-D feature vector from a run's trajectory + inputs.
      rms     : sequence of per-iteration RMS errors (>= T+2 long)
      chneut  : per-iteration charge-neutrality (optional; zero-filled if absent)
      params  : dict with optional 'tempr','brymix','strmix' (missing -> default + missing-flag=1)
    Returns a python list of 15 floats in FEATURE_NAMES order, or None if too few iterations.
    """
    rms = np.asarray(rms, float)
    if len(rms) < T + 2:
        return None
    w = np.log10(np.clip(rms[:T], 1e-15, None))
    slope = float(np.polyfit(np.arange(len(w)), w, 1)[0])
    f = [w[0], w[-1], float(w.mean()), float(w.std()), float(w.min()), w[0] - w[-1], slope]
    if chneut is not None and len(np.asarray(chneut)) >= T:
        cw = np.abs(np.asarray(chneut[:T], float))
        f += [float(np.log10(np.clip(cw[-1], 1e-15, None))), float(np.log10(np.clip(cw.mean(), 1e-15, None)))]
    else:
        f += [0.0, 0.0]
    params = params or {}
    for k, d in _MIX_DEFAULTS:
        v = params.get(k)
        f.append(float(v) if v is not None else d)
        f.append(0.0 if v is not None else 1.0)
    return f


def features_from_record(r, T=T_OBS):
    """Convenience: build features from a dedup_records.pkl row (training path)."""
    return extract_features(r.get("rms"), r.get("chneut"),
                            {k: r.get(k) for k, _ in _MIX_DEFAULTS}, T)
