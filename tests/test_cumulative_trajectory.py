"""Stage-B fix regression: the ml_assist hook must read the CUMULATIVE trajectory across ordered SCF
segments, not only the last KkrCalculation. Proves the bug (last-segment-only stays 'wait') and the fix
(cumulative reads reach the T_obs+2 threshold and SCORE). Pure numpy; no daemon."""
import sys
import numpy as np
sys.path.insert(0, "/Users/hemmati/JupyterHub/jbox/Paper/My_ML_cc/workspace/aiida-kkr-mlassist/src")
from aiida_kkr_mlassist import (load_default_model, seeded_mondrian_policy, parse_trajectory,
                                build_cumulative_trajectory, ml_decision, MLAssistConfig)
from aiida_kkr_mlassist.features import T_OBS

model = load_default_model()
pol = seeded_mondrian_policy(model, alpha=0.10, material="Nb2Se4X2")

# simulate 5 SCF segments of nsteps=10, each reporting ONLY its own 10 iters (as KKR restart does),
# a cleanly-decreasing (converging) run 0.22 -> ~1e-3.
full = np.geomspace(0.22, 1e-3, 50)
segments = [{"convergence_group": {"rms_all_iterations": list(full[i*10:(i+1)*10]),
                                   "charge_neutrality": list(np.full(10, 1e-4))},
             "input_params": {"STRMIX": 0.03, "BRYMIX": 0.05, "TEMPR": 800.0}} for i in range(5)]

# ---- the OLD bug: last-segment-only ----
last_rms, last_chn, last_params = parse_trajectory(segments[-1]["convergence_group"],
                                                   segments[-1]["input_params"])
assert len(last_rms) == 10                                   # one segment = 10 iters
act_bug, tel_bug = ml_decision(pol, last_rms, last_chn, last_params, MLAssistConfig(mode="abort", alpha=0.10))
print(f"OLD (last segment, 10 iters): decision={act_bug} reason={tel_bug.get('reason')}")
assert act_bug == "wait", "old behaviour must be wait (10 < T_obs+2)"   # reproduces the Stage-B finding

# ---- the FIX: cumulative across segments ----
# after 1 segment -> 10 iters -> still wait
cum1_rms, cum1_chn, cum1_p = build_cumulative_trajectory(segments[:1])
assert len(cum1_rms) == 10
a1, _ = ml_decision(pol, cum1_rms, cum1_chn, cum1_p, MLAssistConfig(mode="abort", alpha=0.10))
print(f"FIX after 1 segment (10 iters): decision={a1}"); assert a1 == "wait"

# after 2 segments -> 20 cumulative iters -> SCORES (>= T_obs+2 = 12)
cum2_rms, cum2_chn, cum2_p = build_cumulative_trajectory(segments[:2])
assert len(cum2_rms) == 20 and cum2_chn is not None and len(cum2_chn) == 20
assert cum2_p["strmix"] == 0.03 and cum2_p["brymix"] == 0.05     # mixing from first (cold-start) segment
a2, tel2 = ml_decision(pol, cum2_rms, cum2_chn, cum2_p, MLAssistConfig(mode="abort", alpha=0.10))
print(f"FIX after 2 segments (20 iters): decision={a2} p_converge={tel2.get('p_converge'):.3f} "
      f"thr={tel2.get('conformal_threshold'):.3f}")
assert a2 != "wait" and tel2.get("p_converge") is not None      # NOW it scores
assert a2 == "continue"                                          # decreasing run -> converge, no abort

# full 5 segments -> 50 iters, still scores on the FIRST-10 window (feature window is rms[:T_obs])
cum5_rms, cum5_chn, cum5_p = build_cumulative_trajectory(segments)
assert len(cum5_rms) == 50
a5, tel5 = ml_decision(pol, cum5_rms, cum5_chn, cum5_p, MLAssistConfig(mode="abort", alpha=0.10))
assert a5 != "wait" and tel5.get("p_converge") is not None
print(f"FIX after 5 segments (50 iters): decision={a5} p_converge={tel5.get('p_converge'):.3f}")

# defensive: a segment that restates the whole run so far (cumulative report) is de-duplicated
cumulative_segments = [
    {"convergence_group": {"rms_all_iterations": list(full[:10])}, "input_params": {"STRMIX": 0.03}},
    {"convergence_group": {"rms_all_iterations": list(full[:20])}, "input_params": {"STRMIX": 0.03}},  # prefix-overlap
]
dd_rms, _, _ = build_cumulative_trajectory(cumulative_segments)
assert len(dd_rms) == 20, f"prefix-overlap must dedup to 20, got {len(dd_rms)}"
print(f"defensive dedup (prefix-overlap): {len(dd_rms)} iters (no duplicates)")

print(f"\nT_obs={T_OBS}; first score needs T_obs+2={T_OBS+2} obs -> with nsteps=10, first score at cum iter 20.")
print("CUMULATIVE TRAJECTORY FIX TEST PASS")
