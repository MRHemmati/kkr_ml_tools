# Frozen model artifacts

This folder holds the **human-facing** model provenance: manifests (feature schema, training-data hash,
library versions, in-distribution AUC), the model card, the AiiDA SinglefileData node UUIDs, and sha256
hashes. The **binary `.npz` models themselves ship inside the installable package** at
`src/aiida_kkr_mlassist/models/` (package-data, loaded via `importlib.resources`); they are not duplicated
here. Verify integrity with `MODEL_HASHES.txt`.
