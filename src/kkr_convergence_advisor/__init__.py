"""KKR Convergence Advisor (v1) — optional, retrieval/rule-based, advisory-by-default convergence tips
learned read-only from prior KKR runs + the E1 PotentialBank. NOT a deep model. NEVER auto-applies; donor
tips require E1 certification; CPA/BdG get warnings only. Pure-python core (no AiiDA import here)."""
from .engine import ConvergenceAdvisor, grid_valid_ranks
from .apply import apply_selected
from .core import fingerprint, evidence_level, confidence, family_of, compat_class, outcome_stats, label_outcome
from .schema import TIP_SCHEMA, TIP_TYPES, EVIDENCE_LEVELS, TIP_REQUIRED_FIELDS, validate_tip
from .workchain_stub import advisory_output_dict, INTEGRATION_POINT


def default_index_path(name="advisor_index_v1.json"):
    """Path to a packaged advisor data file (index or example tips). Ships as package-data."""
    from importlib.resources import files
    return files(__name__).joinpath("data", name)


def load_index(name="advisor_index_v1.json"):
    """Load the packaged advisor index (or example tips) JSON as a dict."""
    import json
    with default_index_path(name).open("r") as f:
        return json.load(f)


__version__ = "1.0"
__all__ = ["ConvergenceAdvisor", "apply_selected", "fingerprint", "evidence_level", "confidence",
           "family_of", "compat_class", "outcome_stats", "grid_valid_ranks", "TIP_SCHEMA", "TIP_TYPES",
           "EVIDENCE_LEVELS", "TIP_REQUIRED_FIELDS", "validate_tip", "advisory_output_dict",
           "INTEGRATION_POINT", "label_outcome", "default_index_path", "load_index", "__version__"]
