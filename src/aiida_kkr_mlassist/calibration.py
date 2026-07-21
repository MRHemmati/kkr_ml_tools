"""ml_assist — conformal calibration seeding. A campaign's Mondrian policy is certifiable from run 1 via
a shipped material-matched seed of OUT-OF-SAMPLE (OOF) scores + strata (honest, non-in-sample). As real
campaign labels arrive they refresh/replace the seed. Pure numpy."""
from importlib import resources
import numpy as np
from .conformal import MondrianConformalAbortPolicy


def load_seed(name="calibration_seed_normal"):
    """Return the packaged seed dict {score, y, stratum, material} (OOF scores)."""
    with resources.as_file(resources.files(__package__).joinpath("models", f"{name}.npz")) as p:
        z = np.load(p, allow_pickle=True)
        return {k: z[k] for k in z.files}


def _family(formula):
    if not formula:
        return "unknown"
    return "Bi/NbBi" if "Bi" in formula else ("NbSe2" if "Se" in formula else "other")


def seeded_mondrian_policy(model, alpha=0.05, material=None, seed=None, min_per_stratum=None):
    """Build a Mondrian abort policy seeded from material-matched historical OOF scores.
    material: a family name or a chemical formula (mapped to a family). **NO full-seed fallback for thin
    strata:** when the material is present in the seed we ALWAYS use its matched subset; a thin stratum in
    that subset yields a -inf threshold (advisory-only for that stratum via `certifiable_for`), while
    certifiable strata abort. Only if the material is entirely ABSENT from the seed do we fall back to the
    full seed (there is no material-matched option then; N/A for the NbSe2 Vehicle-B campaign)."""
    seed = seed or load_seed()
    score, y, stratum, mat = seed["score"], seed["y"].astype(int), seed["stratum"], seed["material"]
    fam = _family(material) if material and material not in set(mat) else material
    if fam is not None and fam in set(mat):
        m = (mat == fam)                          # always the matched subset (no thin-stratum fallback)
        score, y, stratum = score[m], y[m], stratum[m]
    pol = MondrianConformalAbortPolicy(model, alpha=alpha)
    pol.calibrate_from_scores(score, y, stratum)
    return pol
