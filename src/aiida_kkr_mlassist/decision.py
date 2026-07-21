"""ml_assist — pure decision core (no AiiDA). Opt-in config, the ml_decision state machine, telemetry
schema, and graceful sub-step failure handling. Importable with numpy only (runs in the daemon env)."""
from dataclasses import dataclass
import numpy as np
from .features import extract_features, enough_iters, T_OBS, FEATURE_NAMES


@dataclass
class MLAssistConfig:
    enabled: bool = True
    mode: str = "advisory"                 # 'advisory' (record only) | 'abort' (may abort runs)
    alpha: float = 0.05
    t_obs: int = T_OBS
    model_id: str = "mlassist_v1_normal_fixed10"
    model_path: str = ""                   # empty -> packaged default model


def observation_ready(rms, t_obs=T_OBS):
    return enough_iters(rms, t_obs)


def parse_trajectory(convergence_group, input_params):
    """Pure (aiida-free) extraction of (rms, chneut, mixing-params) from ONE KkrCalculation's parsed
    convergence_group + input parameter dict. (Single segment; use build_cumulative_trajectory across a
    multi-segment run.)"""
    cg, p = dict(convergence_group or {}), dict(input_params or {})
    rms = cg.get("rms_all_iterations") or cg.get("rms") or []
    chneut = cg.get("charge_neutrality_all_iterations") or cg.get("charge_neutrality")
    params = {k: p.get(kk) for k, kk in [("tempr", "TEMPR"), ("brymix", "BRYMIX"), ("strmix", "STRMIX")]}
    return list(rms), (list(chneut) if chneut is not None else None), params


def build_cumulative_trajectory(segments):
    """Pure (aiida-free) CUMULATIVE (rms, chneut, params) across ORDERED SCF segments — the fix for the
    Stage-B finding (a single kkr_scf_wc segment of nsteps=10 only reports its own 10 iters, so reading
    only the LAST segment perpetually returns 'wait'; the model must see the trajectory ACROSS segments).
      segments: list of dicts {convergence_group, input_params}, in CHRONOLOGICAL order.
    Each KKR restart segment's convergence_group reports ONLY that segment's iterations, so the cumulative
    trajectory is their in-order concatenation (no duplicated iterations). A defensive guard drops an
    exact prefix-overlap in case a segment ever reports cumulatively. Mixing/parameter context is taken
    from the FIRST (cold-start) segment, matching how the frozen model's features were defined (one
    cold-start row per run). Returns (rms_list, chneut_list_or_None, params_dict)."""
    rms, chneut, have_chneut = [], [], False
    for seg in segments or []:
        r, c, _ = parse_trajectory(seg.get("convergence_group"), seg.get("input_params"))
        # defensive: if this segment restates the whole run so far (prefix overlap), keep only the tail
        if r and len(r) >= len(rms) and list(r[:len(rms)]) == list(rms):
            r = r[len(rms):]; c = (c[len(rms):] if c is not None else None)
        rms.extend(r)
        if c is not None:
            chneut.extend(c); have_chneut = True
    params = parse_trajectory({}, (segments[0].get("input_params") if segments else {}))[2]
    return rms, (chneut if have_chneut else None), params


def ml_decision(policy, rms, chneut=None, params=None, cfg: MLAssistConfig = None):
    """Pure decision. Returns (action, telemetry). action in {wait, continue, abort, abstain}."""
    cfg = cfg or MLAssistConfig()
    if not observation_ready(rms, cfg.t_obs):
        return "wait", {"reason": "insufficient_iters", "n_obs": int(len(np.asarray(rms)))}
    x = extract_features(rms, chneut, params, cfg.t_obs)
    p_conv = float(policy.p_converge(np.atleast_2d(x))[0])
    # threshold + calibration count work for BOTH the marginal policy (scalar .threshold) and the
    # Mondrian policy (per-stratum via .threshold_for / dict .n_calib).
    thr = float(policy.threshold_for(x)) if hasattr(policy, "threshold_for") else float(policy.threshold)
    ncal = policy.n_calib.get(policy.strata_fn(x), 0) if isinstance(policy.n_calib, dict) else policy.n_calib
    # PER-STRATUM certifiability for Mondrian (a non-certifiable stratum is advisory-only, never aborts,
    # while other strata still abort); single-threshold policies keep the global abstain behaviour.
    per_stratum = hasattr(policy, "certifiable_for")
    cert = policy.certifiable_for(x) if per_stratum else policy.certifiable()
    tel = {"model_id": cfg.model_id, "mode": cfg.mode, "alpha": cfg.alpha, "t_obs": cfg.t_obs,
           "p_converge": p_conv, "conformal_threshold": thr,
           "certifiable": bool(cert), "stratum_advisory_only": bool(per_stratum and not cert),
           "n_calib_pos": int(ncal), "features": dict(zip(FEATURE_NAMES, [float(v) for v in x]))}
    if not cert:
        if per_stratum:                                    # this stratum advisory-only -> never abort
            tel["action"] = "continue_advisory_stratum"; return "continue", tel
        tel["action"] = "abstain"; return "abstain", tel   # single-threshold policy defers globally
    would_abort = p_conv < thr
    if would_abort and cfg.mode == "abort":
        tel["action"] = "abort"; return "abort", tel
    tel["action"] = "continue" + ("_would_abort" if would_abort else "")
    return "continue", tel


def score_bdg_dual(policy_full, policy_rms, rms, chneut, params, delta_traj, cfg=None):
    """Vehicle-A BdG scoring with dual-scoring telemetry (Rider 1) + missing-Δ fallback (Rider 2).
    Logs BOTH p(rms-only) and p(rms+Δ) every run (post-campaign paired prospective Δ-lift test).
    The ABORT decision uses the rms+Δ policy when Δ is parseable; if Δ is missing/short (format drift,
    absent file) it FALLS BACK to the rms-only policy and records delta_available=False.
    policy_full.model expects [rms-features .. Δ-features]; policy_rms.model expects [rms-features]."""
    from .bdg_parser import delta_features
    cfg = cfg or MLAssistConfig(mode="advisory")
    if not observation_ready(rms, cfg.t_obs):
        return "wait", {"reason": "insufficient_iters", "n_obs": int(len(np.asarray(rms)))}
    x_rms = extract_features(rms, chneut, params, cfg.t_obs)
    p_rms = float(policy_rms.p_converge(np.atleast_2d(x_rms))[0])
    x_delta = delta_features(delta_traj, cfg.t_obs) if delta_traj is not None else None
    delta_ok = x_delta is not None
    if delta_ok:
        p_full = float(policy_full.p_converge(np.atleast_2d(x_rms + x_delta))[0])
        policy, p_used = policy_full, p_full                 # deployed decision model
    else:
        p_full, policy, p_used = None, policy_rms, p_rms      # fallback to rms-only
    thr = float(policy.threshold_for(x_rms + x_delta) if (delta_ok and hasattr(policy, "threshold_for"))
                else (policy.threshold_for(x_rms) if hasattr(policy, "threshold_for") else policy.threshold))
    tel = {"model_id": cfg.model_id, "mode": cfg.mode, "alpha": cfg.alpha, "t_obs": cfg.t_obs,
           "p_rms_only": p_rms, "p_rms_plus_delta": p_full, "p_converge": p_used,
           "delta_available": delta_ok, "conformal_threshold": thr,
           "certifiable": bool(policy.certifiable())}
    if not policy.certifiable():
        tel["action"] = "abstain"; return "abstain", tel
    would_abort = p_used < thr
    if would_abort and cfg.mode == "abort":
        tel["action"] = "abort"; return "abort", tel
    tel["action"] = "continue" + ("_would_abort" if would_abort else "")
    return "continue", tel


def telemetry_extras(tel, decision):
    return {"ml_assist": {"version": "v1", "decision": decision, **tel}}


class MLAssistInspectError(Exception):
    """Typed error so a failed sub-step surfaces cleanly instead of a raw KeyError stack trace."""


def safe_inspect(inspect_fn, *args, **kwargs):
    try:
        return inspect_fn(*args, **kwargs)
    except KeyError as e:
        raise MLAssistInspectError(
            f"sub-step produced no parseable output ({e}); the calc likely aborted early "
            f"(e.g. 'No rest ranks', NaN, walltime). ml_assist fails clean with a typed error.") from e
