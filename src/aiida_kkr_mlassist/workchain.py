"""ml_assist — opt-in AiiDA WorkChain (entry point `kkr.mlassist`). Imports aiida_kkr at module load,
so it is resolved only inside the daemon env (which has aiida-kkr). The pure decision/inference core
lives in the aiida-free sibling modules and is fully unit-tested there.

Behaviour:
  * No `ml_assist` input  -> identical to kkr_scf_wc (zero-risk default).
  * `ml_assist` provided  -> at the observation window, score P(converge) with the frozen numpy model,
    apply the per-campaign conformal policy, record telemetry in node extras. In 'abort' mode a
    certifiable doomed verdict stops the run early (ERROR_MLASSIST_ABORT); 'advisory' only records.
  * inspect_kkr is wrapped by safe_inspect -> an aborted sub-step yields a typed exit, not a stack trace.

INTEGRATION NOTE: the single line that pulls the live RMS/charge-neutrality trajectory + mixing params
from the running calc (`_read_trajectory`) is finalized and exercised during the gated live-wiring step;
everything else (opt-in, model/policy resolution, decision, telemetry, exit codes) is complete here.
"""
from aiida import orm
from aiida.engine import ExitCode
from aiida_kkr.workflows.kkr_scf import kkr_scf_wc

from . import load_default_model, MLAssistModel
from .calibration import seeded_mondrian_policy
from .decision import (MLAssistConfig, ml_decision, telemetry_extras, safe_inspect,
                       MLAssistInspectError, parse_trajectory, build_cumulative_trajectory)


class MLAssistKkrScfWorkChain(kkr_scf_wc):
    """Opt-in ml_assist wrapper around kkr_scf_wc."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input("ml_assist", valid_type=orm.Dict, required=False,
                   help="ml_assist config: enabled, mode(advisory|abort), alpha, t_obs, model_id. "
                        "Absent -> vanilla kkr_scf_wc.")
        spec.input("ml_assist_model", valid_type=orm.SinglefileData, required=False,
                   help="Versioned frozen-model artifact (.npz). Absent -> packaged default model.")
        spec.exit_code(701, "ERROR_MLASSIST_ABORT",
                       message="ml_assist aborted a conformally-doomed run (intended early stop).")
        spec.exit_code(702, "ERROR_SUBSTEP_UNPARSEABLE",
                       message="a sub-step produced no parseable output (caught cleanly by ml_assist).")

    # ---- helpers -------------------------------------------------------------
    def _mlassist_on(self):
        return "ml_assist" in self.inputs and self.inputs.ml_assist.get_dict().get("enabled", True)

    def _config(self):
        return MLAssistConfig(**{k: v for k, v in self.inputs.ml_assist.get_dict().items()
                                 if k in MLAssistConfig.__dataclass_fields__})

    def _load_model(self):
        """Frozen model from an input SinglefileData artifact, else the packaged default."""
        if "ml_assist_model" in self.inputs:
            import tempfile, os
            with self.inputs.ml_assist_model.open(mode="rb") as fh:
                tmp = tempfile.NamedTemporaryFile(suffix=".npz", delete=False); tmp.write(fh.read()); tmp.close()
            model = MLAssistModel.load(tmp.name); os.unlink(tmp.name)
            return model
        return load_default_model()

    def _run_material(self):
        """Best-effort chemical formula of this run (for material-matched calibration seeding)."""
        try:
            return self.inputs.structure.get_formula()
        except Exception:
            return None

    def _resolve_policy(self, cfg):
        """Build the Mondrian abort policy, calibrated from the material-matched OOF seed (certifiable
        from run 1); refreshed online by the campaign flywheel in deployment."""
        return seeded_mondrian_policy(self._load_model(), alpha=cfg.alpha, material=self._run_material())

    def _read_trajectory(self):
        """Pull the CUMULATIVE (rms, chneut, mixing-params) across ALL SCF segments of this workchain, in
        chronological order (Stage-B fix). A single kkr_scf_wc segment (nsteps=10) reports only its own 10
        iterations, so reading the last segment alone perpetually returns 'wait'; the model needs the
        trajectory accumulated across segments. Mixing context = the first (cold-start) segment."""
        from aiida.orm import CalcJobNode
        calcs = sorted(
            [c for c in self.node.called_descendants
             if isinstance(c, CalcJobNode) and getattr(c, "process_label", "") == "KkrCalculation"],
            key=lambda c: c.ctime)
        segments = []
        for c in calcs:
            try:
                cg = c.outputs.output_parameters.get_dict().get("convergence_group", {})
            except Exception:
                continue                      # segment with no parsed output yet -> skip
            segments.append({"convergence_group": cg, "input_params": c.inputs.parameters.get_dict()})
        if not segments:
            return [], None, {}
        return build_cumulative_trajectory(segments)

    def mlassist_decide(self, rms, chneut, params, cfg=None):
        """Testable decision path (what inspect_kkr runs, minus the AiiDA ctx plumbing): resolve the
        seeded policy, score the trajectory, return (action, telemetry_extras)."""
        cfg = cfg or self._config()
        policy = self._resolve_policy(cfg)
        action, tel = ml_decision(policy, rms, chneut, params, cfg)
        return action, telemetry_extras(tel, action)

    # ---- hook ----------------------------------------------------------------
    def inspect_kkr(self):
        """Fire the predictor at the observation window, then defer to base inspection (wrapped so an
        aborted sub-step exits clean)."""
        if not self._mlassist_on():
            return super().inspect_kkr()               # zero-risk passthrough
        try:
            base = safe_inspect(super().inspect_kkr)
        except MLAssistInspectError as exc:
            self.report(f"ml_assist: {exc}")
            return self.exit_codes.ERROR_SUBSTEP_UNPARSEABLE
        cfg = self._config()
        rms, chneut, params = self._read_trajectory()
        action, extras = self.mlassist_decide(rms, chneut, params, cfg)
        self.node.base.extras.set_many(extras)
        self.report(f"ml_assist decision={action} "
                    f"P(converge)={extras['ml_assist'].get('p_converge')} mode={cfg.mode}")
        if action == "abort":
            return self.exit_codes.ERROR_MLASSIST_ABORT
        return base
