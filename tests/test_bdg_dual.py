"""Vehicle-A dual-scoring (Rider 1) + missing-Δ fallback (Rider 2) branching."""
import sys; sys.path.insert(0,"/Users/hemmati/JupyterHub/jbox/Paper/My_ML_cc/workspace/aiida-kkr-mlassist/src")
import numpy as np
from aiida_kkr_mlassist.decision import score_bdg_dual, MLAssistConfig

class StubPolicy:
    def __init__(self, p, thr=0.5): self.p=p; self.threshold=thr; self.n_calib=641
    def p_converge(self, X): return np.array([self.p]*len(X))
    def certifiable(self): return np.isfinite(self.threshold)

rms = list(np.logspace(0,-3,15)); chn = list(np.full(15,1e-4)); params={"strmix":0.03}
delta = np.logspace(-5,-5.2,15)                      # a Δ trajectory (>=T)

# (1) Δ available -> uses rms+Δ policy, logs BOTH scores
act, tel = score_bdg_dual(StubPolicy(0.9), StubPolicy(0.2), rms, chn, params, delta,
                          MLAssistConfig(mode="abort"))
print("Δ available:", act, "| p_rms_only=%.2f p_rms+Δ=%.2f used=%.2f avail=%s"%(
    tel["p_rms_only"], tel["p_rms_plus_delta"], tel["p_converge"], tel["delta_available"]))
assert tel["delta_available"] and tel["p_rms_plus_delta"]==0.9 and tel["p_rms_only"]==0.2
assert tel["p_converge"]==0.9 and act=="continue"      # 0.9>=0.5 threshold -> continue

# (2) Δ missing -> fallback to rms-only policy; abort fires on the rms score
act, tel = score_bdg_dual(StubPolicy(0.9), StubPolicy(0.1), rms, chn, params, None,
                          MLAssistConfig(mode="abort"))
print("Δ missing :", act, "| p_rms_only=%.2f p_rms+Δ=%s used=%.2f avail=%s"%(
    tel["p_rms_only"], tel["p_rms_plus_delta"], tel["p_converge"], tel["delta_available"]))
assert not tel["delta_available"] and tel["p_rms_plus_delta"] is None
assert tel["p_converge"]==0.1 and act=="abort"          # 0.1<0.5 -> abort via fallback policy

# (3) too few iters -> wait
act, _ = score_bdg_dual(StubPolicy(0.9), StubPolicy(0.9), rms[:5], chn[:5], params, delta)
assert act=="wait"
print("BdG dual-scoring + fallback test PASS")
