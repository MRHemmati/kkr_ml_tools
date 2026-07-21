# FINAL freeze verification (2026-07-17)

Confirms the pre-registered requirement: **frozen-model artifacts + sha256 exist and their timestamps
PRECEDE any Phase-3 campaign submission** (no fitting the model to the campaign).

## Frozen models (sha256 verified: manifest == file == stored AiiDA node)
| model | created (freeze) | sha256 | provenance node |
|---|---|---|---|
| mlassist_v1_normal_fixed10 (Vehicle B) | 2026-07-12T22:24:17 | cebe56b9f35e4931… | pk 107155 / uuid 9aa7da90 |
| mlassist_v1_bdg_rmsdelta (Vehicle A) | 2026-07-14T13:40:19 | fd67c9a35b1928df… | pk 107156 / uuid bc05dcbd |
| mlassist_v1_bdg_rms (fallback) | 2026-07-14T13:40:25 | b73c14534c169ff8… | pk 107157 / uuid aa84f134 |

- Latest freeze: **2026-07-14**. Calibration seed `calibration_seed_normal.npz` shipped (OOF scores, honest).
- **Vehicle-A/B campaign runs: 0** (not launched) → freeze trivially precedes.
- Bundle validation runs (smoke 107160, abort tests 107175/107338; ctime 2026-07-16/17) POST-DATE the
  freeze and are NOT campaign runs — no leakage.

## Gated bundle — COMPLETE
| step | result |
|---|---|
| 1 pip install into daemon | kkr.mlassist + kkr.bdg registered/loadable |
| 2 /opt shim + daemon restart | old+new import paths -> same kkr_bdg_wc v0.2.3 (PID 2952223) |
| 3 model SinglefileData nodes | 107155/6/7, sha verified |
| 4 advisory smoke (107160) | exit 0 + live telemetry (P=0.945, continue) — full path proven |
| 5 abort firing | LIVE exit-701 abort OBSERVED on runs 107175 (a=.05) & 107338 (a=.10): both ERROR_MLASSIST_ABORT, decision=abort, at ~iter 48 (4th segment) once the trajectory deteriorated (final P 0.520<0.608 / 0.544<0.825). Mechanism validated end-to-end (live + unit test). NOT shown: an EARLY iter-10 abort on an accessible cell — these NbSe2 cells decrease early / deteriorate late, so the conservative policy correctly waits; early-L1-savings demo needs a doped/CPA cell (all on CLAIX). |
| 6 retroactive provenance | 347 nodes stamped kkr_bdg_wc_commit=6d20d09 |

Rollback backup retained: workspace/backups/kkr_bdg_wc.py.opt-backup.*

## Next milestone (gated, awaiting go)
Launch **Vehicle B** (normal-state, th1+viti, alpha=0.10, paired within-system) once the reviewer clears
the pre-reg drafts. Then Vehicle A after its production-mesh NSTEPS=1 BdG-init pre-flight.

---

# STATE CAPSULE (2026-07-19) — bundle CLOSED, going idle

**No further submissions / daemon changes / package installs / DB writes / job kills without a new
explicitly-approved gated plan.**

### 1. Freeze verification
This file. All 3 model artifacts sha256-verified (manifest==file==node); latest freeze 2026-07-14;
0 campaign runs → freeze precedes any submission.

### 2. Model provenance nodes
| model | pk | uuid | sha256 | OOF AUC |
|---|---|---|---|---|
| mlassist_v1_normal_fixed10 | 107155 | 9aa7da90-49ae-41ee-9d1d-49a7595bf467 | cebe56b9f35e4931069142f8a735ae291eab15796446fc5c3b1f94f6e327f549 | 0.944 |
| mlassist_v1_bdg_rmsdelta | 107156 | bc05dcbd-38f5-4d1d-9ad5-bcf85f5dbb37 | fd67c9a35b1928df… | 0.957 |
| mlassist_v1_bdg_rms | 107157 | aa84f134-21da-45ee-90b1-7e259a5372c3 | b73c14534c169ff8… | 0.946 |
UUID map: workspace/models/model_node_uuids.json. Calibration seed: calibration_seed_normal.npz (packaged).

### 3. Package / wheel
`aiida-kkr-mlassist 0.1.0` INSTALLED in /opt/aiida-kernel (from workspace/aiida-kkr-mlassist source).
Source-built wheel sha256 = 37db6a9b23013abc5a0eb8e58bd840e8891d9785f1034f3b27c5c8ec3faae921 (bundles
3 models + seed + kkr_bdg_wc.py). Canonical kkr_bdg_wc = git feature/kkr-bdg-workflow @ 6d20d09
(v0.2.3, GPU-dropped). Entry points: kkr.mlassist, kkr.bdg.

### 4. Daemon / plugin state
Daemon PID 2952223 (restarted 2026-07-16 21:52), 1 worker. `verdi plugin list aiida.workflows` shows
kkr.mlassist + kkr.bdg. /opt injection replaced by a 2-line re-export shim
(/opt/aiida-kkr/aiida_kkr/workflows/kkr_bdg_wc.py → aiida_kkr_mlassist.kkr_bdg_wc) so old-node
process_type still resolves.

### 5. Rollback backup
workspace/backups/kkr_bdg_wc.py.opt-backup.20260716-215132 (sha256 65f1aa1e…) = the pre-migration /opt
file. To fully revert: restore it to /opt, `pip uninstall aiida-kkr-mlassist`, `verdi daemon restart`.

### 6. Jobs from the bundle — ALL TERMINAL (none pending/running)
107160 smoke exit 0 (advisory, telemetry) · 107175 exit 701 (live abort @iter48) · 107179 counterfactual
exit 0 · 107338 exit 701 (live abort @iter48). No bundle jobs in flight.

### 7. NEXT ACTION
**AWAIT reviewer clearance of the pre-reg drafts + the two off-server review-debt items. Then bring a
SEPARATE Vehicle-B launch plan for explicit approval. Do NOT launch Vehicle B yet.**

### Interpretation caveat (per Mohammad)
The abort-demo investigation is SUGGESTIVE (not proof) that early-doomed trajectories concentrate in
harder doped/CPA cells; usable as motivation only. The Vehicle-A campaign must still test the L1-payoff
claim PROSPECTIVELY. The one live exit-701 fired LATE (iter 48), so an early-abort / large-L1-savings
demonstration remains unproven and is deferred to the campaigns.

---

# Step 5 — final precise record (Mohammad-approved wording, 2026-07-19)

- Live exit-701 abort **was observed** for **107175** and **107338**.
- These are **bundle validation runs, NOT Phase-3 campaign runs**.
- The abort fired **late, around iter ~48**, after deterioration became visible.
- Therefore Step 5 **validates the live abort mechanism end-to-end**, but **does NOT yet validate the
  intended early-abort / large-L1-savings payoff at T_obs≈10**.
- **Vehicle-A payoff remains motivation only and must be tested prospectively.**

State capsule ACCEPTED as complete. Status: IDLE. No Vehicle B launch, submissions, daemon/package
changes, DB writes, or job actions without a new explicitly-approved gated plan.
