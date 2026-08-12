"""ADV core: target fingerprint, compatibility matching, evidence levels, confidence (pure python)."""
import statistics

# ---- compatibility fields that define a "compatibility class" ----
COMPAT_FIELDS = ("code_family", "nspin", "soc", "cpa", "lmax", "ncheb")


def label_outcome(final_rms, qbound, convergence_criterion=None, excepted=False):
    """Canonical per-run QBOUND convergence label (NOT a fixed 1e-3). ADV-1 index builder uses this rule."""
    if excepted:
        return "censored"
    if final_rms is None:
        return "no-traj"
    qcut = qbound if isinstance(qbound, (int, float)) else (
        convergence_criterion if isinstance(convergence_criterion, (int, float)) else 1e-3)
    if final_rms < qcut:
        return "converged"
    if final_rms > 1e-1:
        return "diverge"
    return "stall"


def family_of(formula):
    if not formula:
        return "unknown"
    if formula.startswith("Nb2Se4") or formula.startswith("Nb16"):
        return "NbSe2"
    if formula.startswith("Bi"):
        return "Bi"
    return "other"


def fingerprint(target):
    """Normalise a target spec into the advisor fingerprint. `target` is a plain dict."""
    fp = dict(
        formula=target.get("formula"),
        family=target.get("family") or family_of(target.get("formula")),
        elements=tuple(target.get("elements") or ()),
        z_sequence=tuple(target.get("z_sequence") or ()),
        n_sites=target.get("n_sites"),
        code_family=target.get("code_family", "standard"),
        nspin=target.get("nspin"), soc=bool(target.get("soc", False)),
        cpa=bool(target.get("cpa", False)), lmax=target.get("lmax"),
        ncheb=target.get("ncheb"),
        contour_npts=tuple(sorted(target.get("contour_npts") or ())),
        planned=dict(target.get("planned") or {}),
    )
    fp["compat_class"] = compat_class(fp)
    return fp


def compat_class(rec):
    return "_".join(f"{k}{rec.get(k)}" for k in COMPAT_FIELDS)


def _same_compat(a, b):
    return all(a.get(k) == b.get(k) for k in COMPAT_FIELDS)


def evidence_level(target_fp, run):
    """Return the strongest evidence level ('A'..'D') at which `run` supports `target_fp`, or None."""
    tc = {k: target_fp.get(k) for k in COMPAT_FIELDS}
    rc = {k: run.get(k) for k in COMPAT_FIELDS}
    same_compat = _same_compat(tc, rc)
    # Level A: exact same structure (z-sequence) AND compatible settings
    if same_compat and target_fp.get("z_sequence") and tuple(run.get("z_sequence") or ()) == target_fp["z_sequence"]:
        return "A"
    # Level B: same formula AND compatibility class
    if same_compat and run.get("formula") and run.get("formula") == target_fp.get("formula"):
        return "B"
    # Level C: same material family AND compatibility class
    if same_compat and run.get("family") and run.get("family") == target_fp.get("family"):
        return "C"
    # Level D: weak / global prior (any normal-state run)
    if run.get("regime") == "normal":
        return "D"
    return None


def bucket_runs(target_fp, runs):
    """Group supporting runs by evidence level. Returns {level: [run,...]}."""
    out = {lv: [] for lv in ("A", "B", "C", "D")}
    for r in runs:
        lv = evidence_level(target_fp, r)
        if lv is not None:
            out[lv].append(r)
    return out


def _tuple_z(run):
    z = run.get("z_sequence")
    return tuple(z) if z else ()


def outcome_stats(runs):
    """Robust stats over a bucket of runs (dedup already one-record-per-run)."""
    n = len(runs)
    conv = [r for r in runs if r.get("outcome") == "converged"]
    fails = [r for r in runs if r.get("outcome") in ("stall", "diverge")]
    iters = [r["iters_to_converge"] for r in conv if isinstance(r.get("iters_to_converge"), int)]
    return dict(
        n=n, n_converged=len(conv), n_failed=len(fails),
        success_rate=(len(conv) / n if n else None),
        stall_rate=(sum(1 for r in runs if r.get("outcome") == "stall") / n if n else None),
        diverge_rate=(sum(1 for r in runs if r.get("outcome") == "diverge") / n if n else None),
        median_iters=(int(statistics.median(iters)) if iters else None),
        iters_n=len(iters),
    )


# ---- confidence: f(evidence level, sample size, outcome consistency) ----
_LEVEL_BASE = {"A": 0.90, "B": 0.70, "C": 0.45, "D": 0.30}
_LEVEL_CAP = {"A": 0.98, "B": 0.85, "C": 0.50, "D": 0.35}   # C/D are capped LOW (transfer hints only)


def confidence(level, n_support, consistency=1.0):
    """consistency in [0,1] (e.g. success_rate or fraction agreeing). Small n and low level -> low conf."""
    base = _LEVEL_BASE.get(level, 0.2)
    size_factor = min(1.0, (n_support or 0) / 5.0)        # saturates at n>=5
    val = base * (0.4 + 0.6 * size_factor) * (0.5 + 0.5 * max(0.0, min(1.0, consistency)))
    return round(min(val, _LEVEL_CAP.get(level, 0.35)), 3)


def is_transfer_hint(level):
    """Level C/D are cross-formula/cross-material transfer hints, never 'safe' instructions."""
    return level in ("C", "D")
