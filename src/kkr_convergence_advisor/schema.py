"""ADV: advisor-tip schema + validator (pure python, no dependencies)."""

TIP_TYPES = ("donor_start", "mixing", "contour", "budget", "ranks_partition",
             "risk_warning", "unsafe_warning")
EVIDENCE_LEVELS = ("A", "B", "C", "D")

# Mandatory fields on every emitted tip.
TIP_REQUIRED_FIELDS = ("tip_id", "type", "evidence_level", "n_supporting_runs", "confidence",
                       "recommendation", "reason", "caveats", "applies_to", "index_sha256")

TIP_SCHEMA = {
    "type": "object",
    "required": list(TIP_REQUIRED_FIELDS),
    "properties": {
        "tip_id": {"type": "string"},
        "type": {"enum": list(TIP_TYPES)},
        "evidence_level": {"enum": list(EVIDENCE_LEVELS)},
        "n_supporting_runs": {"type": "integer", "minimum": 0},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "recommendation": {"type": "object"},      # machine-applicable payload (may be empty for warnings)
        "reason": {"type": "string"},
        "caveats": {"type": "array"},
        "applies_to": {"type": "object"},
        "index_sha256": {"type": "string"},
    },
}


def validate_tip(tip):
    """Return (ok, errors[]). Minimal, dependency-free JSON-schema-style validation."""
    errs = []
    if not isinstance(tip, dict):
        return False, ["tip is not an object"]
    for f in TIP_REQUIRED_FIELDS:
        if f not in tip:
            errs.append(f"missing required field: {f}")
    if tip.get("type") not in TIP_TYPES:
        errs.append(f"invalid type: {tip.get('type')}")
    if tip.get("evidence_level") not in EVIDENCE_LEVELS:
        errs.append(f"invalid evidence_level: {tip.get('evidence_level')}")
    c = tip.get("confidence")
    if not (isinstance(c, (int, float)) and 0.0 <= c <= 1.0):
        errs.append(f"confidence out of range: {c}")
    n = tip.get("n_supporting_runs")
    if not (isinstance(n, int) and n >= 0):
        errs.append(f"n_supporting_runs invalid: {n}")
    if not isinstance(tip.get("recommendation", {}), dict):
        errs.append("recommendation must be an object")
    if not isinstance(tip.get("caveats", []), list):
        errs.append("caveats must be an array")
    if not isinstance(tip.get("applies_to", {}), dict):
        errs.append("applies_to must be an object")
    return (len(errs) == 0), errs
