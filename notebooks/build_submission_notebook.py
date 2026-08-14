"""Build notebooks/aiida_kkr_mlassist_submission_walkthrough.ipynb (beginner-friendly).
Safe-by-default: NO cell submits unless the user flips explicit boolean gates. AiiDA cells auto-skip when
AiiDA is unavailable OR when env POTBANK_NB_NO_AIIDA=1 (used for offline verification -> no DB touch)."""
import nbformat as nbf
import os
nb = nbf.v4.new_notebook(); C = []
def md(s): C.append(nbf.v4.new_markdown_cell(s))
def code(s): C.append(nbf.v4.new_code_cell(s))

# ---- 1. Title + safety banner ----
md("""# Using `aiida-kkr-mlassist` and PotentialBank v1: from advisor tips to KKR submissions

**What this notebook does** — it walks you through, step by step:
1. loading **AiiDA** (the workflow/database system),
2. checking your **KKR** and **Voronoi** codes,
3. inspecting available **crystal structures**,
4. loading the **PotentialBank advisor** (optional convergence tips),
5. building **cold** and **warm-start** KKR workflow "builders",
6. **optionally** submitting a few jobs to the cluster,
7. monitoring and reading results.

> ## ⚠️ SAFETY BANNER — read this first
> - **By default this notebook does NOT submit anything.** You can run every cell top to bottom safely; it only
>   *prepares* jobs and *prints plans*.
> - **Submitting consumes real HPC (cluster) resources.** Nothing is sent to the cluster unless **you** edit one
>   cell and set `I_UNDERSTAND_THIS_WILL_SUBMIT_TO_HPC = True`.
> - **Abort mode** (letting a model stop a running calculation) is **off by default** and needs a *second*
>   explicit switch. Beginners should leave it off (advisory-only).
> - The read-only parts (advisor, PotentialBank) work **even without AiiDA**.

**Scope (kept throughout):** PotentialBank v1 = certified **same-structure** donor reuse. **No cross-material
transfer. No guaranteed acceleration. CPA/BdG are out of scope** for this tutorial.""")

# ---- 2. How to use ----
md("""## 2. How to use this notebook (for beginners)

- A notebook is a list of **cells**. A cell is a small box of text or code.
- To **run** a cell: click it, then press **Shift + Enter**. The result appears **just below** the cell.
- Run cells **in order, top to bottom** (some cells use results from earlier ones).
- You will edit **one configuration cell** (Section 4) — change the values on the right of the `=` signs.
- **If a cell shows a red error:** don't panic. Read the last line — it usually says what is missing (e.g. a
  code label or a structure number). Fix the configuration cell and re-run. Errors do **not** submit anything.
- Nothing here is destructive until the very last section, and only if you flip the safety switch.""")

# ---- 3. Imports + safe mode ----
md("""## 3. Imports and safe mode

We import gently. If AiiDA is not installed/configured, the notebook **does not crash** — the read-only
advisor/PotentialBank parts still work; only the submission parts need AiiDA.""")
code('''import os, json
from pathlib import Path

# These three switches are your safety gates. Leave them as-is for a safe, no-submit run.
DRY_RUN = True                                        # True = prepare & print only, never submit
I_UNDERSTAND_THIS_WILL_SUBMIT_TO_HPC = False          # must be True to submit real jobs
I_UNDERSTAND_ABORT_MODE_CAN_STOP_CALCULATIONS = False # must ALSO be True to allow ml_assist abort mode

# Try to load AiiDA. (POTBANK_NB_NO_AIIDA=1 forces "offline" mode used for automated testing.)
AIIDA_AVAILABLE = False
_aiida_msg = ""
try:
    if os.environ.get("POTBANK_NB_NO_AIIDA") == "1":
        raise ImportError("AiiDA disabled for offline verification (POTBANK_NB_NO_AIIDA=1)")
    import aiida
    from aiida import orm
    from aiida.engine import submit
    from aiida.plugins import WorkflowFactory
    AIIDA_AVAILABLE = True
    print("AiiDA imported OK — version", aiida.__version__)
except Exception as e:
    _aiida_msg = str(e)
    print("AiiDA not available in this session:\\n  ", _aiida_msg)
    print("  -> The advisor / PotentialBank cells still work. Submission cells will be skipped.")

# The advisor package is pure-Python (no AiiDA needed).
try:
    import kkr_convergence_advisor as advisor_pkg
    ADVISOR_PKG = True
    print("kkr_convergence_advisor imported OK — version", advisor_pkg.__version__)
except Exception as e:
    ADVISOR_PKG = False
    print("kkr_convergence_advisor not importable here (we'll read its data files directly):", e)

# The workchain package (only needed to submit) — optional.
try:
    import aiida_kkr_mlassist
    MLASSIST_PKG = True
except Exception:
    MLASSIST_PKG = False
print("submit gates -> DRY_RUN:", DRY_RUN, "| submit allowed:", I_UNDERSTAND_THIS_WILL_SUBMIT_TO_HPC,
      "| abort allowed:", I_UNDERSTAND_ABORT_MODE_CAN_STOP_CALCULATIONS)''')

# ---- 4. Config cell ----
md("""## 4. Your configuration — **edit this cell**

Change the values to match your setup. Each is explained in the comment next to it. If you don't know your code
labels, run `verdi code list` in a terminal (Section 5 also shows how).""")
code('''AIIDA_PROFILE = "default"                 # your AiiDA profile name

KKR_CODE_LABEL     = "kkrhost_3.5_intel@iffslurm"   # the KKR host code (label@computer)
VORONOI_CODE_LABEL = "voronoi_3.5_intel@iffslurm"   # the Voronoi code (label@computer)

COMPUTER_HINT = "iffslurm"     # which computer you run on (informational)
PARTITION     = "th1"          # cluster queue/partition name
NUM_MACHINES  = 1              # nodes per job (keep 1 for tutorials)
NUM_MPIPROCS_PER_MACHINE = 12  # MPI ranks; 12 divides the 24/48-pt energy contours (a safe grid-valid choice)
WALLTIME_SECONDS = 3600        # max runtime per job segment (1 hour)

STRUCTURE_PK = None   # <-- put the pk (a number) of the StructureData you want to run
DONOR_PK     = None   # <-- optional: pk of a certified donor's KKR calculation (for warm-start). Leave None for cold.

print("config set. STRUCTURE_PK =", STRUCTURE_PK, "| DONOR_PK =", DONOR_PK)''')

# ---- 5. Load profile + verify env ----
md("""## 5. Load your AiiDA profile and check your codes

This connects to AiiDA (read-only here) and looks up your two codes. If a code is missing, the cell tells you
to run `verdi code list` to see the exact labels you have.""")
code('''def load_codes():
    """Load the AiiDA profile and return (kkr_code, voronoi_code) or (None, None) with guidance."""
    if not AIIDA_AVAILABLE:
        print("AiiDA not available -> skipping. (Read-only advisor cells below still work.)")
        return None, None
    from aiida import load_profile
    load_profile(AIIDA_PROFILE)
    print("profile loaded:", AIIDA_PROFILE)
    kkr = voro = None
    for label, name in [(KKR_CODE_LABEL, "KKR"), (VORONOI_CODE_LABEL, "Voronoi")]:
        try:
            c = orm.load_code(label)
            print(f"  {name} code OK: pk={c.pk} label={c.label} computer={c.computer.label}")
            if name == "KKR": kkr = c
            else: voro = c
        except Exception as e:
            print(f"  {name} code '{label}' NOT found. Run `verdi code list` to see your labels. ({e})")
    return kkr, voro

kkr_code, voronoi_code = load_codes()''')

# ---- 6. Structures ----
md("""## 6. Find or choose a crystal structure

A **`StructureData`** is a crystal (its atoms + unit cell) stored in AiiDA, identified by a number (**pk**). If
you set `STRUCTURE_PK` in Section 4, we load it. Otherwise we list a few recent structures so you can pick one.

*Concepts:* the **formula** is which atoms and how many (e.g. `MgO`); the number of **sites** is how many atoms
are in the unit cell.""")
code('''def describe_structure(structure):
    """Print a friendly one-line description of a StructureData."""
    f = structure.get_formula()
    n = len(structure.sites)
    kinds = ", ".join(sorted({s.kind_name for s in structure.sites}))
    print(f"  pk={structure.pk}  formula={f}  sites={n}  kinds=[{kinds}]  created={structure.ctime:%Y-%m-%d}")

def load_or_list_structures():
    if not AIIDA_AVAILABLE:
        print("AiiDA not available -> skipping structure lookup.")
        return None
    if STRUCTURE_PK is not None:
        s = orm.load_node(STRUCTURE_PK)
        print("Loaded your structure:"); describe_structure(s)
        return s
    print("STRUCTURE_PK is None -> listing a few recent StructureData nodes to choose from:")
    qb = orm.QueryBuilder().append(orm.StructureData, tag="s").order_by({"s": {"ctime": "desc"}})
    for (s,) in qb.limit(8).all():
        describe_structure(s)
    print("\\n-> copy one pk into STRUCTURE_PK (Section 4) and re-run.")
    return None

structure = load_or_list_structures()''')

# ---- 7. Advisor / PotentialBank ----
md("""## 7. Load PotentialBank v1 and the advisor (optional tips)

This part needs **no AiiDA**. The advisor reads the frozen PotentialBank v1 catalog and offers **optional**
suggestions (e.g. "there is a certified donor for this material — warm-starting saved ~X iterations"). It never
changes your workflow; you decide whether to use a tip.""")
code('''def find_repo_root(start=None):
    p = Path(start or Path.cwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / "src" / "kkr_convergence_advisor" / "data" / "advisor_index_v1.json").exists():
            return cand
    return None

ROOT = find_repo_root()
if ADVISOR_PKG:
    adv_idx  = advisor_pkg.load_index()
    adv_tips = advisor_pkg.load_index("advisor_example_tips_v1.json")
    print("advisor loaded from the installed package")
elif ROOT is not None:
    d = ROOT / "src" / "kkr_convergence_advisor" / "data"
    adv_idx  = json.load(open(d / "advisor_index_v1.json"))
    adv_tips = json.load(open(d / "advisor_example_tips_v1.json"))
    print("advisor loaded from repo data files")
else:
    adv_idx = adv_tips = None
    print("could not locate advisor data (run from inside the repo).")

if adv_idx:
    print("PotentialBank v1:", adv_idx["unique_sha_donors"], "unique certified donors /",
          adv_idx["certified_donor_nodes"], "nodes /", adv_idx["n_families"], "families /",
          sum(1 for m in adv_idx["materials"] if m["f2_eligible"]), "F2-eligible materials")''')

code('''def advise(material):
    """Return an optional, advisory-only tip string for a material (or a warning for parked cases)."""
    if not adv_idx:
        return "(advisor not loaded)"
    m = next((x for x in adv_idx["materials"] if x["material"] == material), None)
    if m is None:
        w = next((p for p in adv_idx["parked_warnings"] if p["material"] == material), None)
        return f"WARNING ({w['klass']}): {w['warning']}" if w else "no tip (material not in bank)"
    if m.get("f2_eligible") and m.get("warmstart"):
        ws = m["warmstart"]
        return (f"tip: a certified same-structure donor exists; warm-start measured {ws['warm']} vs "
                f"{ws['cold']} iters ({ws['pct']}). caveat: {ws['contour_caveat']}")
    return f"{m['n_unique_donors']} certified donor(s); advisory only."

for mat in ["MgO", "NaCl", "Si", "Ge", "TiSe2", "Fe", "WSe2", "MoS2"]:
    print(f"{mat:6s} -> {advise(mat)}")''')
md("""**Remember:** these tips are *optional*. The advisor does **not** force anything. The validated use is
**same-structure** donor reuse — a donor is only useful for re-running the *same* crystal it was converged on.""")

# ---- 8. Cold builder ----
md("""## 8. Prepare a **cold** KKR job (standard Voronoi start)

A "builder" is a filled-in form describing one job. Here we build a standard `kkr_scf_wc` (the KKR
self-consistency workflow) starting from a fresh Voronoi potential — the normal "cold" start. **We only build
and print it; we do not submit.**""")
code('''# energy-contour settings (coarse then fine); NUM_MPIPROCS should divide these point counts
BZ = [22, 22, 22]
def make_wf_parameters(convergence_criterion=1e-5):
    return {
        "coarse_preconvergence": True,          # converge cheaply first, then refine (robust default)
        "convergence_criterion": convergence_criterion,
        "nsteps": 100, "kkr_runmax": 3,
        "convergence_setting_coarse": {"n1": 3, "n2": 11, "n3": 3, "npol": 7, "kmesh": BZ, "tempr": 1000.0},
        "convergence_setting_fine":   {"n1": 7, "n2": 29, "n3": 7, "npol": 5, "kmesh": BZ, "tempr": 600.0},
    }

def make_options():
    return {"withmpi": True,
            "resources": {"num_machines": NUM_MACHINES, "tot_num_mpiprocs": NUM_MPIPROCS_PER_MACHINE},
            "queue_name": PARTITION, "max_wallclock_seconds": WALLTIME_SECONDS}

# conservative, beginner-safe physics: normal-state, non-CPA, NO SOC unless you opt in
ENABLE_SOC = False   # leave False for the tutorial
def make_calc_parameters():
    p = {"NSPIN": 1, "LMAX": 3, "RCLUSTZ": 2.3}   # RCLUSTZ may need tuning per cell (see parked cases)
    # (SOC would add NCHEB + <USE_CHEBYCHEV_SOLVER> and a log panel; left off here on purpose.)
    return p

def build_cold_builder(structure):
    """Fill a kkr.scf builder for a cold Voronoi start. Returns the builder (does NOT submit)."""
    if not (AIIDA_AVAILABLE and structure is not None and kkr_code and voronoi_code):
        print("cannot build (need AiiDA + structure + both codes). Skipping.")
        return None
    from aiida.orm import Dict
    KkrScf = WorkflowFactory("kkr.scf")
    b = KkrScf.get_builder()
    b.structure       = structure                       # which crystal
    b.kkr             = kkr_code                         # KKR host code
    b.voronoi         = voronoi_code                     # Voronoi (starting-potential) code
    b.calc_parameters = Dict(dict=make_calc_parameters())
    b.wf_parameters   = Dict(dict=make_wf_parameters())
    b.options         = Dict(dict=make_options())
    b.metadata.label  = f"tutorial_cold_{structure.get_formula()}_EXCLUDE"   # _EXCLUDE = tutorial job
    print("cold builder ready:  label:", b.metadata.label)
    print("  structure pk:", structure.pk, "| ranks:", NUM_MPIPROCS_PER_MACHINE, "| partition:", PARTITION)
    return b

cold_builder = build_cold_builder(structure)''')

# ---- 9. Warm-start builder ----
md("""## 9. Prepare a **warm-start** KKR job (reuse a certified donor)

A **donor potential** is a *converged* potential from a previous run of the **same structure**. Starting from
it (instead of a cold Voronoi guess) usually converges in a handful of iterations. **Certification matters**: we
only reuse potentials that passed E1 checks (byte-exact SHA match, exact atom mapping, non-CPA/BdG). We do
**not** certify new donors here — we reuse an existing one you point to with `DONOR_PK`.""")
code('''def build_warmstart_builder(structure, donor_pk):
    """Build a kkr.scf builder that injects a donor potential as the start (startpot_overwrite)."""
    if not (AIIDA_AVAILABLE and structure is not None and kkr_code and voronoi_code):
        print("cannot build (need AiiDA + structure + codes). Skipping."); return None
    if donor_pk is None:
        print("DONOR_PK is None -> no warm-start. (Set DONOR_PK to a converged same-structure KKR calc pk.)")
        return None
    import io, hashlib
    from aiida.orm import Dict, SinglefileData
    donor_calc = orm.load_node(donor_pk)               # a KkrCalculation that produced out_potential
    with donor_calc.outputs.retrieved.base.repository.open("out_potential", "rb") as f:
        donor_bytes = f.read()
    donor_sha = hashlib.sha256(donor_bytes).hexdigest()
    print("donor pk:", donor_pk, "| out_potential sha256:", donor_sha[:16], "…  bytes:", len(donor_bytes))
    startpot = SinglefileData(io.BytesIO(donor_bytes), filename="potential")   # verbatim bytes
    KkrScf = WorkflowFactory("kkr.scf")
    b = KkrScf.get_builder()
    b.structure        = structure
    b.kkr              = kkr_code
    b.voronoi          = voronoi_code
    b.calc_parameters  = Dict(dict=make_calc_parameters())
    b.wf_parameters    = Dict(dict=make_wf_parameters())
    b.options          = Dict(dict=make_options())
    b.startpot_overwrite = startpot                    # <-- the warm start
    b.metadata.label   = f"tutorial_warm_{structure.get_formula()}_EXCLUDE"
    print("warm-start builder ready: label:", b.metadata.label)
    return b

warm_builder = build_warmstart_builder(structure, DONOR_PK)''')
md("""> **How to pick a donor:** the donor must be a **converged run of the very same structure**. You can find
> one by pk (from your own runs), or consult the advisor (Section 7) to see if that material is F2-eligible in
> PotentialBank v1. The advisor lists donor SHA-256s and provenance references; it does not hand out raw
> potential files.""")

# ---- 10. Several jobs (table-driven) ----
md("""## 10. Prepare several jobs at once (a small plan table)

Beginners often want a few jobs: a cold baseline, a warm-start, maybe a second warm-start or an advisory
`ml_assist` run. We describe them as **rows in a table** (each row = one job) and build them in a loop. Then we
print a **submission plan** — with `will_submit = False` for everyone by default.""")
code('''# each dict is ONE job. Edit/extend as you like.
job_plan = [
    {"label": "cold_baseline",  "mode": "cold",             "donor_pk": None},
    {"label": "warm_donor1",    "mode": "warm",             "donor_pk": DONOR_PK},
    # {"label": "warm_donor2",  "mode": "warm",             "donor_pk": None},   # add a 2nd donor pk if you have one
    # {"label": "mlassist_adv", "mode": "mlassist_advisory", "donor_pk": None},  # advisory-only (Section 11)
]

def build_from_plan(plan):
    built = []
    for job in plan:
        if job["mode"] == "cold":
            b = build_cold_builder(structure)
        elif job["mode"] == "warm":
            b = build_warmstart_builder(structure, job["donor_pk"])
        else:
            b = None   # ml_assist handled in Section 11
        built.append({**job, "builder": b})
    return built

built_jobs = build_from_plan(job_plan)

# a clean, human-readable plan table
try:
    import pandas as pd
    rows = [{"label": j["label"], "mode": j["mode"],
             "structure_pk": (structure.pk if structure else None),
             "donor_pk": j["donor_pk"], "partition": PARTITION,
             "ranks": NUM_MPIPROCS_PER_MACHINE, "walltime_s": WALLTIME_SECONDS,
             "builder_ready": j["builder"] is not None, "will_submit": False} for j in built_jobs]
    plan_df = pd.DataFrame(rows); display(plan_df)
except Exception:
    for j in built_jobs:
        print(j["label"], j["mode"], "builder_ready=", j["builder"] is not None, "will_submit=False")''')

# ---- 11. ml_assist advisory ----
md("""## 11. Optional: an `ml_assist` **advisory** run (no aborting)

`ml_assist` can watch the first SCF iterations and score them. In **advisory** mode it only *records* the
signal — it never stops your run. **Abort mode** (actually stopping a doomed run) is a separate, expert feature
and is **off** unless you flip a second switch. Beginners: keep advisory.""")
code('''def build_mlassist_advisory_builder(structure):
    """Build an ml_assist workchain in ADVISORY mode (records signals, never aborts)."""
    if not AIIDA_AVAILABLE:
        print("AiiDA not available -> skipping ml_assist builder."); return None
    try:
        MLAssist = WorkflowFactory("kkr.mlassist")     # provided by aiida-kkr-mlassist
    except Exception as e:
        print("ml_assist workflow not installed (entry point 'kkr.mlassist' missing):", e)
        print("  -> that's fine; the cold/warm builders above do not need it."); return None
    if not (structure and kkr_code and voronoi_code):
        print("need structure + codes; skipping."); return None
    from aiida.orm import Dict
    b = MLAssist.get_builder()
    b.structure       = structure
    b.kkr             = kkr_code
    b.voronoi         = voronoi_code
    b.calc_parameters = Dict(dict=make_calc_parameters())
    b.wf_parameters   = Dict(dict=make_wf_parameters())
    b.options         = Dict(dict=make_options())
    # ADVISORY only: records model signal, does NOT abort.
    b.ml_assist       = Dict(dict={"enabled": True, "mode": "advisory", "alpha": 0.10})
    b.metadata.label  = f"tutorial_mlassist_advisory_{structure.get_formula()}_EXCLUDE"
    print("ml_assist ADVISORY builder ready (will NOT abort).")
    return b

# Abort mode is gated behind BOTH switches — off by default on purpose.
def build_mlassist_abort_builder(structure):
    if not (I_UNDERSTAND_ABORT_MODE_CAN_STOP_CALCULATIONS and I_UNDERSTAND_THIS_WILL_SUBMIT_TO_HPC):
        print("ABORT mode is disabled. To enable, set BOTH:")
        print("   I_UNDERSTAND_ABORT_MODE_CAN_STOP_CALCULATIONS = True")
        print("   I_UNDERSTAND_THIS_WILL_SUBMIT_TO_HPC = True")
        print("Beginners: leave abort OFF and use advisory mode.")
        return None
    print("(abort-mode builder would be constructed here for expert users)")
    return None

mlassist_builder = build_mlassist_advisory_builder(structure)
_ = build_mlassist_abort_builder(structure)''')

# ---- 12. Pre-flight ----
md("""## 12. Pre-flight checks (before any submission)

A quick PASS/FAIL checklist. If anything is FAIL, fix it in Section 4 and re-run. This cell submits nothing.""")
code('''def preflight():
    checks = []
    checks.append(("AiiDA profile available", AIIDA_AVAILABLE))
    checks.append(("KKR code loaded", bool(AIIDA_AVAILABLE and kkr_code)))
    checks.append(("Voronoi code loaded", bool(AIIDA_AVAILABLE and voronoi_code)))
    checks.append(("structure chosen", structure is not None))
    checks.append(("ranks divide 24 & 48 (grid-valid)", (24 % NUM_MPIPROCS_PER_MACHINE == 0 and
                                                          48 % NUM_MPIPROCS_PER_MACHINE == 0)))
    checks.append(("walltime > 0", WALLTIME_SECONDS > 0))
    donor_ok = (DONOR_PK is None) or (AIIDA_AVAILABLE and _node_exists(DONOR_PK))
    checks.append(("donor pk exists (if warm-start)", donor_ok))
    checks.append(("no SOC unless opted in", not ENABLE_SOC))
    checks.append(("tutorial labels marked _EXCLUDE", True))
    checks.append(("submit switch flipped ON", I_UNDERSTAND_THIS_WILL_SUBMIT_TO_HPC))
    width = max(len(n) for n, _ in checks)
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}]  {name}")
    ready = all(ok for n, ok in checks)
    print("\\nready to submit:", ready, "(and this is a DRY_RUN)" if DRY_RUN else "")
    return ready

def _node_exists(pk):
    try: orm.load_node(pk); return True
    except Exception: return False

preflight_ready = preflight()''')

# ---- 13. Submission ----
md("""## 13. ⛔ Submission cell — **disabled by default**

This is the only cell that can send jobs to the cluster. It refuses unless **both** `DRY_RUN = False` **and**
`I_UNDERSTAND_THIS_WILL_SUBMIT_TO_HPC = True`. Leave them as-is for a safe dry run.""")
code('''def maybe_submit(built_jobs, extra_builders=None):
    to_submit = [(j["label"], j["builder"]) for j in built_jobs if j.get("builder") is not None]
    for lbl, b in (extra_builders or []):
        if b is not None: to_submit.append((lbl, b))

    if DRY_RUN:
        print("DRY RUN — nothing submitted. Would submit:", [lbl for lbl, _ in to_submit] or "(nothing built)")
        return []
    if not I_UNDERSTAND_THIS_WILL_SUBMIT_TO_HPC:
        print("REFUSING to submit: set I_UNDERSTAND_THIS_WILL_SUBMIT_TO_HPC = True to proceed.")
        return []
    if not AIIDA_AVAILABLE:
        print("AiiDA not available -> cannot submit."); return []
    submitted = []
    for lbl, b in to_submit:
        node = submit(b)                      # <-- the real submission
        submitted.append((lbl, node.pk))
        print(f"submitted {lbl}: pk={node.pk}")
    return submitted

submitted = maybe_submit(built_jobs, extra_builders=[("mlassist_advisory", mlassist_builder)])
print("submitted pks:", submitted)''')

# ---- 14. Monitoring ----
md("""## 14. Monitoring your jobs (read-only)

After submitting, watch progress. In a terminal: **`verdi process list`** shows running jobs;
**`verdi process status <pk>`** shows the tree of a single job. In Python, the helper below summarizes one
workchain by pk. (We never kill jobs here.)

*Common statuses:* **Waiting** = queued/running on the cluster; **Finished** = done (check exit status!);
**Excepted** = hit an error; **Paused** = stuck on a transport hiccup (an admin/you can later resume it).""")
code('''def summarize_workchain(pk):
    """Print a friendly status summary of a workchain by pk (read-only)."""
    if not AIIDA_AVAILABLE:
        print("AiiDA not available -> cannot summarize."); return
    wc = orm.load_node(pk)
    print(f"pk {pk}: state={wc.process_state}  exit={wc.exit_status}  "
          f"sealed={wc.is_sealed}  paused={getattr(wc, 'paused', '?')}")
    kids = [d for d in wc.called_descendants
            if getattr(d, 'process_label', '') in ('VoronoiCalculation', 'KkrCalculation')]
    for c in sorted(kids, key=lambda x: x.ctime):
        print(f"   - {c.process_label} pk={c.pk} state={c.process_state} exit={c.exit_status}")

# Example (fill in a real pk you submitted):
# summarize_workchain(123456)
print("Tip: after submitting, call summarize_workchain(<pk>) with one of your submitted pks.")''')

# ---- 15. Reading results ----
md("""## 15. Reading results

When a workflow finishes, pull out the useful numbers. Not every run converges — that is normal and useful
information — so the helper handles missing pieces gracefully.""")
code('''def read_results(pk):
    """Extract convergence / rms / iterations / exit status from a finished KKR workchain (read-only)."""
    if not AIIDA_AVAILABLE:
        print("AiiDA not available -> cannot read results."); return
    import hashlib
    wc = orm.load_node(pk)
    kkr_calcs = sorted([d for d in wc.called_descendants
                        if getattr(d, 'process_label', '') == 'KkrCalculation'], key=lambda x: x.ctime)
    if not kkr_calcs:
        print(f"pk {pk}: no KKR calculation yet (still setting up, or failed early)."); return
    last = kkr_calcs[-1]
    try:
        out = last.outputs.output_parameters.get_dict()
        rms = (out.get("convergence_group", {}).get("rms_all_iterations") or [])
        print(f"pk {pk}: iterations={len(rms)}  final_rms={rms[-1] if rms else None}  "
              f"converged={bool(rms and rms[-1] < 1e-5)}  wc_exit={wc.exit_status}")
    except Exception:
        print(f"pk {pk}: no output_parameters yet (state={last.process_state}, exit={last.exit_status}).")
    try:
        names = last.outputs.retrieved.base.repository.list_object_names()
        if "out_potential" in names:
            with last.outputs.retrieved.base.repository.open("out_potential", "rb") as f:
                print("   out_potential sha256:", hashlib.sha256(f.read()).hexdigest()[:16], "…")
        else:
            print("   (no out_potential retrieved — run may be unconverged or was aborted/paused)")
    except Exception:
        print("   (retrieved files not available)")

# Example: read_results(123456)
print("Tip: call read_results(<pk>) once a job has finished.")''')
md("""**Friendly failure guide.** *Unconverged* → final rms didn't reach 1e-5 (try a donor warm start or gentler
mixing). *Paused* → a transport hiccup; the job may have finished on the cluster but needs resuming to retrieve.
*Missing retrieved* → nothing came back (often an early setup error). *Setup error* (e.g. NACLSD, R_LOG) → a
per-cell parameter needs tuning — see the parked hard cases in PotentialBank v1.""")

# ---- 16. Claims & limitations ----
md("""## 16. Claims and limitations (please keep these honest)

- This notebook helps you **prepare real KKR jobs** and, if you choose, submit them.
- **PotentialBank v1 supports certified *same-structure* donor reuse** — a donor accelerates re-running the
  *same* crystal it converged on.
- **Advisor tips are optional**; the workflow does not force them.
- **No cross-material transfer** is claimed (a donor for material A does not help material B).
- **No guaranteed acceleration** — savings depend on the structure, mixing, and contour; some cells are "parked"
  hard cases.
- **CPA/BdG are out of scope** for this PotentialBank v1 tutorial.
- For `ml_assist`: the early-abort **mechanism was validated live**, but **broad ML transfer was not proven**
  (it does not beat a simple RMS@10 baseline out-of-sample and does not transfer across materials) — deploy
  per-campaign, advisory-first.""")

# ---- 17. Final checklist ----
md("""## 17. Final checklist — what you learned

1. ✅ Load AiiDA and your profile.
2. ✅ Find your KKR and Voronoi **codes**.
3. ✅ Choose a **structure** (by pk).
4. ✅ Load the **advisor** and read optional PotentialBank tips.
5. ✅ Build a **cold** KKR builder.
6. ✅ Build a **warm-start** builder from a certified donor.
7. ✅ Lay out **several jobs** as a plan table (dry run).
8. ✅ (Optional) build an **advisory** `ml_assist` run — abort stays off.
9. ✅ Run **pre-flight** checks.
10. ✅ **Submit** only after flipping the safety switch — then **monitor** and **read results**.

You did all of this **without submitting anything** unless you explicitly chose to. That is the intended, safe
workflow. Happy computing! 🎉""")

nb["cells"] = C
nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                  "language_info": {"name": "python"}}
out = os.path.join(os.path.dirname(__file__), "aiida_kkr_mlassist_submission_walkthrough.ipynb")
nbf.write(nb, out)
print("wrote", out, "with", len(C), "cells")
