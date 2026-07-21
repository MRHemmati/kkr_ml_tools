"""ml_assist v1 — per-campaign CONFORMAL abort policy (Δ4 / gate G1).
The abort decision: abort a run early iff P(converge) is conformally low enough that we are confident
it will NOT converge. One-sided split conformal controls the FALSE-ABORT rate:
    P(abort | the run would actually converge) <= alpha        (alpha <= 0.05 per the reviewer)
Calibrate on a campaign's own converged runs (the flywheel) -> a threshold on P(converge). Abort iff
score < threshold. If too few calibration points to guarantee alpha, threshold = -inf => never abort
(ABSTAIN: advisory only). This is deployment logic; it needs only numpy + the frozen model.
"""
import numpy as np


def conformal_abort_threshold(scores_converged, alpha=0.05):
    """One-sided lower conformal threshold on P(converge), calibrated on CONVERGED runs' scores.
    Guarantee (exchangeability): for a new converged run, P(score < threshold) <= alpha.
    Returns -inf when n is too small to certify alpha (=> never abort at this alpha)."""
    s = np.sort(np.asarray(scores_converged, float))         # ascending
    n = len(s)
    k = int(np.floor(alpha * (n + 1)))                       # #calibration points allowed below
    if k < 1:
        return -np.inf                                       # cannot certify alpha with this n
    return float(s[k - 1])                                   # abort iff score < this (strict)


class ConformalAbortPolicy:
    """Wraps a frozen model (predict_proba, positive class = converge) + a conformal abort threshold.
    Actions: 'abort' (confidently doomed), 'continue' (default / abstain — keep running, advisory)."""

    def __init__(self, model, alpha=0.05, positive_index=1):
        self.model = model
        self.alpha = alpha
        self.pos = positive_index
        self.threshold = -np.inf
        self.n_calib = 0

    def p_converge(self, X):
        return np.asarray(self.model.predict_proba(X))[:, self.pos]

    def calibrate(self, X_cal, y_cal):
        """Calibrate on a campaign's history; only the CONVERGED (y==1) runs set the threshold."""
        y_cal = np.asarray(y_cal, int)
        pos_scores = self.p_converge(np.asarray(X_cal, float))[y_cal == 1]
        self.n_calib = int((y_cal == 1).sum())
        self.threshold = conformal_abort_threshold(pos_scores, self.alpha)
        return self.threshold

    def calibrate_from_scores(self, scores, y):
        """Calibrate from PRECOMPUTED scores (e.g. OOF seed scores — the honest, non-in-sample source)."""
        scores, y = np.asarray(scores, float), np.asarray(y, int)
        self.n_calib = int((y == 1).sum())
        self.threshold = conformal_abort_threshold(scores[y == 1], self.alpha)
        return self.threshold

    def decide(self, X):
        """Per-row action list. abort iff P(converge) < threshold; else continue (advisory/abstain)."""
        p = self.p_converge(np.atleast_2d(np.asarray(X, float)))
        return ["abort" if pi < self.threshold else "continue" for pi in p], p

    def certifiable(self):
        return np.isfinite(self.threshold)


def flat_starter_stratum(x):
    """Mondrian stratum from the feature vector: the 'flat & high-RMS early' staged-mixing group vs the
    rest. Derived from logrms_min (idx 4) and logrms_slope (idx 6) — matches the trajectory-level
    definition (all rms[:T] >= 8e-3 AND near-flat log-slope). Returns 'flat' or 'other'."""
    logrms_min, logrms_slope = float(x[4]), float(x[6])
    return "flat" if (logrms_min >= np.log10(8e-3) and abs(logrms_slope) < 0.05) else "other"


class MondrianConformalAbortPolicy:
    """Group-conditional (Mondrian) conformal abort — one threshold PER STRATUM, so the false-abort
    guarantee holds CONDITIONALLY. A marginal threshold under-protects strata whose converging runs sit
    near the boundary (flat-starters: measured false-abort 0.086 vs alpha 0.05); per-stratum thresholds
    restore it (0.047). Reviewer Issue 1 fix."""

    def __init__(self, model, alpha=0.05, strata_fn=flat_starter_stratum, positive_index=1):
        self.model = model; self.alpha = alpha; self.strata_fn = strata_fn; self.pos = positive_index
        self.thresholds = {}; self.n_calib = {}

    def p_converge(self, X):
        return np.asarray(self.model.predict_proba(X))[:, self.pos]

    def calibrate(self, X_cal, y_cal):
        X_cal = np.asarray(X_cal, float); y_cal = np.asarray(y_cal, int)
        strata = np.array([self.strata_fn(x) for x in X_cal])
        p = self.p_converge(X_cal)
        for s in np.unique(strata):
            m = (strata == s) & (y_cal == 1)
            self.thresholds[s] = conformal_abort_threshold(p[m], self.alpha)
            self.n_calib[s] = int(m.sum())
        return self.thresholds

    def calibrate_from_scores(self, scores, y, strata):
        """Calibrate per-stratum thresholds from PRECOMPUTED (OOF seed) scores + strata labels — the
        honest, non-in-sample calibration source used for material-matched campaign seeding."""
        scores, y, strata = np.asarray(scores, float), np.asarray(y, int), np.asarray(strata)
        for s in np.unique(strata):
            m = (strata == s) & (y == 1)
            self.thresholds[s] = conformal_abort_threshold(scores[m], self.alpha)
            self.n_calib[s] = int(m.sum())
        return self.thresholds

    def threshold_for(self, x):
        return self.thresholds.get(self.strata_fn(x), -np.inf)

    def certifiable_for(self, x):
        """PER-STRATUM certifiability: this run's stratum can abort iff its threshold is finite. A
        non-certifiable stratum (too few calibration points -> -inf threshold) is advisory-only; other
        strata still abort. (Replaces the all-or-nothing global gate for deployment decisions.)"""
        return bool(np.isfinite(self.threshold_for(x)))

    def decide(self, X):
        X = np.atleast_2d(np.asarray(X, float)); p = self.p_converge(X)
        acts = ["abort" if pi < self.threshold_for(x) else "continue" for x, pi in zip(X, p)]
        return acts, p

    def certifiable(self):
        return bool(self.thresholds) and all(np.isfinite(t) for t in self.thresholds.values())


def evaluate_policy(policy, X_test, y_test):
    """Shadow-replay metrics for gate G1: empirical false-abort rate (should be <= ~alpha),
    failure-recall (doomed runs caught), and abort precision. y=1 converged, y=0 doomed."""
    y = np.asarray(y_test, int)
    acts, p = policy.decide(X_test)
    abort = np.array([a == "abort" for a in acts])
    conv, doom = (y == 1), (y == 0)
    false_abort = float((abort & conv).sum() / max(conv.sum(), 1))      # aborted a would-converge run
    recall = float((abort & doom).sum() / max(doom.sum(), 1))           # of doomed, fraction caught
    precision = float((abort & doom).sum() / max(abort.sum(), 1)) if abort.any() else float("nan")
    return {"threshold": policy.threshold, "n_calib_pos": policy.n_calib, "alpha": policy.alpha,
            "false_abort_rate": false_abort, "failure_recall": recall, "abort_precision": precision,
            "n_abort": int(abort.sum()), "n_test": len(y), "certifiable": policy.certifiable()}
