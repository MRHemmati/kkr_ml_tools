"""ml_assist v1 — PURE-NUMPY RandomForest inference (no sklearn). This is what runs in the AiiDA
daemon env (numpy present, sklearn absent). Loads a flattened-forest .npz produced by
phase1_export_model.py and reproduces sklearn's predict_proba EXACTLY.

CRITICAL: sklearn casts X to float32 for tree traversal, so split comparisons MUST be float32 or a
sample sitting on a threshold tie routes to the wrong leaf. predict_proba() enforces this.

Usage:
    from mlassist_infer import MLAssistModel
    m = MLAssistModel.load("mlassist_v1_normal_fixed10.npz")
    m.selfcheck()                       # asserts numpy == sklearn on embedded golden vectors
    p = m.predict_proba(X)[:, 1]        # P(converge)
"""
import numpy as np


class MLAssistModel:
    def __init__(self, art):
        self.cl = art["children_left"]; self.cr = art["children_right"]
        self.feat = art["feature"];     self.thr = art["threshold"]
        self.leaf_proba = art["leaf_proba"]; self.tree_start = art["tree_start"]
        self.classes = art["classes"];  self.feature_names = list(art["feature_names"])
        self._gold_X = art.get("golden_X"); self._gold_p = art.get("golden_proba")

    @classmethod
    def load(cls, path):
        with np.load(path, allow_pickle=False) as z:
            return cls({k: z[k] for k in z.files})

    def predict_proba(self, X):
        X = np.asarray(X, np.float32)               # float32 to match sklearn tree traversal
        if X.ndim == 1: X = X[None, :]
        ts = self.tree_start; C = self.leaf_proba.shape[1]
        acc = np.zeros((len(X), C), dtype=np.float64)
        idx = np.arange(len(X))
        for t in range(len(ts) - 1):
            s, e = ts[t], ts[t + 1]
            clt, crt, ft, tt, lpt = (self.cl[s:e], self.cr[s:e], self.feat[s:e],
                                     self.thr[s:e], self.leaf_proba[s:e])
            node = np.zeros(len(X), np.int64)
            while True:
                leaf = ft[node] == -2
                if leaf.all(): break
                fv = X[idx, np.where(leaf, 0, ft[node])]
                goleft = (~leaf) & (fv <= tt[node]); goright = (~leaf) & (fv > tt[node])
                node = np.where(goleft, clt[node], node); node = np.where(goright, crt[node], node)
            acc += lpt[node]
        return acc / (len(ts) - 1)

    def selfcheck(self, tol=1e-12):
        """assert the numpy path reproduces the embedded sklearn golden vectors (deployment guard)."""
        if self._gold_X is None: raise RuntimeError("artifact has no golden vectors")
        d = float(np.max(np.abs(self.predict_proba(self._gold_X) - self._gold_p)))
        assert d < tol, f"SELFCHECK FAILED: max|numpy-sklearn|={d:.2e} >= {tol:.0e}"
        return d


if __name__ == "__main__":
    import sys
    m = MLAssistModel.load(sys.argv[1] if len(sys.argv) > 1 else
                           "/Users/hemmati/JupyterHub/jbox/Paper/My_ML_cc/workspace/models/mlassist_v1_normal_fixed10.npz")
    print("features:", m.feature_names)
    print("classes:", m.classes.tolist(), "| trees:", len(m.tree_start) - 1)
    print(f"SELFCHECK max|numpy-sklearn| = {m.selfcheck():.2e}  -> PASS")
