"""Mondrian per-stratum conformal controls flat-starter false-abort where marginal fails (Issue 1)."""
import sys, pickle; sys.path.insert(0,"/Users/hemmati/JupyterHub/jbox/Paper/My_ML_cc/workspace/aiida-kkr-mlassist/src")
sys.path.insert(0,"/Users/hemmati/JupyterHub/jbox/Paper/My_ML_cc/workspace")
import numpy as np
from aiida_kkr_mlassist import (MLAssistModel, MondrianConformalAbortPolicy, ConformalAbortPolicy,
                                flat_starter_stratum, default_model_path)
from mlassist.features import features_from_record, T_OBS
B="/Users/hemmati/JupyterHub/jbox/Paper/My_ML_cc"
m=MLAssistModel.load(default_model_path())
dedup=pickle.load(open(f"{B}/workspace/analysis/study_data/dedup_records.pkl","rb"))
SWITCH=8e-3
def is_flat_traj(r):
    rms=np.asarray(r["rms"],float)
    if len(rms)<T_OBS: return False
    w=np.log10(np.clip(rms[:T_OBS],1e-15,None)); s=float(np.polyfit(np.arange(len(w)),w,1)[0])
    return (rms[:T_OBS]>=SWITCH).all() and abs(s)<0.05
X,y,ft=[],[],[]
for r in dedup:
    if r["regime"]!="normal": continue
    f=features_from_record(r)
    if f is None: continue
    X.append(f); y.append(int(r["converged"])); ft.append(is_flat_traj(r))
X,y,ft=np.array(X),np.array(y),np.array(ft)
# feature-derived stratum must agree with trajectory-level flat definition
agree=np.mean([ (flat_starter_stratum(x)=="flat")==fi for x,fi in zip(X,ft)])
print(f"stratum agreement (feature-derived vs trajectory): {100*agree:.1f}%"); assert agree>0.98
rng=np.random.default_rng(0); marg,mond=[],[]
for _ in range(150):
    idx=rng.permutation(len(y)); c,t=idx[:len(y)//2],idx[len(y)//2:]
    pm=ConformalAbortPolicy(m,0.05); pm.calibrate(X[c],y[c])
    pM=MondrianConformalAbortPolicy(m,0.05); pM.calibrate(X[c],y[c])
    flat_conv=ft[t]&(y[t]==1)
    am,_=pm.decide(X[t]); aM,_=pM.decide(X[t])
    am=np.array([a=="abort" for a in am]); aM=np.array([a=="abort" for a in aM])
    marg.append((am&flat_conv).sum()/max(flat_conv.sum(),1))
    mond.append((aM&flat_conv).sum()/max(flat_conv.sum(),1))
print(f"flat-stratum false-abort: MARGINAL={np.mean(marg):.3f}  MONDRIAN={np.mean(mond):.3f} (alpha=0.05)")
assert np.mean(mond)<=0.05+0.01 and np.mean(mond)<np.mean(marg)
print("MONDRIAN TEST PASS")
