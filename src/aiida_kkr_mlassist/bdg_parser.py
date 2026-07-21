"""ml_assist — BdG Δ-channel parser (Δ7). The standard aiida-kkr parser exposes per-iteration RMS and
charge-neutrality but NOT the pairing (anomalous / Δ) channel. KKRhost-BdG prints `l-independent delta`
once per pairing component (typically 2 spin components), just before each `ITERATION N` marker. This
module extracts the per-iteration Δ trajectory from out_kkr and derives Δ-channel features — the
physically-motivated signal for the weak normal->BdG outcome transfer (a growing Δ = pairing instability,
the BdG-specific failure mode invisible to normal-state RMS features). Pure text/numpy; no AiiDA.
"""
import re
import numpy as np

_DELTA = re.compile(r"l-independent delta:\s*([0-9.eEdD+\-]+)")
_ITER_RMS = re.compile(r"ITERATION\s+(\d+)\s+average rms-error")


def _to_float(s):
    return float(s.replace("D", "E").replace("d", "E"))


def parse_delta_trajectory(out_kkr_text, reduce="mean"):
    """Per-iteration Δ trajectory from out_kkr text.
    The Δ value(s) for iteration N are the `l-independent delta` lines that PRECEDE that iteration's
    `average rms-error` marker (KKRhost prints Δ from the current potential, then the iteration result).
    Returns (traj, per_iter) where traj[k] reduces iteration k+1's components (mean|first|min|max) and
    per_iter is the raw list-of-lists. Trailing Δ lines after the last iteration marker are ignored."""
    per_iter, cur = [], []
    for line in out_kkr_text.splitlines():
        md = _DELTA.search(line)
        if md:
            cur.append(_to_float(md.group(1))); continue
        if _ITER_RMS.search(line) and cur:
            per_iter.append(cur); cur = []
    red = {"mean": np.mean, "first": lambda a: a[0], "min": np.min, "max": np.max}[reduce]
    traj = np.array([float(red(d)) for d in per_iter]) if per_iter else np.array([])
    return traj, per_iter


def parse_delta_from_calc(calc, reduce="mean"):
    """Extract the Δ trajectory from an AiiDA KkrCalculation's retrieved out_kkr (BdG runs only)."""
    rf = calc.outputs.retrieved
    if "out_kkr" not in rf.list_object_names():
        return np.array([]), []
    return parse_delta_trajectory(rf.get_object_content("out_kkr"), reduce)


DELTA_FEATURE_NAMES = ["logdelta_0", "logdelta_last", "logdelta_mean", "logdelta_slope",
                       "logdelta_drop", "delta_rel_range", "delta_grew"]


def delta_features(delta_traj, T):
    """BdG Δ-channel features over the first T iterations (append to the normal feature vector for a
    BdG-regime model). Captures whether the pairing amplitude is decaying (healthy), flat, or GROWING
    (pairing instability -> the BdG-specific doom mode). Returns None if too few Δ iterations."""
    d = np.abs(np.asarray(delta_traj, float))
    if len(d) < T:
        return None
    w = np.log10(np.clip(d[:T], 1e-30, None))
    slope = float(np.polyfit(np.arange(len(w)), w, 1)[0])
    rng = float((d[:T].max() - d[:T].min()) / max(d[:T].max(), 1e-30))
    grew = float(d[:T].argmax() > d[:T].argmin())          # 1 if Δ is trending up within the window
    return [w[0], w[-1], float(w.mean()), slope, w[0] - w[-1], rng, grew]
