# kkr_ml/lstm_inference.py

import torch
import torch.nn as nn
import numpy as np
from typing import List, Optional, Tuple


# kkr_ml/workchains/ml_restart_protocol.py
"""
MLRestartProtocol — wraps kkr_scf_wc with LSTM-guided restart logic.

Usage:
    from kkr_ml.workchains.ml_restart_protocol import MLRestartProtocol
    from aiida.engine import submit
    from aiida.orm import load_node

    model_node = load_node(<pk of your SinglefileData>)

    node = submit(
        MLRestartProtocol,
        structure         = my_structure,
        parameters        = my_params_dict,
        potential         = my_start_pot,
        kpoints           = my_kpoints,
        options           = my_options_dict,
        model_node        = model_node,
        restart_threshold = Int(350),
        max_restarts      = Int(2),
        mixing_reduction  = Float(0.7),
    )
"""

from aiida.engine   import (WorkChain, calcfunction, while_, if_,
                            ToContext, append_)
from aiida.orm      import (Dict, Int, Float, Str, Bool,
                            SinglefileData, CalcJobNode,
                            WorkChainNode, load_node)
from aiida.plugins  import WorkflowFactory

import tempfile, os, numpy as np

# ── Import inference utility (pure Python, not an AiiDA node) ────────────────
from kkr_ml.lstm_inference import predict_remaining_iterations


# ════════════════════════════════════════════════════════════════════════════
# Helper calcfunction — provenance-tracked prediction
# ════════════════════════════════════════════════════════════════════════════
@calcfunction
def predict_convergence_lstm(
    output_parameters: Dict,
    model_node:        SinglefileData,
    calc_parameters:   Dict,
) -> Dict:
    """
    Provenance-tracked LSTM inference.
    Called after T_OBS steps of a running KkrCalculation.
    Returns a Dict with prediction + metadata.
    """
    d  = output_parameters.get_dict()
    cg = d.get("convergence_group", {})

    rms      = cg.get("rms_all_iterations",               None)
    rms_spin = cg.get("rms_spin_all_iterations",          None)
    ch_neut  = cg.get("charge_neutrality_all_iterations", None)

    if rms is None or len(rms) < 5:
        return Dict(dict={
            "status":             "insufficient_data",
            "n_steps_available":  len(rms) if rms else 0,
            "predicted_remaining": -1,
        })

    params = calc_parameters.get_dict()
    tempr  = float(params.get("<TEMPR>",  600.0))
    brymix = float(params.get("<BRYMIX>", 0.05))

    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as tmp:
        with model_node.open(mode="rb") as f_node:
            tmp.write(f_node.read())
        bundle_path = tmp.name

    try:
        result = predict_remaining_iterations(
            rms_sequence=         rms,
            rms_spin_sequence=    rms_spin if rms_spin else rms,
            charge_neut_sequence= ch_neut  if ch_neut  else [0.0]*len(rms),
            bundle_path=          bundle_path,
            tempr=tempr,
            brymix=brymix,
        )
    finally:
        os.unlink(bundle_path)

    result.update({
        "status":             "ok",
        "n_steps_available":  len(rms),
        "tempr_used":         tempr,
        "brymix_used":        brymix,
    })
    return Dict(dict=result)


# ════════════════════════════════════════════════════════════════════════════
# Helper calcfunction — tighten mixing parameters for restart
# ════════════════════════════════════════════════════════════════════════════
@calcfunction
def build_restart_parameters(
    original_parameters: Dict,
    mixing_reduction:    Float,
    restart_index:       Int,
) -> Dict:
    """
    Returns a new parameters Dict with reduced STRMIX/BRYMIX.
    Each restart multiplies mixing by `mixing_reduction` (e.g. 0.7).
    Also reduces NINIT_BROYDEN to force more linear mixing at startup.
    """
    params = original_parameters.get_dict()
    factor = float(mixing_reduction) ** int(restart_index)

    original_strmix = float(params.get("<STRMIX>", 0.03))
    original_brymix = float(params.get("<BRYMIX>", 0.05))

    new_strmix = round(original_strmix * factor, 5)
    new_brymix = round(original_brymix * factor, 5)

    # Safety floors — below these KKR convergence becomes pathologically slow
    new_strmix = max(new_strmix, 0.005)
    new_brymix = max(new_brymix, 0.008)

    # Increase initial linear mixing steps to stabilise early iterations
    original_ninit = int(params.get("<NINIT_BROYDEN>", 10))
    new_ninit = min(original_ninit + 5 * int(restart_index), 30)

    params["<STRMIX>"]        = new_strmix
    params["<BRYMIX>"]        = new_brymix
    params["<NINIT_BROYDEN>"] = new_ninit

    return Dict(dict=params)


# ════════════════════════════════════════════════════════════════════════════
# Main WorkChain
# ════════════════════════════════════════════════════════════════════════════
class MLRestartProtocol(WorkChain):
    """
    Wraps kkr_scf_wc with LSTM-guided early restart logic.

    Decision logic after T_OBS steps:
      predicted_remaining > restart_threshold  → restart with tighter mixing
      predicted_remaining ≤ restart_threshold  → continue normally
      n_restarts == max_restarts               → continue regardless (give up)
    """

    T_OBS = 20   # must match the trained model

    @classmethod
    def define(cls, spec):
        super().define(spec)

        # ── Pass-through inputs for kkr_scf_wc ───────────────────────────────
        spec.expose_inputs(
            WorkflowFactory("kkr.scf"),
            namespace="scf",
            exclude=("metadata",),
        )

        # ── ML-specific inputs ────────────────────────────────────────────────
        spec.input(
            "model_node",
            valid_type=SinglefileData,
            help="SinglefileData node containing the .pt LSTM bundle",
        )
        spec.input(
            "restart_threshold",
            valid_type=Int,
            default=lambda: Int(350),
            help=(
                "If LSTM predicts more than this many remaining iterations, "
                "restart with tighter mixing. Tune based on your tolerance "
                "budget — 350 ≈ P75 of the training distribution."
            ),
        )
        spec.input(
            "max_restarts",
            valid_type=Int,
            default=lambda: Int(2),
            help="Maximum number of ML-triggered restarts before giving up",
        )
        spec.input(
            "mixing_reduction",
            valid_type=Float,
            default=lambda: Float(0.7),
            help=(
                "Multiply STRMIX and BRYMIX by this factor on each restart. "
                "0.7 means each restart uses 70%% of the previous mixing."
            ),
        )

        # ── Outputs ───────────────────────────────────────────────────────────
        spec.expose_outputs(WorkflowFactory("kkr.scf"), namespace="scf")
        spec.output(
            "ml_prediction",
            valid_type=Dict,
            help="Dict from predict_convergence_lstm — prediction + metadata",
        )
        spec.output(
            "ml_action",
            valid_type=Str,
            help="'continue' | 'restart' | 'max_restarts_reached'",
        )
        spec.output(
            "n_restarts",
            valid_type=Int,
            help="How many ML-triggered restarts occurred",
        )

        # ── Outline ───────────────────────────────────────────────────────────
        spec.outline(
            cls.setup,
            cls.submit_scf,
            cls.inspect_t_obs,       # wait T_OBS steps, then query LSTM
            while_(cls.should_restart)(
                cls.do_restart,
                cls.submit_scf,
                cls.inspect_t_obs,
            ),
            cls.collect_results,
        )

        spec.exit_code(301, "ERROR_SCF_FAILED",
                       message="The kkr_scf_wc sub-workflow failed")
        spec.exit_code(302, "ERROR_INSUFFICIENT_CONVERGENCE_DATA",
                       message="KkrCalculation produced no RMS data after T_OBS steps")

    # ── Setup ─────────────────────────────────────────────────────────────────
    def setup(self):
        self.ctx.n_restarts       = 0
        self.ctx.current_params   = self.inputs.scf.parameters
        self.ctx.restart_decision = "pending"
        self.ctx.last_prediction  = None
        self.report(
            f"MLRestartProtocol started | "
            f"threshold={self.inputs.restart_threshold.value} iters | "
            f"max_restarts={self.inputs.max_restarts.value}"
        )

    # ── Submit kkr_scf_wc ─────────────────────────────────────────────────────
    def submit_scf(self):
        """Submit kkr_scf_wc with current parameters."""
        KkrScfWorkChain = WorkflowFactory("kkr.scf")

        inputs = self.exposed_inputs(KkrScfWorkChain, namespace="scf")
        inputs["parameters"] = self.ctx.current_params

        # On restart, pass the last converged (partial) potential as start_pot
        if hasattr(self.ctx, "last_scf_wc"):
            last_wc = self.ctx.last_scf_wc
            if hasattr(last_wc.outputs, "out_potential"):
                inputs["startpot"] = last_wc.outputs.out_potential
                self.report(
                    f"Restart {self.ctx.n_restarts}: "
                    f"using potential from WC pk={last_wc.pk} as start"
                )

        future = self.submit(KkrScfWorkChain, **inputs)
        self.report(f"Submitted kkr_scf_wc pk={future.pk}")
        return ToContext(last_scf_wc=future)

    # ── Inspect after T_OBS steps ─────────────────────────────────────────────
    def inspect_t_obs(self):
        """
        Wait until the most recent kkr_scf_wc child KkrCalculation has
        completed at least T_OBS iterations, then run LSTM prediction.

        Strategy: kkr_scf_wc finishes a full KkrCalculation before exposing
        output_parameters. We therefore wait for the FIRST finished
        KkrCalculation child, which will have ≥ T_OBS steps if the SCF
        hasn't already converged.
        """
        wc = self.ctx.last_scf_wc

        # ── Check if the whole WC already finished (fast convergence) ─────────
        if wc.is_finished_ok:
            self.report(
                f"kkr_scf_wc pk={wc.pk} finished before inspection — "
                "skipping LSTM (calculation already converged)"
            )
            self.ctx.restart_decision = "already_converged"
            return

        if wc.is_failed:
            self.report(f"kkr_scf_wc pk={wc.pk} FAILED")
            return self.exit_codes.ERROR_SCF_FAILED

        # ── Find the most recent finished KkrCalculation child ────────────────
        child_calcs = [
            n for n in wc.called
            if isinstance(n, CalcJobNode)
            and n.attributes.get("process_label") == "KkrCalculation"
            and n.is_finished_ok
        ]

        if not child_calcs:
            self.report(
                "No finished KkrCalculation children yet — "
                "WorkChain still in first sub-calc. Skipping prediction."
            )
            self.ctx.restart_decision = "no_data_yet"
            return

        # Pick the child with the most iterations (most informative)
        def n_iters(node):
            try:
                d  = node.outputs.output_parameters.get_dict()
                cg = d.get("convergence_group", {})
                return len(cg.get("rms_all_iterations", []))
            except Exception:
                return 0

        best_child = max(child_calcs, key=n_iters)
        n_steps    = n_iters(best_child)

        if n_steps < self.T_OBS:
            self.report(
                f"Best child has only {n_steps} steps < T_OBS={self.T_OBS} "
                "— skipping prediction"
            )
            self.ctx.restart_decision = "insufficient_steps"
            return

        # ── Run LSTM prediction (provenance-tracked) ──────────────────────────
        self.report(
            f"Running LSTM on child pk={best_child.pk} "
            f"({n_steps} steps available)"
        )
        prediction = predict_convergence_lstm(
            output_parameters=best_child.outputs.output_parameters,
            model_node=       self.inputs.model_node,
            calc_parameters=  best_child.inputs.parameters,
        )
        self.ctx.last_prediction = prediction

        pred_rem = prediction["predicted_remaining"]
        ci_low   = prediction["predicted_remaining_low"]
        ci_high  = prediction["predicted_remaining_high"]
        threshold = self.inputs.restart_threshold.value

        self.report(
            f"LSTM prediction: {pred_rem} iters remaining "
            f"(80% CI: {ci_low}–{ci_high}) | "
            f"threshold={threshold}"
        )

        if (pred_rem > threshold
                and self.ctx.n_restarts < self.inputs.max_restarts.value):
            self.ctx.restart_decision = "restart"
            self.report(
                f"Decision: RESTART (predicted {pred_rem} > {threshold})"
            )
        else:
            if self.ctx.n_restarts >= self.inputs.max_restarts.value:
                self.ctx.restart_decision = "max_restarts_reached"
                self.report(
                    f"Decision: CONTINUE (max_restarts={self.inputs.max_restarts.value} reached)"
                )
            else:
                self.ctx.restart_decision = "continue"
                self.report(
                    f"Decision: CONTINUE (predicted {pred_rem} ≤ {threshold})"
                )

    # ── While condition ───────────────────────────────────────────────────────
    def should_restart(self):
        return self.ctx.restart_decision == "restart"

    # ── Restart: build new parameters ─────────────────────────────────────────
    def do_restart(self):
        self.ctx.n_restarts += 1
        new_params = build_restart_parameters(
            original_parameters=self.ctx.current_params,
            mixing_reduction=   self.inputs.mixing_reduction,
            restart_index=      Int(self.ctx.n_restarts),
        )
        self.ctx.current_params = new_params
        p = new_params.get_dict()
        self.report(
            f"Restart {self.ctx.n_restarts}: "
            f"new STRMIX={p.get('<STRMIX>')}, "
            f"BRYMIX={p.get('<BRYMIX>')}, "
            f"NINIT_BROYDEN={p.get('<NINIT_BROYDEN>')}"
        )

    # ── Final collection ──────────────────────────────────────────────────────
    def collect_results(self):
        """Wait for the final kkr_scf_wc to finish and expose outputs."""
        wc = self.ctx.last_scf_wc

        if not wc.is_finished_ok:
            self.report(f"Final kkr_scf_wc pk={wc.pk} did not finish OK")
            return self.exit_codes.ERROR_SCF_FAILED

        # Expose all kkr_scf_wc outputs under the 'scf' namespace
        self.out_many(
            self.exposed_outputs(wc, WorkflowFactory("kkr.scf"),
                                 namespace="scf")
        )

        # ML outputs
        if self.ctx.last_prediction is not None:
            self.out("ml_prediction", self.ctx.last_prediction)
        else:
            self.out("ml_prediction", Dict(dict={
                "status": "no_prediction_made",
                "reason": self.ctx.restart_decision,
            }))

        action_map = {
            "continue":             "continue",
            "max_restarts_reached": "max_restarts_reached",
            "already_converged":    "already_converged",
            "insufficient_steps":   "continue_insufficient_data",
            "no_data_yet":          "continue_no_data",
        }
        action = action_map.get(self.ctx.restart_decision, "continue")
        self.out("ml_action",   Str(action))
        self.out("n_restarts",  Int(self.ctx.n_restarts))

        self.report(
            f"MLRestartProtocol finished | "
            f"action={action} | "
            f"n_restarts={self.ctx.n_restarts}"
        )

class KKRConvergenceLSTM(nn.Module):
    """Identical architecture to Cell 5b — must stay in sync."""
    def __init__(self, n_ch=3, hidden=64, n_layers=2,
                 n_static=2, dropout=0.0):   # dropout=0 at inference
        super().__init__()
        self.lstm = nn.LSTM(n_ch, hidden, n_layers,
                            batch_first=True,
                            dropout=0.0)
        self.head = nn.Sequential(
            nn.Linear(hidden + n_static, 64), nn.ReLU(),
            nn.Linear(64, 32), nn.ReLU(),
            nn.Linear(32, 1),
        )
    def forward(self, x, s):
        _, (h, _) = self.lstm(x)
        return self.head(torch.cat([h[-1], s], dim=1)).squeeze(-1)


def load_model_from_bundle(bundle_path: str) -> Tuple[KKRConvergenceLSTM, dict]:
    """Load model + metadata from a .pt bundle file."""
    bundle = torch.load(bundle_path, map_location="cpu", weights_only=False)
    # In lstm_inference.py — replace the model construction line
    model = KKRConvergenceLSTM(
        n_ch=     bundle["N_CHANNELS"],
        hidden=   bundle["HIDDEN"],
        n_layers= bundle["N_LAYERS"],
        n_static= bundle["N_STATIC"],
        dropout=  bundle.get("DROPOUT", 0.2),  # read from bundle, default 0.2
    )
    model.load_state_dict(bundle["state_dict"])
    model.eval()
    return model, bundle


def predict_remaining_iterations(
    rms_sequence:      List[float],
    rms_spin_sequence: List[float],
    charge_neut_sequence: List[float],
    bundle_path: str,
    tempr: float = 600.0,
    brymix: float = 0.05,
) -> dict:
    """
    Given the first T_OBS steps of a running KkrCalculation,
    predict how many SCF iterations remain.

    Parameters
    ----------
    rms_sequence          : cg/rms_all_iterations[:T_OBS]
    rms_spin_sequence     : cg/rms_spin_all_iterations[:T_OBS]
    charge_neut_sequence  : cg/charge_neutrality_all_iterations[:T_OBS]
    bundle_path           : path to the .pt bundle (from SinglefileData)
    tempr                 : smearing temperature (K)
    brymix                : Broyden mixing factor

    Returns
    -------
    dict with keys:
        predicted_remaining  (int)   — point estimate
        predicted_remaining_low  (int)  — 80% CI lower (×0.6 heuristic)
        predicted_remaining_high (int)  — 80% CI upper (×1.7 heuristic)
        log_pred             (float) — raw log-space prediction
        n_obs                (int)   — steps actually observed
    """
    model, bundle = load_model_from_bundle(bundle_path)
    T_OBS   = bundle["T_OBS"]
    ch_mean = np.array(bundle["ch_mean"], dtype=np.float32)
    ch_std  = np.array(bundle["ch_std"],  dtype=np.float32)
    LOG_MIN = bundle["LOG_MIN"]
    LOG_MAX = bundle["LOG_MAX"]
    LOG_EPS = 1e-12

    n_obs = min(len(rms_sequence), T_OBS)

    # Stack and log-transform channels
    ch_arrays = [
        np.log(np.abs(rms_sequence[:n_obs])          + LOG_EPS),
        np.log(np.abs(rms_spin_sequence[:n_obs])      + LOG_EPS),
        np.log(np.abs(charge_neut_sequence[:n_obs])   + LOG_EPS),
    ]
    X = np.stack(ch_arrays, axis=1).astype(np.float32)  # (n_obs, 3)
    X = (X - ch_mean) / ch_std                          # normalise

    # Pad to T_OBS if fewer steps available (repeat last step)
    if n_obs < T_OBS:
        pad = np.tile(X[-1:], (T_OBS - n_obs, 1))
        X   = np.concatenate([X, pad], axis=0)

    # Static context
    static = np.array([
        np.log(tempr / 600.0 + 1e-3),
        brymix / 0.05,
    ], dtype=np.float32)

    X_t = torch.tensor(X).unsqueeze(0)          # (1, T_OBS, 3)
    s_t = torch.tensor(static).unsqueeze(0)     # (1, 2)

    with torch.no_grad():
        log_pred = float(model(X_t, s_t).squeeze())

    log_pred  = np.clip(log_pred, LOG_MIN, LOG_MAX)
    pred_rem  = int(np.round(np.exp(log_pred)))

    # Empirical CI: log-space std ≈ 0.52 from LODO residuals
    # → asymmetric bounds in linear space
    pred_low  = int(np.exp(log_pred - 0.52))
    pred_high = int(np.exp(log_pred + 0.52))

    return {
        "predicted_remaining":      pred_rem,
        "predicted_remaining_low":  pred_low,
        "predicted_remaining_high": pred_high,
        "log_pred":                 log_pred,
        "n_obs":                    n_obs,
    }