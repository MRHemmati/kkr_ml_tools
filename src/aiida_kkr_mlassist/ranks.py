"""ml_assist v1 — MPI-rank / energy-grid auto-validator (reviewer §3, kkr_bdg_wc footgun #1).
KKR parallelises over energy points; MPI ranks must DIVIDE each step's energy-point count or the run
aborts 'No rest ranks allowed'. A multi-step chain (kkr_bdg_wc: normal SCF 24-pt, semi-circle/BdG 32-pt)
has DIFFERENT grids per step, so:
  - floor rule: a single shared rank count must be a COMMON divisor of ALL step grids;
  - preferred (v0.2.4): PER-STEP ranks — each step gets its own grid-valid count near the budget.
Doctrine sweet spot = 2-3 energy points per rank; 1 pt/rank = latency mode. Pure functions; no AiiDA.
"""
import numpy as np


def divisors(n):
    n = int(n)
    return [d for d in range(1, n + 1) if n % d == 0]


def energy_points(params):
    """Energy-point count of a KKR contour from its parameters.
    Semi-circle contour -> NPT1 alone; standard fine contour -> NPOL+NPT1+NPT2+NPT3."""
    g = {k.strip("<>").upper(): v for k, v in dict(params).items()}
    if g.get("USE_SEMI_CIRCLE_CONTOUR"):
        return int(g.get("NPT1", 0))
    return int(g.get("NPOL", 0)) + int(g.get("NPT1", 0)) + int(g.get("NPT2", 0)) + int(g.get("NPT3", 0))


def valid_ranks(npts, max_ranks=None):
    ds = divisors(npts)
    return [d for d in ds if (max_ranks is None or d <= max_ranks)]


def common_valid_ranks(step_grids, max_ranks=None):
    """Ranks valid for EVERY step (the floor rule for a single shared rank count)."""
    sets = [set(valid_ranks(g, max_ranks)) for g in step_grids]
    return sorted(set.intersection(*sets)) if sets else []


def best_rank(npts, budget, pts_per_rank=(3, 2)):
    """Pick the grid-valid rank <= budget maximising utilisation: prefer ~pts_per_rank energy pts/rank
    (avoid 1 pt/rank latency mode) but never exceed budget. Falls back to the largest valid divisor."""
    cands = valid_ranks(npts, budget)
    if not cands:
        return 1
    for ppr in pts_per_rank:                      # try 3 pts/rank, then 2
        target = max(1, npts // ppr)
        ok = [d for d in cands if d <= target]
        if ok:
            return max(ok)
    return max(cands)


def per_step_ranks(step_grids, budget, pts_per_rank=(3, 2)):
    """Reviewer's preferred v0.2.4 fix: each step its own grid-valid rank near the budget."""
    return [best_rank(g, budget, pts_per_rank) for g in step_grids]


def validate_chain_ranks(requested_ranks, step_grids):
    """Every-step validation for a SHARED rank count. Returns (ok, message, suggested_common_ranks)."""
    bad = [g for g in step_grids if int(requested_ranks) > g or g % int(requested_ranks) != 0]
    common = common_valid_ranks(step_grids)
    if not bad:
        return True, f"ranks={requested_ranks} divide all step grids {step_grids}", common
    return (False,
            f"ranks={requested_ranks} do NOT divide step grid(s) {bad}; would abort 'No rest ranks'. "
            f"Common-divisor ranks for {step_grids} = {common} (or use per-step ranks).",
            common)
