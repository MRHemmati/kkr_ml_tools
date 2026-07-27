"""ADV-4 AiiDA integration STUB (source-only, documentation). This does NOT subclass or modify any
production workchain and does NOT import AiiDA — it defines the intended `convergence_advisor` input
namespace and advisory output shape, plus a pure-python helper to build the advisory output dict. Full
kkr_scf_wc integration is deferred to a gated stage; the integration point is documented below.

INTENDED INTEGRATION (kkr_scf_wc subclass or thin wrapper), advisory-by-default:

    spec.input_namespace('convergence_advisor', required=False, dynamic=True)
    spec.input('convergence_advisor.enabled', valid_type=Bool, default=lambda: Bool(False))
    spec.input('convergence_advisor.index', valid_type=(SinglefileData, Str), required=False)
    spec.input('convergence_advisor.apply_selected', valid_type=List, required=False)   # opt-in tip ids
    spec.input('convergence_advisor.min_confidence', valid_type=Float, required=False)
    spec.input('convergence_advisor.max_evidence_level', valid_type=Str, required=False)
    spec.output('convergence_advisor_tips', valid_type=Dict, required=False)

BEHAVIOUR CONTRACT:
  * Absent namespace or enabled=False  -> IDENTICAL to stock kkr_scf_wc (zero behavioural change).
  * enabled=True, apply_selected empty  -> compute tips, emit `convergence_advisor_tips` Dict, CHANGE NOTHING.
  * enabled=True, apply_selected=[ids]  -> apply ONLY those safe tips to the builder via apply.apply_selected
                                            (donor tips require E1-CERTIFIED), record applied/rejected in the
                                            output Dict. Never mutate pre-existing stored nodes; the applied
                                            change lives on the NEW workchain's inputs (auditable provenance).
  * Label the NEW workchain metadata only (e.g. '..._ADVISOR'); no labels/extras/groups on existing nodes.
"""


def advisory_output_dict(tips, applied_record=None, target_fingerprint=None):
    """Build the plain dict that a workchain would wrap in a Dict output node (provenance-safe)."""
    return {
        "schema": "convergence_advisor_tips_v1",
        "n_tips": len(tips),
        "tips": tips,                                  # each carries evidence_level/n_supporting_runs/confidence/reason
        "applied": (applied_record or {}).get("applied", []),
        "rejected": (applied_record or {}).get("rejected", []),
        "target_fingerprint": target_fingerprint or {},
        "advisory_by_default": True,
    }


INTEGRATION_POINT = (
    "kkr_scf_wc.start / an outer wrapper: after inputs are read, if convergence_advisor.enabled, call "
    "ConvergenceAdvisor(index).advise(target_from_inputs) -> tips; if apply_selected non-empty call "
    "apply.apply_selected(builder_repr, tips, apply_selected, certified_segs) and merge into the builder; "
    "always emit advisory_output_dict(...) as convergence_advisor_tips. No install/daemon change in this stage."
)
