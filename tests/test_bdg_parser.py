"""BdG Δ-parser correctness on a synthetic out_kkr fragment (no AiiDA needed)."""
import sys; sys.path.insert(0, "/Users/hemmati/JupyterHub/jbox/Paper/My_ML_cc/workspace/aiida-kkr-mlassist/src")
import numpy as np
from aiida_kkr_mlassist.bdg_parser import parse_delta_trajectory, delta_features, DELTA_FEATURE_NAMES
txt = """
+++ SCF ITERATIONS START +++
 l-independent delta:  1.455477156763534E-005
 l-independent delta:  1.455232711868613E-005
 ITERATION   1 average rms-error : v+ + v- =  1.0828D-05
 l-independent delta:  1.424751575058399E-005
 l-independent delta:  1.424559099521017E-005
 ITERATION   2 average rms-error : v+ + v- =  9.8113D-06
 l-independent delta:  2.000000000000000E-005
 l-independent delta:  2.000000000000000E-005
 ITERATION   3 average rms-error : v+ + v- =  8.9634D-06
"""
traj, per = parse_delta_trajectory(txt)
assert len(traj) == 3 and all(len(p) == 2 for p in per), (len(traj), per)
assert abs(traj[0] - 1.45535e-5) < 1e-9 and abs(traj[2] - 2.0e-5) < 1e-12
# D-exponent parsing + reduce modes
assert abs(parse_delta_trajectory(txt, reduce="first")[0][0] - 1.455477156763534e-5) < 1e-12
f = delta_features(traj, 3)
assert f is not None and len(f) == len(DELTA_FEATURE_NAMES)
assert delta_features(traj, 10) is None            # too few iters -> None
print("BdG Δ-parser test PASS:", dict(zip(DELTA_FEATURE_NAMES, [round(v,3) for v in f])))
