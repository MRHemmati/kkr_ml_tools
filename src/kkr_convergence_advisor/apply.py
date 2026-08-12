"""ADV-3 apply helper (source-only, pure python). Applies ONLY explicitly-selected safe tips to a COPY of a
builder representation (a plain dict). Never mutates stored AiiDA nodes. Default advisory-only."""
import copy


def apply_selected(builder_repr, tips, apply_selected=None, certified_donor_segs=None):
    """
    builder_repr : plain dict, e.g. {"wf_parameters": {...}, "options": {...}, "startpot_overwrite_source_seg": None}
                   (a REPRESENTATION of a builder, NOT a live AiiDA builder — this helper never touches AiiDA).
    tips         : list of tip dicts (from the engine).
    apply_selected : list of tip_ids to apply. Default None/[] -> nothing changes.
    certified_donor_segs : set of E1-CERTIFIED source segment pks (for donor safety).
    Returns (new_builder_repr, record) where record = {"applied": [...], "rejected": [{tip_id, reason}]}.
    """
    new = copy.deepcopy(builder_repr) if builder_repr else {}
    record = {"applied": [], "rejected": []}
    selected = list(apply_selected or [])
    if not selected:
        return new, record                                  # advisory-only default: change nothing
    certified = set(certified_donor_segs or set())
    by_id = {t["tip_id"]: t for t in tips}

    for tid in selected:
        t = by_id.get(tid)
        if t is None:
            record["rejected"].append({"tip_id": tid, "reason": "unknown tip_id"}); continue
        ttype = t.get("type")
        # --- hard safety gates ---
        if ttype in ("unsafe_warning", "risk_warning"):
            record["rejected"].append({"tip_id": tid, "reason": f"{ttype} is not machine-applicable (advisory)"}); continue
        rec = t.get("recommendation") or {}
        if ttype == "donor_start":
            seg = rec.get("startpot_overwrite_source_seg")
            if rec.get("certification") != "E1_CERTIFIED" or seg not in certified:
                record["rejected"].append({"tip_id": tid, "reason": "donor not E1-CERTIFIED (refuse to apply)"}); continue
            new["startpot_overwrite_source_seg"] = seg
            new.setdefault("wf_parameters", {}).update(rec.get("wf_parameters") or {})
            record["applied"].append({"tip_id": tid, "type": ttype, "set": {"startpot_overwrite_source_seg": seg}})
            continue
        # generic machine-applicable payloads: wf_parameters / options only
        applied_fields = {}
        for key in ("wf_parameters", "options"):
            if isinstance(rec.get(key), dict):
                new.setdefault(key, {}).update(rec[key]); applied_fields[key] = rec[key]
        if applied_fields:
            record["applied"].append({"tip_id": tid, "type": ttype, "set": applied_fields})
        else:
            record["rejected"].append({"tip_id": tid, "reason": "no machine-applicable payload"})
    return new, record
