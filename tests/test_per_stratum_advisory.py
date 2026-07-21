"""Stage A.6: per-stratum advisory gating. A CERTIFIABLE stratum aborts a low-P run; a thin (non-
certifiable) stratum is ADVISORY-ONLY (never aborts) even at low P. No full-seed fallback."""
import sys, numpy as np
sys.path.insert(0,"/Users/hemmati/JupyterHub/jbox/Paper/My_ML_cc/workspace/aiida-kkr-mlassist/src")
from aiida_kkr_mlassist.conformal import MondrianConformalAbortPolicy
from aiida_kkr_mlassist.decision import ml_decision, MLAssistConfig, extract_features
from aiida_kkr_mlassist import flat_starter_stratum

class Stub:  # always predicts P(converge)=0.1 (doomed) regardless of features
    def predict_proba(self, X): return np.tile([0.9, 0.1], (len(np.atleast_2d(X)), 1))

pol = MondrianConformalAbortPolicy(Stub(), alpha=0.10)
# calibration: "other" stratum certifiable (30 converged), "flat" stratum thin (3 converged -> -inf thr)
scores = np.r_[np.linspace(0.5, 0.99, 30), np.linspace(0.5, 0.99, 3)]
y      = np.r_[np.ones(30, int),           np.ones(3, int)]
strata = np.r_[np.array(["other"]*30),     np.array(["flat"]*3)]
pol.calibrate_from_scores(scores, y, strata)
print("thresholds:", {k: (round(float(v),3) if np.isfinite(v) else "-inf") for k,v in pol.thresholds.items()})
assert np.isfinite(pol.thresholds["other"]) and not np.isfinite(pol.thresholds["flat"])

# rms trajectories that map to each stratum (flat_starter_stratum uses logrms_min idx4 + slope idx6)
flat_rms  = [0.1]*12                                  # all >=8e-3, flat -> "flat" stratum
other_rms = list(np.logspace(-0.3, -3, 12))           # 0.5 -> 1e-3 steep -> "other" stratum
assert flat_starter_stratum(extract_features(flat_rms,None,{})) == "flat"
assert flat_starter_stratum(extract_features(other_rms,None,{})) == "other"

# CERTIFIABLE stratum ("other"), abort mode, P=0.1 < threshold -> ABORT
act_o, tel_o = ml_decision(pol, other_rms, None, {}, MLAssistConfig(mode="abort", alpha=0.10))
print(f"other stratum (certifiable): action={act_o} P={tel_o['p_converge']} thr={tel_o['conformal_threshold']:.3f} cert={tel_o['certifiable']}")
assert act_o == "abort"

# THIN stratum ("flat"), abort mode, P=0.1 but non-certifiable -> ADVISORY, never abort
act_f, tel_f = ml_decision(pol, flat_rms, None, {}, MLAssistConfig(mode="abort", alpha=0.10))
print(f"flat stratum (thin):        action={act_f} P={tel_f['p_converge']} advisory_only={tel_f['stratum_advisory_only']} cert={tel_f['certifiable']}")
assert act_f == "continue" and tel_f["stratum_advisory_only"] is True and tel_f["action"] == "continue_advisory_stratum"
print("\nPER-STRATUM ADVISORY TEST PASS")
