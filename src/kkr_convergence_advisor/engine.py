"""ADV-2 engine: retrieval/rule-based Convergence Advisor (NOT a deep model). Emits ranked, provenance-backed
tips with mandatory fields + hard safety. Advisory by default; never auto-applies."""
import json, statistics
from collections import Counter
from . import core
from .schema import TIP_REQUIRED_FIELDS

PER_ITER_SECONDS = {"th1": 340, "oscar": 340, "viti": 200, "th1-2020-64": 41, "th1-2020-32": 60}


def _divisors(n):
    return [i for i in range(1, n + 1) if n % i == 0]


def grid_valid_ranks(contour_npts, max_cores=12):
    """Ranks must divide EVERY contour's energy-point count."""
    if not contour_npts:
        return list(range(1, max_cores + 1))
    common = set(_divisors(contour_npts[0]))
    for n in contour_npts[1:]:
        common &= set(_divisors(n))
    return sorted(r for r in common if r <= max_cores)


class ConvergenceAdvisor:
    def __init__(self, index, index_sha256=None):
        """index: dict (advisor_index_v1) or path to advisor_index.json. index_sha256: optional override
        (else read from a sibling advisor_index_manifest.json, else fall back to the index version)."""
        import os
        sha = index_sha256
        if isinstance(index, str):
            if sha is None:
                mf = os.path.join(os.path.dirname(index), "advisor_index_manifest.json")
                if os.path.exists(mf):
                    try: sha = json.load(open(mf)).get("sha256")
                    except Exception: sha = None
            index = json.load(open(index))
        self.index = index
        self.runs = index.get("runs", [])
        self.donors = index.get("donors", [])
        self.index_sha256 = sha or index.get("sha256") or index.get("version", "unknown")

    # -- helpers --
    def _base(self, ttype, level, n, conf, rec, reason, caveats, applies_to):
        return dict(type=ttype, evidence_level=level, n_supporting_runs=int(n), confidence=float(conf),
                    recommendation=rec, reason=reason, caveats=list(caveats), applies_to=applies_to,
                    index_sha256=self.index_sha256,
                    tip_id=f"{ttype}__{applies_to.get('formula','?')}__{applies_to.get('compat_class','?')}__{level}")

    def _certified_donors_for(self, fp):
        """E1 CERTIFIED donors that exactly match the target's z-sequence + compat (Level A only)."""
        out = []
        for d in self.donors:
            if d.get("certification") != "E1_CERTIFIED":
                continue
            try:
                z = tuple(json.loads(d.get("z_sequence") or "[]"))
            except Exception:
                z = ()
            same_compat = (str(d.get("code_family")) == str(fp.get("code_family"))
                           and str(d.get("nspin")) == str(fp.get("nspin"))
                           and str(d.get("lmax")) == str(fp.get("lmax"))
                           and str(d.get("soc")) == str(fp.get("soc")))
            if z and z == fp.get("z_sequence") and same_compat:
                out.append(d)
        return out

    # -- main --
    def advise(self, target):
        fp = core.fingerprint(target)
        buckets = core.bucket_runs(fp, self.runs)
        tips = []

        # ---- SAFETY: CPA / BdG / non-normal target -> warnings only ----
        if fp.get("cpa") or (target.get("regime") and target.get("regime") != "normal"):
            tips.append(self._base(
                "unsafe_warning", "A", 0, 0.9, {},
                "Target is CPA/doped or BdG regime: v1 emits NO certified donor/mixing advice for this regime "
                "(CPA sites have no certifiable block->site mapping; BdG uses a different contour/mesh regime).",
                ["No safe donor/mixing tip in v1 for CPA/BdG.", "Use standard normal-state runs for advice."],
                {"formula": fp["formula"], "compat_class": fp["compat_class"], "regime": target.get("regime", "cpa")}))
            # still allow generic ranks tip (deterministic) below, but no donor/mixing.
            return self._finalize(self._add_ranks_partition(fp, tips))

        # best evidence level with any supporting runs
        best = next((lv for lv in ("A", "B", "C", "D") if buckets[lv]), None)

        # ---- donor_start (Level A, CERTIFIED only) ----
        donors = self._certified_donors_for(fp)
        if donors and not fp.get("cpa"):
            a_runs = buckets["A"]
            st = core.outcome_stats(a_runs)
            conf = core.confidence("A", len(donors), consistency=(st["success_rate"] or 0.7))
            heldout = [d for d in donors if str(d.get("in_train")) == "False"]
            pick = (heldout or donors)[0]
            tips.append(self._base(
                "donor_start", "A", len(donors), conf,
                {"startpot_overwrite_source_seg": pick["source_seg"], "certification": "E1_CERTIFIED",
                 "wf_parameters": {"coarse_preconvergence": True}},
                f"Level A: {len(donors)} E1-CERTIFIED same-structure donor(s) available; "
                f"{st['n_converged']}/{st['n']} same-structure runs converged historically "
                f"(median {st['median_iters']} iters). A certified warm start can cut cold iterations "
                f"substantially (historical median ~194 saved), but this is NOT guaranteed.",
                ["same structure != guaranteed same basin (check final energy/moment)",
                 "warm-start is not always faster (observed ~1/9 slower)",
                 "advisory only; apply only via apply_selected"],
                {"formula": fp["formula"], "compat_class": fp["compat_class"]}))

        # ---- mixing tip (from converged runs at best level) ----
        if best:
            conv = [r for r in buckets[best] if r.get("outcome") == "converged"
                    and isinstance(r.get("strmix"), (int, float))]
            if conv:
                sm = statistics.median([r["strmix"] for r in conv])
                bm_vals = [r["brymix"] for r in conv if isinstance(r.get("brymix"), (int, float))]
                bm = statistics.median(bm_vals) if bm_vals else None
                st = core.outcome_stats(buckets[best])
                conf = core.confidence(best, st["n"], consistency=(st["success_rate"] or 0.5))
                tips.append(self._base(
                    "mixing", best, len(conv), conf,
                    {"wf_parameters": {"strmix": round(sm, 4), **({"brymix": round(bm, 4)} if bm else {})}},
                    f"Level {best}: {len(conv)} converged run(s) used median STRMIX={round(sm,4)}"
                    + (f", BRYMIX={round(bm,4)}" if bm else "") + ". "
                    + ("Transfer hint only (cross-formula/material)." if core.is_transfer_hint(best) else ""),
                    (["low-confidence transfer hint"] if core.is_transfer_hint(best) else [])
                    + ["advisory only"],
                    {"formula": fp["formula"], "compat_class": fp["compat_class"]}))

        # ---- contour tip: keep coarse_preconvergence=True ----
        planned = fp.get("planned", {})
        if planned.get("coarse_preconvergence") is False:
            # evidence: cold runs with coarse pre-convergence converged; fine-only cold failed (E3c-b)
            n_cold_ok = sum(1 for r in buckets.get(best or "D", [])
                            if r.get("start_type") == "cold" and r.get("outcome") == "converged")
            tips.append(self._base(
                "contour", best or "D", n_cold_ok, core.confidence(best or "D", max(n_cold_ok, 3), 0.9),
                {"wf_parameters": {"coarse_preconvergence": True}},
                "Planned coarse_preconvergence=False: fine-only cold starts failed to converge in budget in "
                "prior tests (E3c-b: 5/5 censored). Keep coarse_preconvergence=True so the cold start reaches "
                "the basin cheaply before the fine contour.",
                ["applies to COLD starts; warm/donor starts may skip coarse", "advisory only"],
                {"formula": fp["formula"], "compat_class": fp["compat_class"]}))

        # ---- budget tip: walltime / kkr_runmax / nsteps ----
        if best:
            st = core.outcome_stats(buckets[best])
            if st["median_iters"]:
                part = planned.get("partition", "th1")
                spi = PER_ITER_SECONDS.get(part, 340)
                # cold needs the full median; warm ~ a fraction
                est_iters = st["median_iters"]
                walltime = int(min(est_iters * spi * 1.3, 10 * 3600))
                tips.append(self._base(
                    "budget", best, st["n"], core.confidence(best, st["n"], st["success_rate"] or 0.5),
                    {"options": {"max_wallclock_seconds": walltime},
                     "wf_parameters": {"kkr_runmax": 3, "nsteps": 100}},
                    f"Level {best}: median {est_iters} iters-to-converge; at ~{spi}s/iter on {part}, allow "
                    f"~{walltime}s walltime and kkr_runmax>=3 so the run isn't censored mid-convergence.",
                    ["per-iter time is partition-dependent", "advisory only"],
                    {"formula": fp["formula"], "compat_class": fp["compat_class"]}))

        # ---- ranks / partition ----
        tips = self._add_ranks_partition(fp, tips)

        # ---- risk warning: aggressive mixing / fine-only cold ----
        if isinstance(planned.get("strmix"), (int, float)) and planned["strmix"] >= 0.1:
            tips.append(self._base(
                "risk_warning", best or "D", 0, 0.6,
                {"suggested": {"strmix": 0.03}},
                f"Planned STRMIX={planned['strmix']} is aggressive; large straight-mixing historically caused "
                "oscillation/NaN-divergence on these cells. Prefer STRMIX ~ 0.01-0.03.",
                ["heuristic warning", "advisory only"],
                {"formula": fp["formula"], "compat_class": fp["compat_class"]}))

        return self._finalize(tips)

    def _add_ranks_partition(self, fp, tips):
        planned = fp.get("planned", {})
        contour = list(fp.get("contour_npts") or (24, 48))
        valid = grid_valid_ranks(contour, max_cores=12)
        planned_ranks = planned.get("ranks")
        bad = planned_ranks is not None and (planned_ranks not in valid)
        rec_ranks = 12 if 12 in valid else (max(valid) if valid else 1)
        tips.append(self._base(
            "ranks_partition", "A", 0, 0.99 if bad else 0.8,
            {"options": {"tot_num_mpiprocs": rec_ranks,
                         "queue_name": planned.get("partition") or "th1"}},
            (f"Planned ranks={planned_ranks} do NOT divide all contour points {contour}; "
             if bad else "") +
            f"Grid-valid ranks (divide {contour}) = {valid}; use {rec_ranks} on th1/viti (Intel). "
            "Avoid EPYC th1-2020-* for normal-state to preserve quota.",
            ["ranks must divide every contour's energy-point count", "advisory only"],
            {"formula": fp["formula"], "compat_class": fp["compat_class"]}))
        return tips

    def _finalize(self, tips):
        # ensure mandatory fields, then rank: warnings first (safety), then by confidence
        for t in tips:
            for f in TIP_REQUIRED_FIELDS:
                t.setdefault(f, None)
        order = {"unsafe_warning": 0, "risk_warning": 1}
        tips.sort(key=lambda t: (order.get(t["type"], 2), -(t["confidence"] or 0)))
        return tips
