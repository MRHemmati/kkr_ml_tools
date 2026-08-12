"""P2: drive the wrapper's decision pipeline on RECORDED trajectories, no daemon. Mirrors what
inspect_kkr runs: parse_trajectory (from a mocked calc's convergence_group) -> seeded Mondrian policy
-> ml_decision -> telemetry extras. Confirms the hooks are finalized and behave. Runs under numpy only."""
import sys, pickle
import numpy as np
BASE = "/Users/hemmati/JupyterHub/jbox/Paper/My_ML_cc"
sys.path.insert(0, f"{BASE}/workspace/aiida-kkr-mlassist/src")
import aiida_kkr_mlassist as mla
from aiida_kkr_mlassist import (load_default_model, seeded_mondrian_policy, parse_trajectory,
                                ml_decision, telemetry_extras, MLAssistConfig)

model = mla.load_default_model()
dedup = pickle.load(open(f"{BASE}/workspace/analysis/study_data/dedup_records.pkl", "rb"))

# --- seeded, material-matched policy is certifiable from run 1 (NbSe2) ---
pol = seeded_mondrian_policy(model, alpha=0.05, material="Nb2Se4X2")
assert pol.certifiable(), "seeded NbSe2 Mondrian policy must be certifiable"
print("seeded policy thresholds:", {k: round(float(v), 3) for k, v in pol.thresholds.items()},
      "| n_calib:", pol.n_calib)

# --- parse_trajectory reproduces a mocked calc's convergence_group + mixing params ---
conv = next(r for r in dedup if r["regime"] == "normal" and r["converged"] and r["final_rms"] < 1e-7)
cg = {"rms_all_iterations": list(map(float, conv["rms"])),
      "charge_neutrality": list(map(float, conv["chneut"]))}
inparams = {"STRMIX": 0.03, "BRYMIX": 0.05, "TEMPR": 800.0}
rms, chneut, params = parse_trajectory(cg, inparams)
assert len(rms) == len(conv["rms"]) and params["strmix"] == 0.03 and len(chneut) == len(rms)
print(f"parse_trajectory: rms[{len(rms)}] chneut[{len(chneut)}] params={params}")

def pipeline(r, mode):
    """the exact decision path inspect_kkr runs, on a recorded run."""
    cg = {"rms_all_iterations": list(map(float, r["rms"])), "charge_neutrality": list(map(float, r["chneut"]))}
    rms, chn, prm = parse_trajectory(cg, {"STRMIX": r.get("strmix") or 0.03})
    act, tel = ml_decision(pol, rms, chn, prm, MLAssistConfig(mode=mode, alpha=0.05))
    return act, telemetry_extras(tel, act)

# --- converged run -> continue; doomed run -> abort (abort mode) ---
act_c, ex_c = pipeline(conv, "abort")
print(f"converged run -> {act_c}  P={ex_c['ml_assist']['p_converge']:.3f}"); assert act_c == "continue"
doom = min((r for r in dedup if r["regime"] == "normal" and not r["converged"] and len(r["rms"]) >= 12),
           key=lambda r: model.predict_proba([mla.extract_features(r["rms"], r["chneut"], {})])[0, 1])
act_d, ex_d = pipeline(doom, "abort")
print(f"doomed run    -> {act_d}  P={ex_d['ml_assist']['p_converge']:.3f} thr-region")
assert act_d == "abort" and ex_d["ml_assist"]["decision"] == "abort"
# advisory mode never aborts
act_a, ex_a = pipeline(doom, "advisory")
assert act_a == "continue" and "would_abort" in ex_a["ml_assist"]["action"]
print(f"doomed run (advisory) -> {act_a} (recorded {ex_a['ml_assist']['action']})")

# --- too-few-iters -> wait (safe no-op) ---
act_w, _ = ml_decision(pol, list(conv["rms"])[:5], None, {}, MLAssistConfig())
assert act_w == "wait"
print("\nP2 WRAPPER PIPELINE TEST PASS (parse -> seeded policy -> decision -> telemetry)")
