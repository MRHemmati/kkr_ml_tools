"""Package smoke test: pure core imports (no AiiDA), packaged model loads + selfchecks, entry-point
target is declared. Runs under the daemon python (numpy only)."""
import sys, numpy as np
sys.path.insert(0, "/Users/hemmati/JupyterHub/jbox/Paper/My_ML_cc/workspace/aiida-kkr-mlassist/src")
import aiida_kkr_mlassist as mla
print("package version:", mla.__version__)
m = mla.load_default_model()
d = m.selfcheck()
print(f"packaged model selfcheck (numpy==sklearn) = {d:.2e}")
assert d < 1e-12
# rank validator sanity via public API
ok, msg, common = mla.validate_chain_ranks(16, [24, 32])
assert not ok and common == [1, 2, 4, 8]
# conformal + decision reachable from the top-level API
assert hasattr(mla, "ConformalAbortPolicy") and hasattr(mla, "ml_decision")
print("default_model_path:", mla.default_model_path().split("/aiida_kkr_mlassist/")[-1])

# all three shipped models load + selfcheck (numpy only)
import glob, os
mdir=os.path.join(os.path.dirname(mla.default_model_path()))
for npz in sorted(glob.glob(mdir+"/mlassist_*.npz")):   # models only (skip calibration_seed_*)
    mm=mla.MLAssistModel.load(npz)
    d=mm.selfcheck(); assert d<1e-12
    print("model OK:", os.path.basename(npz), "feat", len(mm.feature_names), "selfcheck", f"{d:.1e}")

print("SMOKE PASS")
