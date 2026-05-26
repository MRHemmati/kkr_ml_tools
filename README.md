## Installation

1. Copy WorkChain to AiiDA's Python environment:
   ```bash
   cp ml_restart_protocol.py $(python -c "import site; print(site.getsitepackages())")/
   verdi daemon restart
   ```

2. Import the LSTM model node into your AiiDA profile:
   ```bash
   verdi archive import model_node_100933.aiida
   # note the new PK printed — use it as builder.model_node = load_node(<new_pk>)
   ```
```
import model_node_100933.aiida:

type         SinglefileData
pk           100933
uuid         9c7f4fd7-9396-4e55-8d34-d5a03c1db720
label        KKR-SCF LSTM convergence predictor (T_obs=20)
description  Trained on 2431 normal SCF KkrCalculation sequences. Input: first 20 steps of [log(rms), log(rms_spin), log(|charge_neutrality|)]. Output: log(remaining_iterations). Mean MAPR=+17.5% (LODO). Channels normalised with mean=[-6.29025936126709, -14.268150329589844, -6.470577716827393], std=[3.254223108291626, 6.328523635864258, 4.123773097991943].
ctime        2026-05-26 10:09:08.250586+00:00
mtime        2026-05-26 10:09:08.425981+00:00
```

3. Install dependencies:
   ```bash
   pip install torch numpy  # CPU-only torch is sufficient
   ```

## Usage
See usage example in ml_restart_protocol.py (bottom of file).
# Minimal usage 
``` python
from ml_restart_protocol import MLRestartProtocol
from aiida.orm import load_node, Dict
from aiida.engine import submit

builder = MLRestartProtocol.get_builder()

# kkr_scf_wc inputs
builder.kkr_scf.voronoi         = <voronoi_code>
builder.kkr_scf.kkr             = <kkr_code>
builder.kkr_scf.structure       = <StructureData>
builder.kkr_scf.calc_parameters = Dict(dict={
    'LMAX': 2, 'RCLUSTZ': 0.85, 'NSPIN': 2,
    'RMAX': 10, 'GMAX': 100, 'BRYMIX': 0.01,
})
builder.kkr_scf.wf_parameters   = <wf_params_Dict>
builder.kkr_scf.options         = Dict(dict={...})

# ML inputs — update model_node PK after importing the archive
builder.model_node        = load_node(<pk_after_import>)
builder.max_restarts      = orm.Int(3)
builder.restart_threshold = orm.Int(30)   # tune per system

wc = submit(MLRestartProtocol, **builder)
```