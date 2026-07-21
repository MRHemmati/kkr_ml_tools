"""aiida-kkr-mlassist — opt-in ML-assisted SCF-convergence control for aiida-kkr (v1).
Pure-numpy inference core (features/infer/conformal/ranks/decision) usable without AiiDA; the AiiDA
WorkChain lives in .workchain and is exposed via the `aiida.workflows` entry point `kkr.mlassist`.
"""
from importlib import resources

from .features import extract_features, FEATURE_NAMES, T_OBS
from .infer import MLAssistModel
from .conformal import (ConformalAbortPolicy, conformal_abort_threshold, evaluate_policy,
                        MondrianConformalAbortPolicy, flat_starter_stratum)
from .ranks import (validate_chain_ranks, per_step_ranks, common_valid_ranks, energy_points)
from .decision import (MLAssistConfig, ml_decision, telemetry_extras, safe_inspect,
                       MLAssistInspectError, observation_ready, parse_trajectory, build_cumulative_trajectory)
from .calibration import seeded_mondrian_policy, load_seed

__version__ = "0.1.1"
DEFAULT_MODEL_ID = "mlassist_v1_normal_fixed10"


def default_model_path():
    """Path to the packaged frozen model artifact (shipped inside the package)."""
    return str(resources.files(__name__).joinpath("models", f"{DEFAULT_MODEL_ID}.npz"))


def load_default_model():
    """Load the packaged frozen model (numpy only)."""
    return MLAssistModel.load(default_model_path())


__all__ = ["extract_features", "FEATURE_NAMES", "T_OBS", "MLAssistModel", "ConformalAbortPolicy", "MondrianConformalAbortPolicy", "flat_starter_stratum",
           "conformal_abort_threshold", "evaluate_policy", "validate_chain_ranks", "per_step_ranks",
           "common_valid_ranks", "energy_points", "MLAssistConfig", "ml_decision", "telemetry_extras",
           "safe_inspect", "MLAssistInspectError", "observation_ready", "parse_trajectory", "build_cumulative_trajectory", "seeded_mondrian_policy", "load_seed", "default_model_path",
           "load_default_model", "__version__", "DEFAULT_MODEL_ID"]
