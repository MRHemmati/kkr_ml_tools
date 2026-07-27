"""ADV-5 tests for the KKR Convergence Advisor (pure python; no AiiDA). Run with pytest or directly."""
import os, sys, json
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC)
import kkr_convergence_advisor as adv
from kkr_convergence_advisor import ConvergenceAdvisor, apply_selected, validate_tip, label_outcome, grid_valid_ranks

# ---- synthetic deterministic index fixture ----
NB_Z = [41, 41, 34, 34, 34, 34, 0, 0]          # Nb2Se4X2 (Z-sequence)
COMPAT = dict(code_family="standard", nspin=2, soc=False, cpa=False, lmax=2, ncheb=None)
def run(**kw):
    r = dict(regime="normal", formula="Nb2Se4X2", family="NbSe2", z_sequence=NB_Z, outcome="converged",
             iters_to_converge=190, strmix=0.02, brymix=0.03, start_type="cold", **COMPAT); r.update(kw); return r
FIX = {
    "version": "test", "sha256": "TESTSHA",
    "runs": [run() for _ in range(6)] + [run(outcome="stall", iters_to_converge=None),
                                         run(formula="Bi4X4", family="Bi", z_sequence=[83,83,83,83,0,0,0,0])],
    "donors": [dict(certification="E1_CERTIFIED", source_seg=110573, formula="Nb2Se4X2",
                    z_sequence=json.dumps(NB_Z), code_family="standard", nspin="2", lmax="2", soc="False",
                    raw_sha256="abc", in_train="False")],
}
TARGET = dict(formula="Nb2Se4X2", z_sequence=NB_Z, contour_npts=[24, 48], regime="normal", **COMPAT)


def _adv(): return ConvergenceAdvisor(FIX)

def test_1_exact_structure_levelA():
    tips = _adv().advise(TARGET)
    assert any(t["evidence_level"] == "A" for t in tips), "expected a Level A tip for exact structure"

def test_2_certified_donor_produces_donor_start():
    tips = _adv().advise(TARGET)
    d = [t for t in tips if t["type"] == "donor_start"]
    assert d and d[0]["recommendation"]["certification"] == "E1_CERTIFIED"
    assert d[0]["recommendation"]["startpot_overwrite_source_seg"] == 110573

def test_3_cpa_target_only_unsafe_warning():
    cpa_target = dict(TARGET); cpa_target["cpa"] = True
    tips = _adv().advise(cpa_target)
    assert any(t["type"] == "unsafe_warning" for t in tips)
    assert not any(t["type"] in ("donor_start", "mixing") for t in tips), "no safe advice for CPA in v1"

def test_3b_uncertified_donor_not_applied():
    # a donor tip with a non-certified seg must be rejected by apply
    tips = _adv().advise(TARGET)
    d = [t for t in tips if t["type"] == "donor_start"][0]
    _, rec = apply_selected({}, tips, [d["tip_id"]], certified_donor_segs=set())  # empty certified set
    assert any(x["reason"].startswith("donor not E1-CERTIFIED") for x in rec["rejected"])

def test_4_no_change_when_apply_selected_empty():
    tips = _adv().advise(TARGET)
    b0 = {"wf_parameters": {"strmix": 0.5}, "options": {"queue_name": "th1"}}
    new, rec = apply_selected(b0, tips, [])
    assert new == b0 and rec["applied"] == []

def test_5_selected_tip_modifies_only_copy():
    tips = _adv().advise(TARGET)
    mix = [t for t in tips if t["type"] == "mixing"][0]
    b0 = {"wf_parameters": {"strmix": 0.5}}
    new, rec = apply_selected(b0, tips, [mix["tip_id"]])
    assert b0["wf_parameters"]["strmix"] == 0.5, "original builder must not be mutated"
    assert new["wf_parameters"]["strmix"] != 0.5 and rec["applied"], "copy should be updated"

def test_6_levelC_low_confidence_transfer_caveat():
    # target of a DIFFERENT formula but same family+compat -> only Level C support
    tgt = dict(formula="Nb2Se4X10", z_sequence=[41,41,34,34,34,34,34,34,34,34,0,0], contour_npts=[24,48],
               regime="normal", **COMPAT)
    tips = _adv().advise(tgt)
    cds = [t for t in tips if t["evidence_level"] in ("C", "D") and t["type"] == "mixing"]
    if cds:
        assert cds[0]["confidence"] <= 0.5
        assert any("transfer" in c.lower() for c in cds[0]["caveats"])

def test_7_per_qbound_label():
    # final_rms 0.005 with own QBOUND 0.008 -> converged (NOT stall by fixed 1e-3)
    assert label_outcome(0.005, 0.008) == "converged"
    assert label_outcome(0.005, 1e-3) == "stall"          # fixed cut would mislabel
    assert label_outcome(0.5, 0.008) == "diverge"
    assert label_outcome(None, 0.008) == "no-traj"
    assert label_outcome(0.005, 0.008, excepted=True) == "censored"

def test_8_contour_tip_for_nbse2():
    tgt = dict(TARGET); tgt["planned"] = {"coarse_preconvergence": False}
    tips = _adv().advise(tgt)
    assert any(t["type"] == "contour" and t["recommendation"]["wf_parameters"]["coarse_preconvergence"] is True
               for t in tips)

def test_9_grid_valid_ranks_12():
    assert grid_valid_ranks([24, 48], max_cores=12) == [1, 2, 3, 4, 6, 8, 12]
    tips = _adv().advise(dict(TARGET, planned={"ranks": 20}))
    rp = [t for t in tips if t["type"] == "ranks_partition"][0]
    assert rp["recommendation"]["options"]["tot_num_mpiprocs"] == 12

def test_10_schema_validates_all_tips():
    for tgt in (TARGET, dict(TARGET, cpa=True), dict(TARGET, planned={"strmix": 0.2, "ranks": 20})):
        for t in _adv().advise(tgt):
            ok, errs = validate_tip(t)
            assert ok, f"tip failed schema: {errs} :: {t.get('type')}"


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}"); passed += 1
        except Exception:
            print(f"FAIL {fn.__name__}"); traceback.print_exc()
    print(f"\n{passed}/{len(fns)} passed")
