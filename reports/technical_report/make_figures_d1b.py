"""Regenerate report figures from D1b/D1-QC artifacts (local, read-only inputs). venv matplotlib.
Outputs: figures/figD1_percohort.pdf, figD2_calibrated_savings.pdf, figD3_transport_recal.pdf,
figD4_pilot.pdf. No AiiDA, no compute campaign."""
import json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
R=json.load(open('report/d1b_metrics.json')); Q=json.load(open('report/d1_qc_metrics.json'))
OUT='report/figures'

# ---- figD1: per-cohort ML vs RMS@10 AUC (the honest one-look) ----
order=['primary_NbSe2_normal_cold','primary_NbSe2_normal_warm','sec_Bi','sec_otherKKR','sec_BdG_misfit','sec_unknown','sec_warm_restart_all']
lbl={'primary_NbSe2_normal_cold':'NbSe$_2$-normal\nCOLD (primary)','primary_NbSe2_normal_warm':'NbSe$_2$-normal\nWARM','sec_Bi':'Bi/NbBi','sec_otherKKR':'other-KKR','sec_BdG_misfit':'BdG-misfit\n(norm.model)','sec_unknown':'unknown','sec_warm_restart_all':'warm/restart\n(all fam)'}
def g(k,m):
    a=R[k]['auc']; return (a[m]['auc'],a[m]['auc']-a[m]['lo'],a[m]['hi']-a[m]['auc']) if a and a.get(m) else (np.nan,0,0)
x=np.arange(len(order)); w=0.38
fig,ax=plt.subplots(figsize=(9,4))
ml=[g(k,'ML') for k in order]; rm=[g(k,'RMS10') for k in order]
ax.bar(x-w/2,[m[0] for m in ml],w,yerr=[[m[1] for m in ml],[m[2] for m in ml]],capsize=3,label='frozen ML',color='#cc6677')
ax.bar(x+w/2,[m[0] for m in rm],w,yerr=[[m[1] for m in rm],[m[2] for m in rm]],capsize=3,label='RMS@10',color='#4477aa')
ax.axhline(0.5,ls=':',c='k',lw=.8)
ax.set_xticks(x); ax.set_xticklabels([lbl[k]+f"\nn={R[k]['n']} c={R[k]['converged']}" for k in order],fontsize=8)
ax.set_ylabel('held-out AUC (per-QBOUND labels)'); ax.set_ylim(0,1.05)
ax.legend(loc='lower left'); plt.tight_layout(); plt.savefig(f'{OUT}/figD1_percohort.pdf'); plt.close()

# ---- figD2: calibrated risk-savings on the primary cohort (ML vs RMS@10) ----
pr=R['primary_NbSe2_normal']['recal']; alphas=[0.05,0.10,0.20]; ak=['a0.05','a0.1','a0.2']
ml_rec=[pr[a]['ML']['recall'] for a in ak]; rm_rec=[pr[a]['RMS10']['recall'] for a in ak]
ml_sav=[pr[a]['ML']['saved_frac'] for a in ak]; rm_sav=[pr[a]['RMS10']['saved_frac'] for a in ak]
ml_fa=[pr[a]['ML']['fa'] for a in ak]; rm_fa=[pr[a]['RMS10']['fa'] for a in ak]
fig,ax=plt.subplots(1,2,figsize=(10,3.8))
ax[0].plot(alphas,rm_rec,'s-',color='#4477aa',label='RMS@10 recall')
ax[0].plot(alphas,ml_rec,'o-',color='#cc6677',label='ML recall')
ax[0].plot(alphas,rm_fa,'x--',color='gray',label='realized FA')
ax[0].plot(alphas,alphas,':',c='k',lw=.8,label='target FA')
ax[0].set_xlabel(r'target false-abort $\alpha$'); ax[0].set_ylabel('failed-run recall'); ax[0].set_title('(a) Recall @ calibrated FA (primary cohort)'); ax[0].legend(fontsize=8)
ax[1].plot(alphas,rm_sav,'s-',color='#4477aa',label='RMS@10')
ax[1].plot(alphas,ml_sav,'o-',color='#cc6677',label='ML')
ax[1].set_xlabel(r'target false-abort $\alpha$'); ax[1].set_ylabel('fraction of wasted iters saved'); ax[1].set_title('(b) Compute saved (primary cohort)'); ax[1].legend(fontsize=8)
plt.tight_layout(); plt.savefig(f'{OUT}/figD2_calibrated_savings.pdf'); plt.close()

# ---- figD3: conformal transport vs recalibration ----
# seeded (D1, NbSe2 seed applied to pooled held-out) false-abort vs recalibrated
fig,ax=plt.subplots(figsize=(6,4))
cats=['seeded threshold\n(NbSe$_2$ seed,\nno recal)','per-cohort\nrecalibrated']
seeded_fa=0.468; recal_ml=Q['recalibration']['alpha_0.1']['ML']['fa_mean']; recal_rms=Q['recalibration']['alpha_0.1']['RMS@10']['fa_mean']
ax.bar([0],[seeded_fa],0.5,color='#cc6677',label='realized false-abort')
ax.bar([1-0.13],[recal_ml],0.26,color='#cc6677')
ax.bar([1+0.13],[recal_rms],0.26,color='#4477aa',label='RMS@10 recal')
ax.axhline(0.10,ls=':',c='k',lw=1,label=r'target $\alpha=0.10$')
ax.set_xticks([0,1]); ax.set_xticklabels(cats,fontsize=9)
ax.set_ylabel(r'realized false-abort rate @ $\alpha=0.10$'); ax.set_ylim(0,0.55)
ax.annotate('seed does\nNOT transport',(0,seeded_fa),xytext=(0.15,0.40),fontsize=8,arrowprops=dict(arrowstyle='->'))
ax.legend(fontsize=8,loc='upper right'); plt.tight_layout(); plt.savefig(f'{OUT}/figD3_transport_recal.pdf'); plt.close()

# ---- figD4: live pilot S5 abort vs S1 withheld (schematic from recorded trajectories) ----
fig,ax=plt.subplots(figsize=(6.5,4))
# recorded: S5 diverged (C2a counterfactual 150 iters); C2b aborted at iter 20. S1 converged 145 iters, p=0.262 (withheld).
it=np.arange(1,151)
s5=0.22*np.exp(0.008*it)  # diverging-ish schematic to rms rising
s1=0.22*np.exp(-0.03*it)+2.8e-5
ax.semilogy(it,s5,color='#cc6677',label='S5 (Fe 92%): diverges — stock 150 it')
ax.semilogy(it[:20],s5[:20],color='#cc6677',lw=3)
ax.axvline(20,ls='--',c='#cc6677',lw=1)
ax.annotate('ML ABORT @iter20\n(P=0.297<thr) — saved ~130 it',(20,s5[19]),xytext=(35,0.6),fontsize=8,color='#cc6677',arrowprops=dict(arrowstyle='->',color='#cc6677'))
ax.semilogy(it,s1,color='#228833',label='S1 (pristine): converges — 145 it')
ax.annotate('S1 P=0.262 (low) but CONVERGES\n-> advisory withheld abort (correct)',(60,s1[59]),xytext=(45,3e-3),fontsize=8,color='#228833',arrowprops=dict(arrowstyle='->',color='#228833'))
ax.axhline(1e-3,ls=':',c='gray',lw=.8)
ax.set_xlabel('SCF iteration'); ax.set_ylabel('RMS error'); ax.set_title('Live Fe-pilot: S5 true abort, S1 withheld (schematic)')
ax.legend(fontsize=8,loc='lower left'); plt.tight_layout(); plt.savefig(f'{OUT}/figD4_pilot.pdf'); plt.close()
print("wrote figD1_percohort, figD2_calibrated_savings, figD3_transport_recal, figD4_pilot")
