"""Build notebooks/potentialbank_v1_walkthrough.ipynb from packaged artifacts (offline).
No AiiDA / HPC / MP-API / raw potentials. All numbers read from the committed CSV/JSON artifacts."""
import nbformat as nbf
import os
nb = nbf.v4.new_notebook()
C = []
def md(s): C.append(nbf.v4.new_markdown_cell(s))
def code(s): C.append(nbf.v4.new_code_cell(s))

md("""# PotentialBank v1 — walkthrough

A runnable, **AiiDA-free** tour of the frozen **PotentialBank v1** artifact for reviewers/users opening this
repo. It uses only the committed/packaged artifacts (manifest, tables, advisor index) — **no** AiiDA DB, HPC,
daemon, raw potential files, or Materials Project API.

**Frozen headline (verified from artifacts in the next cells):**
- **237 unique certified donors** / **238 certified nodes** (1 recorded historical byte-duplicate);
- **8 families**;
- **33 F2-eligible materials** (≥2 independent certified donors).

**Scope (kept throughout):** certified *same-structure* donor reuse only — **no cross-material transfer**, **no
guaranteed acceleration**; CPA/BdG are out of scope for PotentialBank v1.""")

code('''import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def find_repo_root(start=None):
    p = Path(start or Path.cwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / "reports" / "potentialbank_v1" / "potentialbank_v1_summary.json").exists():
            return cand
    raise FileNotFoundError("repo root not found (run from repo root or notebooks/)")

ROOT = find_repo_root()
PB   = ROOT / "reports" / "potentialbank_v1"
ADV  = ROOT / "src" / "kkr_convergence_advisor" / "data"
print("repo root:", ROOT)
print("bundle   :", PB.relative_to(ROOT))
print("advisor  :", ADV.relative_to(ROOT))''')

md("## 2. Load the packaged artifacts")
code('''manifest = pd.read_csv(PB / "potentialbank_v1_manifest.csv")
summary  = json.load(open(PB / "potentialbank_v1_summary.json"))
cov_fam  = pd.read_csv(PB / "tables" / "coverage_by_family.csv")
cov_cc   = pd.read_csv(PB / "tables" / "coverage_by_compat.csv")
warmst   = pd.read_csv(PB / "tables" / "warmstart_synthesis.csv")
parked   = pd.read_csv(PB / "tables" / "deferred_parked.csv")
adv_idx  = json.load(open(ADV / "advisor_index_v1.json"))
adv_tips = json.load(open(ADV / "advisor_example_tips_v1.json"))
print("manifest rows        :", len(manifest))
print("coverage_by_family   :", len(cov_fam), "families")
print("coverage_by_compat   :", len(cov_cc), "compat classes")
print("warmstart_synthesis  :", len(warmst), "rows")
print("deferred_parked      :", len(parked), "hard cases")
print("advisor index mats   :", len(adv_idx["materials"]), "| example tips:", len(adv_tips["tips"]))''')

md("## 3. Manifest overview (counts + fields + duplicate-sha check)")
code('''# headline numbers straight from the summary artifact, cross-checked against the manifest
nodes  = summary["certified_donor_nodes"]
unique = summary["unique_sha_donors"]
fams   = len(summary["by_family"])
f2     = summary["f2_eligible_material_count"]
print(f"certified donor nodes : {nodes}")
print(f"unique-sha donors     : {unique}")
print(f"families              : {fams}")
print(f"F2-eligible materials : {f2}")
print(f"compat classes        : {manifest['compat_class'].nunique()}")

# verify the frozen headline (loaded, not blindly hardcoded)
assert unique == manifest["sha256"].nunique() == 237, "unique donor count mismatch"
assert nodes == 238 and fams == 8 and f2 == 33, "headline mismatch"
print("\\nHEADLINE VERIFIED from artifacts: 237 unique / 238 nodes / 8 families / 33 F2-eligible")''')

code('''# key fields (one row per certified donor)
print("columns:", list(manifest.columns))
manifest[["source_stage","family","material","sha256","z_sequence","natyp",
          "nspin","soc","lmax","compat_class","empty_sphere","f2_eligible"]].head(8)''')

md("""**Field meanings.** `sha256` = byte-exact potential fingerprint (dedup key); `z_sequence`/`natyp` = per-site
atomic numbers (empty spheres as Z=0) and site count; `nspin`/`soc`/`lmax` = spin/SOC/angular settings;
`empty_sphere` = whether explicit vacant spheres are used (Si/Ge only); `compat_class` = the settings class a
donor is reusable within; `source_stage` = which campaign stage certified it; `f2_eligible` = the material has
≥2 independent donors. (`seg_pk`/`wc_pk`/`uuid` in the CSV are the AiiDA provenance handles — the raw
potentials live in the AiiDA repository, not here.)""")

code('''# duplicate-sha check: 238 nodes vs 237 unique -> exactly one recorded historical byte-duplicate
print("duplicate_sha_excluded (summary):", summary["duplicate_sha_excluded"])
print("detail:", summary["duplicate_detail"])
dups = manifest["sha256"].value_counts()
print("\\nany duplicate sha WITHIN the deduped manifest?:", (dups > 1).any(), "(expected False — the historical dup was collapsed)")''')

md("## 4. Coverage by family and compatibility class")
code('''fam = cov_fam.sort_values("n_donors", ascending=False)
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.bar(fam["family"], fam["n_donors"], color="#3b6ea5")
ax.set_ylabel("certified donors"); ax.set_title("PotentialBank v1 — donors by family")
plt.xticks(rotation=30, ha="right"); plt.tight_layout(); plt.show()
fam[["family","n_donors","n_materials","n_f2_eligible","empty_sphere"]]''')

code('''fig, ax = plt.subplots(figsize=(8, 3.6))
x = range(len(fam))
ax.bar([i-0.2 for i in x], fam["n_materials"], 0.4, label="materials", color="#b0b0b0")
ax.bar([i+0.2 for i in x], fam["n_f2_eligible"], 0.4, label="F2-eligible", color="#c0562c")
ax.set_xticks(list(x)); ax.set_xticklabels(fam["family"], rotation=30, ha="right")
ax.set_ylabel("materials"); ax.set_title("Materials and F2-eligibility by family"); ax.legend()
plt.tight_layout(); plt.show()''')

code('''# coverage by compatibility class (top classes)
cov_cc.sort_values("n_donors", ascending=False).head(12)''')

md("""## 5. Certification rules (E1) — plain language

A potential is admitted as a donor only if **all** hold:
1. the **AiiDA-retrieved, staged, and manifest SHA-256 all agree** (3-way match);
2. the **parser succeeds** and the potential **byte-exactly round-trips**;
3. the per-type **Z-sequence matches the structure site order** and **NATYP == number of sites** (empty
   spheres encoded as Z=0);
4. the cell is **non-CPA and non-BdG**;
5. NSPIN / SOC / LMAX / mesh parse and there is **no guessed mapping** (unsafe → rejected).

CPA/disordered and BdG are excluded by construction. Below are real certified rows (we display manifest
metadata only — we do **not** open raw potential files).""")
code('''examples = ["MgO","NaCl","Si","Ge","TiSe2"]
ex = manifest[manifest["material"].isin(examples)].drop_duplicates(["material","sha256"])
ex[["family","material","z_sequence","natyp","nspin","soc","lmax","empty_sphere","compat_class",
    "cpa","bdg","f2_eligible","sha256"]].reset_index(drop=True)''')

md("""## 6. Warm-start benchmark

Injecting a certified donor as the start potential cuts iterations-to-converge (same-structure). Numbers are
read from `warmstart_synthesis.csv`. **Warm-start benchmark outputs are not themselves certified as donors.**""")
code('''warmst[["family","material","cold_iters","warm_iters","saved","pct_saved","direction_symmetry","contour_caveat"]]''')

code('''import re
def first_int(s):
    m = re.findall(r"[0-9]+", str(s).replace(",", "")); return int(m[0]) if m else None
w = warmst.copy()
w["cold1"] = w["cold_iters"].map(first_int); w["warm1"] = w["warm_iters"].map(first_int)
fig, ax = plt.subplots(figsize=(9, 3.8))
x = range(len(w))
ax.bar([i-0.2 for i in x], w["cold1"], 0.4, label="cold (Voronoi)", color="#8a8a8a")
ax.bar([i+0.2 for i in x], w["warm1"], 0.4, label="warm (donor start)", color="#2e8b57")
ax.set_yscale("log"); ax.set_xticks(list(x))
ax.set_xticklabels(w["material"], rotation=40, ha="right", fontsize=8)
ax.set_ylabel("iterations (log)"); ax.set_title("Warm vs cold iterations (per benchmark row)"); ax.legend()
plt.tight_layout(); plt.show()''')

code('''# percent saved
def first_pct(s):
    m = re.findall(r"[0-9]+", str(s)); return int(m[0]) if m else None
w["pct1"] = w["pct_saved"].map(first_pct)
fig, ax = plt.subplots(figsize=(7.5, 3.4))
ax.bar(w["material"], w["pct1"], color="#3b6ea5")
ax.set_ylabel("% iters saved (first listed)"); ax.set_title("Iteration savings by benchmark")
plt.xticks(rotation=40, ha="right", fontsize=8); plt.tight_layout(); plt.show()''')

md("""**Examples / caveats (read from the table above):**
- **MgO / NaCl** show the *mixing-path* effect: a Broyden target converges a warm start in a few iterations,
  while a pure-linear target still crawls (e.g. 500 vs 750) — hence the two numbers and the 33–99 % range.
- **Si / Ge** are covalent empty-sphere donors (~2–3 vs ~117–119 iters).
- **TiSe2** is coarse-converged only (its fine contour destabilizes the zero-gap semimetal) — a recorded
  contour caveat. Magnitude is mixing/contour-dependent, so we report per-family and never a single pooled
  headline.""")

md("## 7. Advisor index — optional, advisory-only tips")
code('''def advise(material):
    m = next((x for x in adv_idx["materials"] if x["material"] == material), None)
    if m is None:
        wobj = next((p for p in adv_idx["parked_warnings"] if p["material"] == material), None)
        return f"WARNING ({wobj['klass']}): {wobj['warning']}" if wobj else "no advice (not in bank)"
    if m.get("f2_eligible") and m.get("warmstart"):
        ws = m["warmstart"]
        return (f"donor_start (Level A): warm-start from a certified {material} donor; "
                f"measured {ws['warm']} vs {ws['cold']} iters ({ws['pct']}). caveat: {ws['contour_caveat']}")
    return f"{material}: {m['n_unique_donors']} certified donor(s); advisory only."

for mat in ["MgO", "NaCl", "Si", "Au", "WSe2", "MoS2"]:
    print(f"{mat:6s} -> {advise(mat)}\\n")''')
code('''# the shipped worked example tips (each carries evidence level + confidence + reason)
pd.DataFrame(adv_tips["tips"])[["tip_type","material","evidence_level","confidence","recommendation"]]''')
md("""Tips are **advisory only** — a stock run ignores them; an opt-in run *may* inject the suggested certified
donor. The advisor never suggests a guessed/uncertified/CPA/BdG donor, and emits **warnings** (never "safe"
tips) for parked hard cases.""")

md("## 8. Deferred / parked hard cases (documented boundaries)")
code('''parked[["material","klass","stage","reason"]]''')
md("""Failures are **useful**: each parked case is root-caused (NACLSD cluster overflow, SOC contour/EMIN
instability, tetragonal VERTEX3D shapefun degeneracy, hard-convergence, empty-sphere requirement), mapping out
where the method does and does not apply. None of these are certified donors.""")

md("## 9. Claim ladder (allowed / disallowed)")
code('''ladder = (PB / "PAPER_CLAIM_LADDER_AFTER_POTBANK_V1.md").read_text().splitlines()
def section(title):
    out, grab = [], False
    for ln in ladder:
        if ln.startswith("## "):
            grab = title.lower() in ln.lower()
            continue
        if grab and ln.strip().startswith(("-", "*")):
            out.append(ln.strip())
    return out
print("VALIDATED (excerpt):")
for ln in section("VALIDATED")[:3]: print("  ", ln)
print("\\nDISALLOWED:")
for ln in section("DISALLOWED")[:6]: print("  ", ln)''')
md("""**Explicit scope reminders:**
- `ml_assist` early-abort **mechanism was validated live**, but **broad ML transfer was not proven** (it does
  not beat a simple RMS@10 baseline out-of-sample and does not transfer across materials).
- **PotentialBank v1 supports certified same-structure reuse.**
- **No cross-material transfer.**
- **No guaranteed acceleration.**""")

md("## 10. Reproducibility (checksums + version)")
code('''import hashlib
man = PB / "MANIFEST.sha256"
ver = PB / "VERSION"
if ver.exists():
    print("VERSION:"); print(json.dumps(json.load(open(ver)), indent=2))
if man.exists():
    ok = bad = 0
    for line in man.read_text().splitlines():
        sha, rel = line.split(None, 1); rel = rel.strip()
        p = ROOT / rel
        if not p.exists(): bad += 1; continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        ok += (got == sha); bad += (got != sha)
    print(f"\\nMANIFEST.sha256 verify: {ok} OK, {bad} mismatched/missing (of {ok+bad})")
else:
    print("MANIFEST.sha256 not present (bundle metadata not built)")
print("\\nSummary: PotentialBank v1 =", summary["unique_sha_donors"], "unique certified donors across",
      len(summary["by_family"]), "families;", summary["f2_eligible_material_count"], "F2-eligible.",
      "Same-structure reuse only; no cross-material transfer; no guaranteed acceleration.")''')

nb["cells"] = C
nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                  "language_info": {"name": "python"}}
out = os.path.join(os.path.dirname(__file__), "potentialbank_v1_walkthrough.ipynb")
nbf.write(nb, out)
print("wrote", out, "with", len(C), "cells")
