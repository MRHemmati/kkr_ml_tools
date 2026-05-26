from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

from aiida import orm
from aiida.engine import WorkChain, calcfunction, while_
from aiida.plugins import WorkflowFactory

KkrScfWorkChain = WorkflowFactory("kkr.scf")


class KKRConvergenceLSTM(nn.Module):
    def __init__(self, n_ch=3, hidden=64, n_layers=2, n_static=2, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(n_ch, hidden, n_layers, batch_first=True,
                            dropout=dropout if n_layers > 1 else 0.0)
        self.head = nn.Sequential(
            nn.Linear(hidden + n_static, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )
    def forward(self, x, s):
        _, (h, _) = self.lstm(x)
        return self.head(torch.cat([h[-1], s], dim=1)).squeeze(-1)


def _load_bundle(model_node):
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as tmp:
        with model_node.open(mode="rb") as f:
            tmp.write(f.read())
        path = tmp.name
    bundle = torch.load(path, map_location="cpu", weights_only=False)
    os.unlink(path)
    return bundle


def _build_model(bundle):
    model = KKRConvergenceLSTM(
        n_ch=bundle["N_CHANNELS"], hidden=bundle["HIDDEN"],
        n_layers=bundle["N_LAYERS"], n_static=bundle["N_STATIC"],
        dropout=bundle.get("DROPOUT", 0.2),
    )
    model.load_state_dict(bundle["state_dict"])
    model.eval()
    return model


def extract_scf_history(output_params):
    d = output_params.get_dict()
    conv = d.get("convergence_group", {})
    mix  = d.get("mixing_history", {})
    rms_charge = conv.get("rms") or conv.get("rms_all_atoms")
    rms_anom   = conv.get("dos_ef") or conv.get("rms_anom") or rms_charge
    alpha      = mix.get("alpha") or mix.get("mixfac")
    if not (rms_charge and rms_anom and alpha):
        return None
    n = min(len(rms_charge), len(rms_anom), len(alpha))
    arr = np.zeros((n, 3), dtype=np.float32)
    arr[:, 0] = np.log10(np.clip(rms_charge[:n], 1e-15, None))
    arr[:, 1] = np.log10(np.clip(rms_anom[:n],   1e-15, None))
    arr[:, 2] = np.log10(np.clip(alpha[:n],       1e-15, None))
    return arr


def build_static_features(structure, params):
    d = params.get_dict()
    kmesh = d.get("BZKP", d.get("kmesh", [8, 8, 8]))
    n_kpts = (int(kmesh[0]) * int(kmesh[1]) * int(kmesh[2])
               if isinstance(kmesh, (list, tuple)) and len(kmesh) == 3
               else int(kmesh))
    temp_ry = float(d.get("TEMPR", d.get("smearing_temperature", 0.02)))
    return np.array([np.log10(max(n_kpts, 1)),
                     np.log10(max(temp_ry, 1e-10))], dtype=np.float32)


@calcfunction
def ml_predict_remaining_iters(output_params, structure, kkr_params, model_node):
    bundle  = _load_bundle(model_node)
    model   = _build_model(bundle)
    T_OBS   = bundle["T_OBS"]
    ch_mean = np.array(bundle["ch_mean"], dtype=np.float32)
    ch_std  = np.array(bundle["ch_std"],  dtype=np.float32)
    LOG_MIN = bundle["LOG_MIN"]
    LOG_MAX = bundle["LOG_MAX"]

    history = extract_scf_history(output_params)
    if history is None or len(history) < 5:
        return orm.Dict(dict={"pred_log": None, "pred_remaining": None,
                               "n_obs_available": 0 if history is None else len(history),
                               "status": "insufficient_history"})

    if len(history) >= T_OBS:
        window = history[-T_OBS:]
    else:
        pad    = np.tile(history[0], (T_OBS - len(history), 1))
        window = np.vstack([pad, history])

    window_norm = (window - ch_mean) / (ch_std + 1e-8)
    static      = build_static_features(structure, kkr_params)
    x = torch.tensor(window_norm[None], dtype=torch.float32)
    s = torch.tensor(static[None],      dtype=torch.float32)
    with torch.no_grad():
        log_pred = float(model(x, s))
    log_clipped    = float(np.clip(log_pred, LOG_MIN, LOG_MAX))
    pred_remaining = int(np.exp(log_clipped))
    return orm.Dict(dict={"pred_log": round(log_clipped, 4),
                           "pred_remaining": pred_remaining,
                           "n_obs_available": len(history),
                           "status": "ok"})


@calcfunction
def tighten_mixing_params(current_params, pred_result, restart_number):
    d = current_params.get_dict()
    n = int(restart_number.value)
    alpha = float(d.get("MIXFAC", d.get("mixfac", 0.05)))
    brymix = float(d.get("BRYMIX", 0.05))
    nstep  = int(d.get("NSTEP", 200))
    if   n == 0: new_a, new_b, new_n = alpha*0.60, brymix*1.5, nstep
    elif n == 1: new_a, new_b, new_n = alpha*0.42, brymix*2.0, min(nstep, 150)
    else:        new_a, new_b, new_n = max(alpha*0.30, 1e-4), brymix*2.5, min(nstep, 100)
    p = dict(d)
    p["MIXFAC"] = round(new_a, 5)
    p["BRYMIX"] = round(min(new_b, 0.5), 4)
    p["NSTEP"]  = new_n
    return orm.Dict(dict=p)


class MLRestartProtocol(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.expose_inputs(KkrScfWorkChain, namespace="kkr_scf",
                           exclude=["clean_workdir"])
        spec.input("model_node", valid_type=orm.SinglefileData)
        spec.input("max_restarts", valid_type=orm.Int, default=lambda: orm.Int(3))
        spec.input("restart_threshold", valid_type=orm.Int, default=lambda: orm.Int(30))
        spec.expose_outputs(KkrScfWorkChain, namespace="kkr_scf")
        spec.output("ml_predictions", valid_type=orm.List)
        spec.outline(
            cls.setup,
            while_(cls.should_run_scf)(
                cls.run_kkr_scf,
                cls.inspect_and_decide,
            ),
            cls.results,
        )
        spec.exit_code(401, "ERROR_SCF_FAILED",   message="kkr_scf_wc failed")
        spec.exit_code(402, "ERROR_MAX_RESTARTS",  message="Max ML restarts reached")

    def setup(self):
        self.ctx.restart_count  = 0
        self.ctx.ml_predictions = []
        self.ctx.converged      = False
        self.ctx.current_params = self.inputs.kkr_scf.calc_parameters
        self.report(f"MLRestartProtocol: max_restarts={self.inputs.max_restarts.value}, "
                    f"threshold={self.inputs.restart_threshold.value}")

    def should_run_scf(self):
        return (not self.ctx.converged and
                self.ctx.restart_count <= self.inputs.max_restarts.value)

    def run_kkr_scf(self):
        inputs = self.exposed_inputs(KkrScfWorkChain, namespace="kkr_scf")
        inputs["calc_parameters"] = self.ctx.current_params
        if self.ctx.restart_count > 0 and hasattr(self.ctx, "prev_remote"):
            inputs["remote_data"] = self.ctx.prev_remote
        future = self.submit(KkrScfWorkChain, **inputs)
        self.report(f"Submitted kkr_scf_wc attempt {self.ctx.restart_count+1}, PK={future.pk}")
        return self.to_context(current_scf=future)

    def inspect_and_decide(self):
        scf = self.ctx.current_scf
        if not scf.is_finished_ok:
            return self.exit_codes.ERROR_SCF_FAILED
        out_params = scf.outputs.output_parameters
        self.ctx.prev_remote = scf.outputs.remote_folder
        conv_flag = out_params.get_dict().get("convergence_group", {}).get("converged", False)
        if conv_flag:
            self.ctx.converged = True
            self.ctx.final_scf = scf
            self.report("Converged — done.")
            return
        pred = ml_predict_remaining_iters(
            output_params=out_params,
            structure=self.inputs.kkr_scf.structure,
            kkr_params=self.ctx.current_params,
            model_node=self.inputs.model_node,
        )
        self.ctx.ml_predictions.append(pred.get_dict())
        self.report(f"LSTM: status={pred['status']}, pred_remaining={pred['pred_remaining']}")
        should_restart = (
            pred["status"] == "ok"
            and pred["pred_remaining"] is not None
            and pred["pred_remaining"] > self.inputs.restart_threshold.value
            and self.ctx.restart_count < self.inputs.max_restarts.value
        )
        if should_restart:
            self.ctx.restart_count += 1
            self.ctx.current_params = tighten_mixing_params(
                current_params=self.ctx.current_params,
                pred_result=pred,
                restart_number=orm.Int(self.ctx.restart_count - 1),
            )
            self.report(f"ML restart {self.ctx.restart_count}. "
                        f"MIXFAC={self.ctx.current_params['MIXFAC']}")
        else:
            self.ctx.converged = True
            self.ctx.final_scf = scf

    def results(self):
        self.out_many(self.exposed_outputs(self.ctx.final_scf, KkrScfWorkChain, namespace="kkr_scf"))
        self.out("ml_predictions", orm.List(list=self.ctx.ml_predictions))
        self.report(f"Done. restarts={self.ctx.restart_count}, converged={self.ctx.converged}")
